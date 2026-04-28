# -*- coding: utf-8 -*-
"""
05-query-and-scan / s02 — sort order and limit.

- ``scan_index_forward=False`` reverses the sort-key order. Common
  pattern: "give me the 10 most recent transactions on this card".
- ``limit=N`` caps the result count. Combined with descending order,
  this is an efficient "top-N" query.
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
        table_name = f"{PREFIX}_query_transactions"
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

    with Transaction.batch_write() as batch:
        for i in range(20):
            batch.save(Transaction(
                card_id="CD001",
                tx_ts=base_ts + timedelta(hours=i),
                amount=10.0 + i,
                merchant=f"M{i}",
            ))

    # Most recent 5: descending sort + limit 5.
    rows = list(Transaction.query("CD001", scan_index_forward=False, limit=5))
    print("most recent 5 (descending):")
    for tx in rows:
        print(f"  {tx.tx_ts.isoformat()} amount={tx.amount}")

    # Oldest 3: default (ascending) + limit 3.
    rows = list(Transaction.query("CD001", limit=3))
    print("\noldest 3 (ascending):")
    for tx in rows:
        print(f"  {tx.tx_ts.isoformat()} amount={tx.amount}")

    # Transaction.delete_table()
