# -*- coding: utf-8 -*-
"""
Shared model definitions for the pipeline-metadata composite demo.

Imported by ``s01_setup.py``, ``s02_seed_data.py``, ``s03_queries.py``,
and ``s04_compare_capacity.py``.
"""

from pynamodb.models import Model
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection
from pynamodb.attributes import (
    UnicodeAttribute,
    NumberAttribute,
    UTCDateTimeAttribute,
)
from pynamodb.constants import PAY_PER_REQUEST_BILLING_MODE

PREFIX = "yq_dynamodb_poc"


class StatusIndex(GlobalSecondaryIndex):
    """
    GSI for "find all runs in status X" queries.

    PK = run_status, SK = start_ts (so results come out time-ordered
    within a status).
    """

    class Meta:
        index_name = "status-index"
        projection = AllProjection()

    run_status = UnicodeAttribute(hash_key=True)
    start_ts = UTCDateTimeAttribute(range_key=True)


class PipelineRun(Model):
    """
    One row per execution of a data pipeline.

    Primary access: ``query(pipeline_name)`` returns every run of one
    pipeline, ``run_id`` ascending. Combined with
    ``scan_index_forward=False`` and ``limit=N``, that gives the "latest
    N runs of pipeline X" pattern.
    """

    class Meta:
        table_name = f"{PREFIX}_pipeline_runs"
        region = "us-east-1"
        billing_mode = PAY_PER_REQUEST_BILLING_MODE

    pipeline_name = UnicodeAttribute(hash_key=True)
    run_id = UnicodeAttribute(range_key=True)
    run_status = UnicodeAttribute()  # SUCCESS / FAILED / PARTIAL
    start_ts = UTCDateTimeAttribute()
    end_ts = UTCDateTimeAttribute(null=True)
    records_processed = NumberAttribute(default=0)
    quarantine_count = NumberAttribute(default=0)
    s3_path = UnicodeAttribute(null=True)
    delta_version = NumberAttribute(null=True)

    status_index = StatusIndex()
