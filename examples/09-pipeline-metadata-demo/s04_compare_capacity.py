# -*- coding: utf-8 -*-
"""
09-pipeline-metadata-demo / s04 — GSI vs scan, ConsumedReadCapacityUnits.

Same logical question — "find all FAILED pipeline runs" — answered
two ways. We use the boto3 low-level client because pynamodb's
high-level iterator does not expose ``ConsumedCapacity`` directly.

Expected outcome: scan reads ~30 rows worth of capacity, GSI query
reads only the FAILED rows. The bigger the table, the wider the gap.
"""

from pynamodb_session_manager.api import use_boto_session

from yq_dynamodb_poc.one.api import one

from models import PipelineRun

bsm = one.bsm

with use_boto_session(PipelineRun, bsm):
    table_name = PipelineRun.Meta.table_name
    client = bsm.dynamodb_client

    scan_resp = client.scan(
        TableName=table_name,
        FilterExpression="run_status = :s",
        ExpressionAttributeValues={":s": {"S": "FAILED"}},
        ReturnConsumedCapacity="TOTAL",
    )
    print(
        "[scan + filter]"
        f"  matched={len(scan_resp['Items'])}/scanned={scan_resp['ScannedCount']}"
        f"  ConsumedReadCapacityUnits={scan_resp['ConsumedCapacity']['CapacityUnits']}"
    )

    query_resp = client.query(
        TableName=table_name,
        IndexName="status-index",
        KeyConditionExpression="run_status = :s",
        ExpressionAttributeValues={":s": {"S": "FAILED"}},
        ReturnConsumedCapacity="TOTAL",
    )
    print(
        "[query GSI]   "
        f"  matched={len(query_resp['Items'])}/scanned={query_resp['ScannedCount']}"
        f"  ConsumedReadCapacityUnits={query_resp['ConsumedCapacity']['CapacityUnits']}"
    )
