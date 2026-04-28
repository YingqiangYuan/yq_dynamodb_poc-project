# -*- coding: utf-8 -*-
"""
03-crud-basic / s03 — instance.update(actions=[...]).

``update`` mutates specific attributes server-side. Compared to ``save``:

- Cheaper — only the changed attributes travel over the wire.
- Safer when multiple writers touch the same row — fields you do not
  list are left alone.

Three action verbs cover most cases:

- ``Attr.set(value)``           — set a scalar / list / map / set to ``value``
- ``Attr.add(<set or number>)`` — for sets: add elements; for numbers: increment
- ``Attr.remove()``             — drop the attribute entirely (different from ``set(None)``)
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

    Transaction(
        card_id="CD001",
        tx_ts=ts,
        amount=42.50,
        merchant="Starbucks",
        note="initial note",
        tags={"coffee"},
    ).save()

    tx = Transaction.get("CD001", ts)
    tx.update(actions=[
        Transaction.amount.set(99.99),       # overwrite scalar
        Transaction.tags.add({"flagged"}),   # set: add element
        Transaction.note.remove(),           # drop attribute
    ])

    after = Transaction.get("CD001", ts)
    print(f"amount = {after.amount}              (was 42.50)")
    print(f"tags   = {sorted(after.tags)}  (was ['coffee'])")
    print(f"note   = {after.note}             (attribute now absent)")

    # Transaction.delete_table()
