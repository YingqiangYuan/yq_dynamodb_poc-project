# -*- coding: utf-8 -*-
"""
03-crud-basic / s04 — instance.delete().

Removes one row. Idempotent: deleting a non-existent row succeeds
silently unless you attach a condition (see ``06-condition-expression/``).
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

    tx = Transaction.get("CD001", ts)
    tx.delete()
    print("row deleted")

    try:
        Transaction.get("CD001", ts)
    except Transaction.DoesNotExist:
        print("confirmed: row no longer exists")

    # Transaction.delete_table()
