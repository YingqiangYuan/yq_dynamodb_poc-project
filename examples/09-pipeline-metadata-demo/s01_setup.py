# -*- coding: utf-8 -*-
"""
09-pipeline-metadata-demo / s01 — create the table and GSI.

Idempotent: skips if the table already exists. Run this once before
``s02_seed_data.py``.
"""

from pynamodb_session_manager.api import use_boto_session

from yq_dynamodb_poc.one.api import one

from models import PipelineRun

bsm = one.bsm

with use_boto_session(PipelineRun, bsm):
    if PipelineRun.exists():
        print(f"table already exists: {PipelineRun.Meta.table_name}")
    else:
        PipelineRun.create_table(wait=True)
        print(f"created table + status-index GSI: {PipelineRun.Meta.table_name}")
