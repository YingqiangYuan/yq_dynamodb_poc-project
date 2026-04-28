# -*- coding: utf-8 -*-
"""
06-condition-expression / s01 — save-if-not-exists.

By default ``instance.save()`` is an upsert: same key replaces. Attaching
``condition=Model.<hash_key>.does_not_exist()`` turns it into a strict
insert. On conflict pynamodb raises ``PutError``, which wraps DynamoDB's
``ConditionalCheckFailedException``.
"""

from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, NumberAttribute
from pynamodb.constants import PAY_PER_REQUEST_BILLING_MODE
from pynamodb.exceptions import PutError

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
    credit_limit = NumberAttribute()


bsm = one.bsm

with use_boto_session(Card, bsm):
    if not Card.exists():
        Card.create_table(wait=True)

    for c in Card.scan():
        c.delete()

    # First insert: condition holds, save succeeds.
    Card(card_id="CD001", holder_name="Alice", credit_limit=10000).save(
        condition=Card.card_id.does_not_exist()
    )
    print("first insert: ok")

    # Second insert with same key + same condition: rejected.
    try:
        Card(card_id="CD001", holder_name="Mallory", credit_limit=999_999).save(
            condition=Card.card_id.does_not_exist()
        )
    except PutError as e:
        print(f"second insert rejected ({type(e).__name__}): row was protected")

    # Verify: row still has Alice's data.
    after = Card.get("CD001")
    print(f"final state: holder_name={after.holder_name} credit_limit={after.credit_limit}")

    # Card.delete_table()
