# -*- coding: utf-8 -*-
"""
05-query-and-scan / s03 — manual pagination via last_evaluated_key.

For most code, just iterating ``Model.query(...)`` is enough — pynamodb
fetches additional pages from DynamoDB transparently.

Manual pagination is needed when:

- You expose pagination to a caller (REST endpoint, UI "load more")
  and need a stable cursor to hand back.
- You want to bound memory usage by stopping after N pages.

The cursor is ``result.last_evaluated_key`` (a dict). Pass it as
``last_evaluated_key=`` on the next call to resume. When the underlying
query is exhausted, ``last_evaluated_key`` is ``None``.
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
        for i in range(23):
            batch.save(Transaction(
                card_id="CD001",
                tx_ts=base_ts + timedelta(hours=i),
                amount=10.0 + i,
                merchant=f"M{i}",
            ))

    page_size = 5
    page_num = 0
    last_key = None

    while True:
        page_num += 1
        page = Transaction.query(
            "CD001", limit=page_size, last_evaluated_key=last_key
        )
        rows = list(page)
        print(f"page {page_num}: {len(rows)} rows | last_key={page.last_evaluated_key}")
        for tx in rows:
            print(f"  {tx.tx_ts.isoformat()} amount={tx.amount}")
        last_key = page.last_evaluated_key
        if not last_key:
            break

    print(f"\ntotal pages: {page_num}")

    # Transaction.delete_table()
