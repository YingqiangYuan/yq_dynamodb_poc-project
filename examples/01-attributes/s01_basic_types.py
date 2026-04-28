# -*- coding: utf-8 -*-
"""
01-attributes / s01 — basic Attribute types.

Covers the four scalar types you will use most:

- ``UnicodeAttribute``     — strings
- ``NumberAttribute``      — int/float
- ``BooleanAttribute``     — true/false
- ``UTCDateTimeAttribute`` — UTC timestamps

And the two most important modifiers:

- ``default=<value-or-callable>`` — value used if the field is unset on a new instance
- ``null=True``                   — the field is allowed to be missing
"""

from datetime import datetime, timezone

from pynamodb.models import Model
from pynamodb.attributes import (
    UnicodeAttribute,
    NumberAttribute,
    BooleanAttribute,
    UTCDateTimeAttribute,
)
from pynamodb.constants import PAY_PER_REQUEST_BILLING_MODE

from pynamodb_session_manager.api import use_boto_session

from yq_dynamodb_poc.one.api import one

PREFIX = "yq_dynamodb_poc"


class Customer(Model):
    class Meta:
        table_name = f"{PREFIX}_attr_customers"
        region = "us-east-1"
        billing_mode = PAY_PER_REQUEST_BILLING_MODE

    customer_id = UnicodeAttribute(hash_key=True)
    name = UnicodeAttribute()
    # ``null=True`` — age may legitimately be missing (we don't always know it).
    age = NumberAttribute(null=True)
    # ``default=True`` — newly created customers default to active.
    is_active = BooleanAttribute(default=True)
    # ``default="STANDARD"`` — unset tier defaults to STANDARD.
    tier = UnicodeAttribute(default="STANDARD")
    # Pass a callable so each new row gets a fresh "now" instead of all
    # rows sharing one frozen timestamp captured at module load.
    signup_at = UTCDateTimeAttribute(default=lambda: datetime.now(timezone.utc))


bsm = one.bsm

with use_boto_session(Customer, bsm):
    if not Customer.exists():
        Customer.create_table(wait=True)

    for c in Customer.scan():
        c.delete()

    # Row 1: every field set explicitly.
    Customer(
        customer_id="C001",
        name="Alice",
        age=30,
        is_active=True,
        tier="GOLD",
        signup_at=datetime(2026, 1, 15, tzinfo=timezone.utc),
    ).save()

    # Row 2: only required fields. Defaults kick in.
    Customer(customer_id="C002", name="Bob").save()

    # Row 3: explicit None on the nullable field.
    Customer(customer_id="C003", name="Carol", age=None).save()

    for c in Customer.scan():
        print(
            f"{c.customer_id} | name={c.name} | age={c.age} | "
            f"is_active={c.is_active} | tier={c.tier} | signup_at={c.signup_at}"
        )

    # Customer.delete_table()
