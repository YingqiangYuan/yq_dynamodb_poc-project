# -*- coding: utf-8 -*-
"""
06-condition-expression / s02 — conditional update.

``instance.update(actions=[...], condition=...)`` only applies the
actions if the condition is true at write time. Useful for state-machine
fields: "only raise the credit limit if the card is ACTIVE", "only mark
SHIPPED if the order is currently PAID", etc.
"""

from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, NumberAttribute
from pynamodb.constants import PAY_PER_REQUEST_BILLING_MODE
from pynamodb.exceptions import UpdateError

from pynamodb_session_manager.api import use_boto_session

from yq_dynamodb_poc.one.api import one

PREFIX = "yq_dynamodb_poc"


class Card(Model):
    class Meta:
        table_name = f"{PREFIX}_cond_cards"
        region = "us-east-1"
        billing_mode = PAY_PER_REQUEST_BILLING_MODE

    card_id = UnicodeAttribute(hash_key=True)
    holder_name = UnicodeAttribute()
    status = UnicodeAttribute(default="ACTIVE")  # ACTIVE / FROZEN / CLOSED
    credit_limit = NumberAttribute()


bsm = one.bsm

with use_boto_session(Card, bsm):
    if not Card.exists():
        Card.create_table(wait=True)

    for c in Card.scan():
        c.delete()

    Card(card_id="CD001", holder_name="Alice", status="ACTIVE", credit_limit=10000).save()

    # Happy path: status is ACTIVE, condition holds.
    card = Card.get("CD001")
    card.update(
        actions=[Card.credit_limit.set(20000)],
        condition=Card.status == "ACTIVE",
    )
    print(f"after happy-path update: credit_limit={Card.get('CD001').credit_limit}")

    # Flip status to FROZEN.
    card.update(actions=[Card.status.set("FROZEN")])

    # Sad path: status is no longer ACTIVE, condition fails.
    try:
        card.update(
            actions=[Card.credit_limit.set(30000)],
            condition=Card.status == "ACTIVE",
        )
    except UpdateError as e:
        print(f"second update rejected ({type(e).__name__}): card no longer ACTIVE")

    # Verify: credit_limit is still 20000, not 30000.
    final = Card.get("CD001")
    print(f"final state: status={final.status} credit_limit={final.credit_limit}")

    # Card.delete_table()
