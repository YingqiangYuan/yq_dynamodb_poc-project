# -*- coding: utf-8 -*-
"""
04-batch-operations / s02 — Model.batch_get(keys).

Reads many rows in a single call. ``keys`` is a list of ``(hash_key,
range_key)`` tuples (or just hash keys for single-key tables). pynamodb
chunks them at 100 per ``BatchGetItem`` request.

Items come back in arbitrary order; sort client-side if you need a
specific ordering. Missing keys are silently skipped — they do **not**
raise.
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

    seed = [
        Transaction(
            card_id="CD001",
            tx_ts=base_ts + timedelta(minutes=i),
            amount=10.0 + i,
            merchant=f"Merchant{i}",
        )
        for i in range(10)
    ]
    with Transaction.batch_write() as batch:
        for tx in seed:
            batch.save(tx)

    keys_to_get = [
        ("CD001", base_ts + timedelta(minutes=0)),
        ("CD001", base_ts + timedelta(minutes=2)),
        ("CD001", base_ts + timedelta(minutes=4)),
        ("CD001", base_ts + timedelta(minutes=6)),
        ("CD001", base_ts + timedelta(minutes=8)),
        ("CD999", base_ts),  # missing — silently skipped, NOT an error
    ]

    fetched = list(Transaction.batch_get(keys_to_get))
    print(
        f"requested {len(keys_to_get)} keys, fetched {len(fetched)} rows "
        "(missing keys are skipped)"
    )
    for tx in sorted(fetched, key=lambda t: t.tx_ts):
        print(f"  {tx.card_id} {tx.tx_ts.isoformat()} amount={tx.amount}")

    # Transaction.delete_table()
