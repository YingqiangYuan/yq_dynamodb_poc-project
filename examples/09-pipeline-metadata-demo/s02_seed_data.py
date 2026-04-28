# -*- coding: utf-8 -*-
"""
09-pipeline-metadata-demo / s02 — seed 30 mock runs.

Wipes the table first (idempotent reseed), then writes 30 simulated
pipeline runs:

- 3 pipelines: ``txn-b2s``, ``credit-b2s``, ``billing-b2s``
- 3 statuses: ``SUCCESS`` (most), ``FAILED`` (some), ``PARTIAL`` (some)
- spread evenly across the **last 7 days** so ``s03_queries.py``'s
  rolling-7-day filter has data to match.
"""

import random
import uuid
from datetime import datetime, timezone, timedelta

from pynamodb_session_manager.api import use_boto_session

from yq_dynamodb_poc.one.api import one

from models import PipelineRun

PIPELINES = ["txn-b2s", "credit-b2s", "billing-b2s"]
STATUSES = ["SUCCESS", "FAILED", "PARTIAL"]
STATUS_WEIGHTS = [0.7, 0.15, 0.15]

random.seed(42)

bsm = one.bsm

with use_boto_session(PipelineRun, bsm):
    if not PipelineRun.exists():
        raise SystemExit("run s01_setup.py first")

    for r in PipelineRun.scan():
        r.delete()

    end_window = datetime.now(timezone.utc)
    start_window = end_window - timedelta(days=7)
    span_seconds = (end_window - start_window).total_seconds()

    runs = []
    for i in range(30):
        pipeline = random.choice(PIPELINES)
        status = random.choices(STATUSES, weights=STATUS_WEIGHTS)[0]
        # Distribute starts evenly across the 7-day window.
        start = start_window + timedelta(seconds=span_seconds * (i / 29))
        end = start + timedelta(minutes=random.randint(5, 60))

        records = random.randint(50_000, 500_000)
        # FAILED runs have higher quarantine rates by design.
        rate = (
            random.uniform(0.05, 0.20)
            if status == "FAILED"
            else random.uniform(0.001, 0.05)
        )
        quarantine = int(records * rate)

        runs.append(PipelineRun(
            pipeline_name=pipeline,
            run_id=f"{start.strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}",
            run_status=status,
            start_ts=start,
            end_ts=end,
            records_processed=records,
            quarantine_count=quarantine,
            s3_path=f"s3://datalake/silver/{pipeline}/dt={start.strftime('%Y-%m-%d')}",
            delta_version=random.randint(100, 1000),
        ))

    with PipelineRun.batch_write() as batch:
        for r in runs:
            batch.save(r)

    by_pipeline = {p: 0 for p in PIPELINES}
    by_status = {s: 0 for s in STATUSES}
    for r in runs:
        by_pipeline[r.pipeline_name] += 1
        by_status[r.run_status] += 1

    print(f"seeded {len(runs)} runs")
    print(f"  by pipeline: {by_pipeline}")
    print(f"  by status:   {by_status}")
