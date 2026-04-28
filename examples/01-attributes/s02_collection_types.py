# -*- coding: utf-8 -*-
"""
01-attributes / s02 — collection Attribute types.

- ``UnicodeSetAttribute`` — unordered set of strings (DynamoDB type ``SS``)
- ``NumberSetAttribute``  — unordered set of numbers (``NS``)
- ``ListAttribute``       — ordered list of values (``L``)
- ``MapAttribute``        — nested object with named fields (``M``)

Use ``MapAttribute`` when the nested shape is fixed and you want
pynamodb to validate it; use ``JSONAttribute`` (next script) when the
payload is freeform.
"""

from pynamodb.models import Model
from pynamodb.attributes import (
    UnicodeAttribute,
    UnicodeSetAttribute,
    NumberSetAttribute,
    ListAttribute,
    MapAttribute,
)
from pynamodb.constants import PAY_PER_REQUEST_BILLING_MODE

from pynamodb_session_manager.api import use_boto_session

from yq_dynamodb_poc.one.api import one

PREFIX = "yq_dynamodb_poc"


class Address(MapAttribute):
    """Nested object validated by pynamodb at save time."""

    line1 = UnicodeAttribute()
    city = UnicodeAttribute()
    zip_code = UnicodeAttribute()


class Card(Model):
    class Meta:
        table_name = f"{PREFIX}_attr_cards"
        region = "us-east-1"
        billing_mode = PAY_PER_REQUEST_BILLING_MODE

    card_id = UnicodeAttribute(hash_key=True)
    # Sets are unordered and de-duped. ``default=set`` is a callable, so
    # each new row gets its own empty set instead of sharing one.
    tags = UnicodeSetAttribute(default=set)
    reward_points_history = NumberSetAttribute(default=set)
    # Lists keep insertion order. ``of=`` could pin element type.
    recent_merchants = ListAttribute(default=list)
    billing_address = Address(null=True)


bsm = one.bsm

with use_boto_session(Card, bsm):
    if not Card.exists():
        Card.create_table(wait=True)

    for c in Card.scan():
        c.delete()

    Card(
        card_id="CD001",
        tags={"vip", "premium"},
        reward_points_history={100, 250, 500},
        recent_merchants=["Amazon", "Starbucks", "Uber"],
        billing_address=Address(line1="1 Market St", city="SF", zip_code="94105"),
    ).save()

    # Defaults: empty set, empty list, null nested map.
    Card(card_id="CD002").save()

    for c in Card.scan():
        addr = c.billing_address
        addr_str = f"{addr.line1}, {addr.city} {addr.zip_code}" if addr else None
        print(
            f"{c.card_id} | tags={sorted(c.tags) if c.tags else []} | "
            f"points={sorted(c.reward_points_history) if c.reward_points_history else []} | "
            f"merchants={c.recent_merchants} | address={addr_str}"
        )

    # Card.delete_table()
