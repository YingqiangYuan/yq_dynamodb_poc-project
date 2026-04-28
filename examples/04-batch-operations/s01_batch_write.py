# -*- coding: utf-8 -*-
"""
04-batch-operations / s01 — Model.batch_write() context manager.

``batch_write`` accepts arbitrarily many writes; pynamodb chunks them
into ``BatchWriteItem`` calls of <=25 items each and retries unprocessed
ones internally. Use it whenever many writes are ready at the same time.
"""

from datetime import datetime, timezone, timedelta

from pynamodb.models import Model
from pynamodb.attributes import (
    UnicodeAttribute,
    NumberAttribute,
    UTCDateTimeAttribute,
)
from pynamodb.constants import PAY_PER_REQUEST_BILLING_MODE

from pynamodb_session_manager.api import use_boto_session

from yq_dynamodb_poc.one.api import one

PREFIX = "yq_dynamodb_poc"


class Transaction(Model):
    class Meta:
        table_name = f"{PREFIX}_batch_transactions"
        region = "us-east-1"
        billing_mode = PAY_PER_REQUEST_BILLING_MODE

    card_id = UnicodeAttribute(hash_key=True)
    tx_ts = UTCDateTimeAttribute(range_key=True)
    amount = NumberAttribute()
    merchant = UnicodeAttribute()


bsm = one.bsm

with use_boto_session(Transaction, bsm):
    if not Transaction.exists():
        Transaction.create_table(wait=True)

    for t in Transaction.scan():
        t.delete()

    base_ts = datetime(2026, 4, 1, tzinfo=timezone.utc)

    # 60 items > the 25-per-batch limit. pynamodb chunks transparently.
    items = [
        Transaction(
            card_id=f"CD{i % 3:03d}",
            tx_ts=base_ts + timedelta(minutes=i),
            amount=10.0 + i,
            merchant=f"Merchant{i % 5}",
        )
        for i in range(60)
    ]

    with Transaction.batch_write() as batch:
        for tx in items:
            batch.save(tx)
    # Items are flushed when the ``with`` block exits.

    total = sum(1 for _ in Transaction.scan())
    print(f"wrote {total} items in batches of 25")

    # batch_write also handles deletes — same chunking rules.
    with Transaction.batch_write() as batch:
        for tx in Transaction.scan():
            batch.delete(tx)
    print(f"after batch delete: {sum(1 for _ in Transaction.scan())} items")

    # Transaction.delete_table()
