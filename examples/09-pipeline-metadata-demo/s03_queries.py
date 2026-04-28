# -*- coding: utf-8 -*-
"""
09-pipeline-metadata-demo / s03 — three roadmap query patterns.

1. Latest 10 runs of a given pipeline (main table, descending SK).
2. All FAILED runs across pipelines (``status-index`` GSI).
3. 7-day rolling quarantine_rate average for a pipeline (main table +
   client-side aggregation).
"""

from datetime import datetime, timezone, timedelta

from pynamodb_session_manager.api import use_boto_session

from yq_dynamodb_poc.one.api import one

from models import PipelineRun


def latest_runs(pipeline_name: str, n: int = 10) -> list[PipelineRun]:
    return list(PipelineRun.query(
        pipeline_name,
        scan_index_forward=False,
        limit=n,
    ))


def all_failed_runs() -> list[PipelineRun]:
    return list(PipelineRun.status_index.query("FAILED"))


def quarantine_rate_avg(pipeline_name: str, days: int = 7) -> tuple[float, int]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    rates: list[float] = []
    for r in PipelineRun.query(pipeline_name):
        if r.start_ts >= cutoff and r.records_processed > 0:
            rates.append(float(r.quarantine_count) / float(r.records_processed))
    avg = sum(rates) / len(rates) if rates else 0.0
    return avg, len(rates)


bsm = one.bsm

with use_boto_session(PipelineRun, bsm):
    print("=== Q1: latest 10 runs of txn-b2s (main table, SK desc) ===")
    for r in latest_runs("txn-b2s", n=10):
        print(
            f"  {r.start_ts.isoformat()} status={r.run_status:<7} "
            f"records={r.records_processed:>7} quarantine={r.quarantine_count}"
        )

    print("\n=== Q2: all FAILED runs across pipelines (status-index GSI) ===")
    for r in all_failed_runs():
        print(
            f"  {r.pipeline_name:<12} {r.start_ts.isoformat()} "
            f"records={r.records_processed} quarantine={r.quarantine_count}"
        )

    print("\n=== Q3: 7-day quarantine_rate average per pipeline ===")
    for p in ["txn-b2s", "credit-b2s", "billing-b2s"]:
        avg, n = quarantine_rate_avg(p, days=7)
        print(f"  {p:<12} avg_rate={avg:.4f}  (over {n} runs in window)")
