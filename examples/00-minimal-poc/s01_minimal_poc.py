# -*- coding: utf-8 -*-
"""
00-minimal-poc — minimal end-to-end POC.

The "Golden Reference" for the whole ``examples/`` series. Walks through the
full pynamodb lifecycle with the fewest lines possible:

1. Define a pynamodb ``Model`` (``Card``) — one Python class == one table.
2. Create the table on the AWS account behind ``bsm`` (skip if it exists).
3. Wipe existing rows so the script is idempotent — keep the table itself
   to avoid the ``create_table`` wait on every run.
4. ``save`` one row.
5. ``get`` it back and print.
6. A commented-out ``Card.delete_table()`` is left at the end; uncomment it
   when you want to drop the table entirely.

Run::

    python examples/00-minimal-poc/s01_minimal_poc.py
"""

from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, NumberAttribute
from pynamodb.constants import PAY_PER_REQUEST_BILLING_MODE

from pynamodb_session_manager.api import use_boto_session

from yq_dynamodb_poc.one.api import one

# Every table name starts with "yq_dynamodb_poc_" so this project never
# collides with other tables in the same AWS account, and a single prefix
# scan is enough to clean everything up.
PREFIX = "yq_dynamodb_poc"


class Card(Model):
    """
    Minimal Card model: a single hash_key plus two scalar attributes.

    - ``Meta``      describes the table itself (name / region / billing mode).
    - ``Attribute`` instances describe columns (type / hash_key / range_key).
    """

    class Meta:
        table_name = f"{PREFIX}_cards"
        region = "us-east-1"
        billing_mode = PAY_PER_REQUEST_BILLING_MODE

    card_id = UnicodeAttribute(hash_key=True)
    holder_name = UnicodeAttribute()
    credit_limit = NumberAttribute()


# boto_session_manager pointing at this project's AWS account.
bsm = one.bsm

# ``use_boto_session`` is a context manager from pynamodb_session_manager:
# inside the ``with`` block, every DynamoDB call made through ``Card`` is
# routed through ``bsm`` (its profile / region / credentials). On exit the
# original connection settings are restored, so the same Python process can
# talk to multiple AWS accounts within one run.
with use_boto_session(Card, bsm):
    # 1. Create the table once; subsequent runs skip this branch.
    if not Card.exists():
        Card.create_table(wait=True)

    # 2. Wipe all rows so the script is idempotent across reruns.
    for card in Card.scan():
        card.delete()

    # 3. Write one row.
    card = Card(card_id="CD001", holder_name="Alice", credit_limit=10000)
    card.save()

    # 4. Read it back and print.
    card_back = Card.get("CD001")
    print(card_back)
    print(f"holder_name  = {card_back.holder_name}")
    print(f"credit_limit = {card_back.credit_limit}")

    # 5. Uncomment to drop the table entirely.
    # Card.delete_table()
