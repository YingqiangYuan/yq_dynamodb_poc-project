# -*- coding: utf-8 -*-
"""
05-query-and-scan / s04 — Scan + filter, and why to avoid it in prod.

``Model.scan(<filter_condition>)`` reads every row in the table and
discards the ones that don't match the filter. Filtering happens
server-side, but **after** read units are charged — so cost scales with
the size of the table, not with the size of the result.

Two practical guidelines:

1. **Don't scan in production code paths.** Add a GSI on the field you
   are filtering by, then ``query`` that GSI instead.
2. **Scans for ops/admin/migrations are fine.** That is what they exist
   for.
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

    # Mixed amounts on two cards.
    with Transaction.batch_write() as batch:
        for i in range(10):
            batch.save(Transaction(
                card_id="CD001",
                tx_ts=base_ts + timedelta(hours=i),
                amount=50.0 + i * 30,  # 50, 80, 110, 140, ...
                merchant=f"M{i}",
            ))
        for i in range(10):
            batch.save(Transaction(
                card_id="CD002",
                tx_ts=base_ts + timedelta(hours=i),
                amount=10.0 + i * 25,
                merchant=f"X{i}",
            ))

    # Scan + filter: amount > 100 across the whole table.
    big_txns = list(Transaction.scan(Transaction.amount > 100))
    print(f"transactions with amount > 100: {len(big_txns)}")
    for tx in big_txns:
        print(f"  {tx.card_id} {tx.tx_ts.isoformat()} amount={tx.amount}")

    # Multiple filters with & / |.
    big_on_cd001 = list(Transaction.scan(
        (Transaction.amount > 100) & (Transaction.card_id == "CD001")
    ))
    print(f"\namount > 100 AND card_id == CD001: {len(big_on_cd001)} rows")

    # Transaction.delete_table()
