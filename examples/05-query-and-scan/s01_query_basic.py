# -*- coding: utf-8 -*-
"""
05-query-and-scan / s01 — basic query patterns.

- ``Model.query(hash_key)`` returns every row under that partition key,
  sorted by sort key ascending.
- ``Model.query(hash_key, Model.sort_key.<op>(...))`` adds a sort-key
  condition (`==`, `<`, `<=`, `>`, `>=`, `between`, `begins_with`).
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

    # 10 transactions on CD001, 5 on CD002.
    with Transaction.batch_write() as batch:
        for i in range(10):
            batch.save(Transaction(
                card_id="CD001",
                tx_ts=base_ts + timedelta(hours=i),
                amount=10.0 * (i + 1),
                merchant=f"M{i}",
            ))
        for i in range(5):
            batch.save(Transaction(
                card_id="CD002",
                tx_ts=base_ts + timedelta(hours=i),
                amount=20.0 * (i + 1),
                merchant=f"X{i}",
            ))

    # Query 1: all rows for CD001.
    rows = list(Transaction.query("CD001"))
    print(f"all rows for CD001: {len(rows)}")

    # Query 2: rows for CD001 within a 4-hour window.
    start = base_ts + timedelta(hours=2)
    end = base_ts + timedelta(hours=5)
    rows = list(Transaction.query("CD001", Transaction.tx_ts.between(start, end)))
    print(f"CD001 between {start.isoformat()} and {end.isoformat()}: {len(rows)} rows")
    for tx in rows:
        print(f"  {tx.tx_ts.isoformat()} amount={tx.amount}")

    # Transaction.delete_table()
