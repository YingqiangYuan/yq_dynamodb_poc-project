# -*- coding: utf-8 -*-
"""
08-gsi-and-lsi / s02 — KEYS_ONLY vs INCLUDE vs ALL projections.

Three GSIs on the same table, all keyed by ``(status, tx_ts)`` but with
different projections. Querying each shows what attributes come back:

- ``KeysOnlyProjection()``    — only the GSI keys + main table keys
- ``IncludeProjection([...])`` — keys + the listed extra attributes
- ``AllProjection()``          — every attribute on the row

The fewer attributes you project, the cheaper the GSI is to maintain
(less write amplification) and the smaller it is to store. The cost
shows up at read time: if the projected fields are insufficient you
need a follow-up ``Model.get()``, doubling the read.
"""

from datetime import datetime, timezone, timedelta

from pynamodb.models import Model
from pynamodb.indexes import (
    GlobalSecondaryIndex,
    KeysOnlyProjection,
    IncludeProjection,
    AllProjection,
)
from pynamodb.attributes import (
    UnicodeAttribute,
    NumberAttribute,
    UTCDateTimeAttribute,
)
from pynamodb.constants import PAY_PER_REQUEST_BILLING_MODE

from pynamodb_session_manager.api import use_boto_session

from yq_dynamodb_poc.one.api import one

PREFIX = "yq_dynamodb_poc"


class StatusKeysOnlyIndex(GlobalSecondaryIndex):
    class Meta:
        index_name = "status-keys-only"
        projection = KeysOnlyProjection()
    status = UnicodeAttribute(hash_key=True)
    tx_ts = UTCDateTimeAttribute(range_key=True)


class StatusIncludeIndex(GlobalSecondaryIndex):
    class Meta:
        index_name = "status-include"
        # Keys + ``amount`` only. ``merchant`` is NOT projected.
        projection = IncludeProjection(["amount"])
    status = UnicodeAttribute(hash_key=True)
    tx_ts = UTCDateTimeAttribute(range_key=True)


class StatusAllIndex(GlobalSecondaryIndex):
    class Meta:
        index_name = "status-all"
        projection = AllProjection()
    status = UnicodeAttribute(hash_key=True)
    tx_ts = UTCDateTimeAttribute(range_key=True)


class Transaction(Model):
    class Meta:
        table_name = f"{PREFIX}_idx_proj_transactions"
        region = "us-east-1"
        billing_mode = PAY_PER_REQUEST_BILLING_MODE

    card_id = UnicodeAttribute(hash_key=True)
    tx_ts = UTCDateTimeAttribute(range_key=True)
    status = UnicodeAttribute()
    amount = NumberAttribute()
    merchant = UnicodeAttribute()

    status_keys_only = StatusKeysOnlyIndex()
    status_include = StatusIncludeIndex()
    status_all = StatusAllIndex()


bsm = one.bsm

with use_boto_session(Transaction, bsm):
    if not Transaction.exists():
        Transaction.create_table(wait=True)

    for t in Transaction.scan():
        t.delete()

    base_ts = datetime(2026, 4, 1, tzinfo=timezone.utc)
    with Transaction.batch_write() as batch:
        for i in range(6):
            batch.save(Transaction(
                card_id=f"CD{i % 2:03d}",
                tx_ts=base_ts + timedelta(hours=i),
                status="FAILED" if i % 2 == 0 else "SUCCESS",
                amount=10.0 + i,
                merchant=f"M{i}",
            ))

    def show(label, rows):
        print(f"\n[{label}]")
        for tx in rows:
            # Attributes not projected come back as None on the model.
            print(
                f"  card_id={tx.card_id} tx_ts={tx.tx_ts.isoformat()} "
                f"status={tx.status} amount={tx.amount} merchant={tx.merchant}"
            )

    show("KEYS_ONLY", Transaction.status_keys_only.query("FAILED"))
    show("INCLUDE [amount]", Transaction.status_include.query("FAILED"))
    show("ALL", Transaction.status_all.query("FAILED"))

    # Transaction.delete_table()
