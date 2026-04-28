# -*- coding: utf-8 -*-
"""
08-gsi-and-lsi / s04 — GSI vs scan + filter, by ConsumedCapacity.

Same question — "how many FAILED transactions are there?" — answered
two ways:

1. ``scan`` + filter on ``status``. DynamoDB reads every row, then
   discards non-matching ones server-side.
2. ``query`` against the ``status-index`` GSI. DynamoDB jumps directly
   to the FAILED partition.

We use the boto3 low-level client here to read ``ConsumedCapacity`` off
the response — pynamodb's high-level iterator does not expose it
directly. The two numbers tell the cost story clearly.

Run this after seeding the same table from ``s01_gsi_basic.py`` (or run
this script directly — it seeds its own data first).
"""

from datetime import datetime, timezone, timedelta

from pynamodb.models import Model
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection
from pynamodb.attributes import (
    UnicodeAttribute,
    NumberAttribute,
    UTCDateTimeAttribute,
)
from pynamodb.constants import PAY_PER_REQUEST_BILLING_MODE

from pynamodb_session_manager.api import use_boto_session

from yq_dynamodb_poc.one.api import one

PREFIX = "yq_dynamodb_poc"


class StatusIndex(GlobalSecondaryIndex):
    class Meta:
        index_name = "status-index"
        projection = AllProjection()

    status = UnicodeAttribute(hash_key=True)
    tx_ts = UTCDateTimeAttribute(range_key=True)


class Transaction(Model):
    class Meta:
        table_name = f"{PREFIX}_idx_transactions"
        region = "us-east-1"
        billing_mode = PAY_PER_REQUEST_BILLING_MODE

    card_id = UnicodeAttribute(hash_key=True)
    tx_ts = UTCDateTimeAttribute(range_key=True)
    status = UnicodeAttribute()
    amount = NumberAttribute()
    merchant = UnicodeAttribute()

    status_index = StatusIndex()


bsm = one.bsm

with use_boto_session(Transaction, bsm):
    if not Transaction.exists():
        Transaction.create_table(wait=True)

    for t in Transaction.scan():
        t.delete()

    # Seed enough rows that the difference is observable. Most rows are
    # SUCCESS so the FAILED partition is a small slice of the table.
    base_ts = datetime(2026, 4, 1, tzinfo=timezone.utc)
    with Transaction.batch_write() as batch:
        for i in range(60):
            batch.save(Transaction(
                card_id=f"CD{i % 5:03d}",
                tx_ts=base_ts + timedelta(minutes=i),
                status="FAILED" if i % 10 == 0 else "SUCCESS",
                amount=10.0 + i,
                merchant=f"M{i}",
            ))

    table_name = Transaction.Meta.table_name
    client = bsm.dynamodb_client

    # ---- Option 1: scan + filter ----
    scan_resp = client.scan(
        TableName=table_name,
        FilterExpression="#s = :status",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":status": {"S": "FAILED"}},
        ReturnConsumedCapacity="TOTAL",
    )
    print(
        "[scan + filter]"
        f"  matched={len(scan_resp['Items'])}/"
        f"scanned={scan_resp['ScannedCount']}"
        f"  ConsumedCapacity={scan_resp['ConsumedCapacity']['CapacityUnits']}"
    )

    # ---- Option 2: query the GSI ----
    query_resp = client.query(
        TableName=table_name,
        IndexName="status-index",
        KeyConditionExpression="#s = :status",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":status": {"S": "FAILED"}},
        ReturnConsumedCapacity="TOTAL",
    )
    print(
        "[query GSI]   "
        f"  matched={len(query_resp['Items'])}/"
        f"scanned={query_resp['ScannedCount']}"
        f"  ConsumedCapacity={query_resp['ConsumedCapacity']['CapacityUnits']}"
    )

    # The scan reads ~60 rows worth of capacity; the GSI query reads
    # only the matching rows. The bigger the table, the bigger the gap.

    # Transaction.delete_table()
