# -*- coding: utf-8 -*-
"""
03-crud-basic / s05 — instance.refresh().

``refresh`` re-fetches the row from DynamoDB into the same Python object.
Useful after an update, or when you suspect another writer has changed
the row out from under you.
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
    ).save()

    # Two handles on the same row.
    handle_a = Transaction.get("CD001", ts)
    handle_b = Transaction.get("CD001", ts)

    # Writer B mutates server state.
    handle_b.update(actions=[Transaction.amount.set(99.99)])

    # Writer A's local view is now stale.
    print(f"handle_a.amount before refresh = {handle_a.amount}")  # still 42.50

    handle_a.refresh()
    print(f"handle_a.amount after refresh  = {handle_a.amount}")  # now 99.99

    # Transaction.delete_table()
