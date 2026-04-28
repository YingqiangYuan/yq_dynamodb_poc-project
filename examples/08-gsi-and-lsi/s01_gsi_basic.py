# -*- coding: utf-8 -*-
"""
08-gsi-and-lsi / s01 — basic GSI.

Main table: ``Transaction`` keyed by (card_id, tx_ts).
GSI ``status_index``: keyed by (status, tx_ts).

Use case: "find all FAILED transactions across the whole table, sorted
by time". Without the GSI we would have to ``scan`` the entire table.

A GSI is a separate physical structure DynamoDB maintains as you write
to the main table. Writes to the main table propagate to the GSI
asynchronously, so GSI reads are **eventually** consistent — you cannot
ask for strongly consistent reads on a GSI.
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
        # AllProjection means the GSI carries every attribute — reads
        # return complete rows, no follow-up Model.get() needed.
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
    status = UnicodeAttribute()  # SUCCESS / FAILED / PENDING
    amount = NumberAttribute()
    merchant = UnicodeAttribute()

    status_index = StatusIndex()


bsm = one.bsm

with use_boto_session(Transaction, bsm):
    if not Transaction.exists():
        Transaction.create_table(wait=True)

    for t in Transaction.scan():
        t.delete()

    base_ts = datetime(2026, 4, 1, tzinfo=timezone.utc)
    statuses = ["SUCCESS", "FAILED", "PENDING"]

    with Transaction.batch_write() as batch:
        for i in range(15):
            batch.save(Transaction(
                card_id=f"CD{i % 3:03d}",
                tx_ts=base_ts + timedelta(hours=i),
                status=statuses[i % 3],
                amount=10.0 + i,
                merchant=f"M{i}",
            ))

    # Query the GSI: every FAILED transaction across the whole table.
    failed = list(Transaction.status_index.query("FAILED"))
    print(f"FAILED transactions: {len(failed)}")
    for tx in failed:
        print(f"  {tx.card_id} {tx.tx_ts.isoformat()} amount={tx.amount} merchant={tx.merchant}")

    # GSI also supports sort-key conditions and limit.
    recent_pending = list(
        Transaction.status_index.query(
            "PENDING",
            Transaction.tx_ts >= base_ts + timedelta(hours=10),
            scan_index_forward=False,
            limit=3,
        )
    )
    print(f"\nmost recent 3 PENDING (since hour 10): {len(recent_pending)} rows")
    for tx in recent_pending:
        print(f"  {tx.card_id} {tx.tx_ts.isoformat()}")

    # Transaction.delete_table()
