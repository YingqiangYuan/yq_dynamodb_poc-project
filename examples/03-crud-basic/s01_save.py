# -*- coding: utf-8 -*-
"""
03-crud-basic / s01 — instance.save().

``save`` writes the whole item. If a row with the same composite key
already exists it is replaced silently (no error). To prevent that, use
a condition expression — see ``06-condition-expression/s01_save_if_not_exists.py``.
"""

from datetime import datetime, timezone

from pynamodb.models import Model
from pynamodb.attributes import (
    UnicodeAttribute,
    NumberAttribute,
    UTCDateTimeAttribute,
    UnicodeSetAttribute,
)
from pynamodb.constants import PAY_PER_REQUEST_BILLING_MODE

from pynamodb_session_manager.api import use_boto_session

from yq_dynamodb_poc.one.api import one

PREFIX = "yq_dynamodb_poc"


class Transaction(Model):
    class Meta:
        table_name = f"{PREFIX}_crud_transactions"
        region = "us-east-1"
        billing_mode = PAY_PER_REQUEST_BILLING_MODE

    card_id = UnicodeAttribute(hash_key=True)
    tx_ts = UTCDateTimeAttribute(range_key=True)
    amount = NumberAttribute()
    merchant = UnicodeAttribute()
    note = UnicodeAttribute(null=True)
    tags = UnicodeSetAttribute(default=set)


bsm = one.bsm

ts = datetime(2026, 4, 1, 12, 0, tzinfo=timezone.utc)

with use_boto_session(Transaction, bsm):
    if not Transaction.exists():
        Transaction.create_table(wait=True)

    for t in Transaction.scan():
        t.delete()

    # First save: a brand-new row.
    Transaction(
        card_id="CD001",
        tx_ts=ts,
        amount=42.50,
        merchant="Starbucks",
        tags={"coffee"},
    ).save()
    print("first save: row inserted")

    # Second save with the same composite key REPLACES the previous row.
    # ``note`` was unset before; now it has a value, ``tags`` has changed.
    Transaction(
        card_id="CD001",
        tx_ts=ts,
        amount=99.99,
        merchant="Starbucks",
        note="upsized order",
        tags={"coffee", "breakfast"},
    ).save()
    print("second save: row replaced")

    after = Transaction.get("CD001", ts)
    print(
        f"final state: amount={after.amount}, note={after.note}, "
        f"tags={sorted(after.tags)}"
    )

    # Transaction.delete_table()
