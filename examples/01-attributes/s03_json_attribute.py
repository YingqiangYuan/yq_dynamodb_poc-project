# -*- coding: utf-8 -*-
"""
01-attributes / s03 — JSONAttribute for freeform payloads.

Reach for ``JSONAttribute`` when the field's shape varies per row, e.g.
the ``transaction_metadata`` blob attached to a credit-card transaction:
some rows include device fingerprints, others include 3-D Secure data,
others are empty.

Internally pynamodb serializes the payload to a JSON string and stores it
as a single ``S`` attribute. You lose server-side queryability into the
nested fields — that is the cost of schemaless storage.
"""

from datetime import datetime, timezone

from pynamodb.models import Model
from pynamodb.attributes import (
    UnicodeAttribute,
    NumberAttribute,
    UTCDateTimeAttribute,
    JSONAttribute,
)
from pynamodb.constants import PAY_PER_REQUEST_BILLING_MODE

from pynamodb_session_manager.api import use_boto_session

from yq_dynamodb_poc.one.api import one

PREFIX = "yq_dynamodb_poc"


class Transaction(Model):
    class Meta:
        table_name = f"{PREFIX}_attr_transactions"
        region = "us-east-1"
        billing_mode = PAY_PER_REQUEST_BILLING_MODE

    tx_id = UnicodeAttribute(hash_key=True)
    amount = NumberAttribute()
    tx_ts = UTCDateTimeAttribute(default=lambda: datetime.now(timezone.utc))
    # Anything JSON-serializable: dicts, lists, nested combinations, primitives.
    metadata = JSONAttribute(null=True)


bsm = one.bsm

with use_boto_session(Transaction, bsm):
    if not Transaction.exists():
        Transaction.create_table(wait=True)

    for t in Transaction.scan():
        t.delete()

    # Row 1: rich nested metadata.
    Transaction(
        tx_id="TX001",
        amount=129.99,
        metadata={
            "device": {"os": "iOS", "model": "iPhone 15", "ip": "203.0.113.7"},
            "three_ds": {"version": "2.2.0", "result": "AUTHENTICATED"},
            "risk_signals": ["new_device", "geo_match"],
        },
    ).save()

    # Row 2: minimal metadata.
    Transaction(
        tx_id="TX002",
        amount=4.50,
        metadata={"channel": "in_store"},
    ).save()

    # Row 3: no metadata at all.
    Transaction(tx_id="TX003", amount=42.00).save()

    for t in Transaction.scan():
        print(f"{t.tx_id} | amount={t.amount} | metadata={t.metadata}")

    # Transaction.delete_table()
