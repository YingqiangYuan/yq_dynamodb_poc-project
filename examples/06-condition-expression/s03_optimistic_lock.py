# -*- coding: utf-8 -*-
"""
06-condition-expression / s03 — manual optimistic locking.

Two clients read the same row, both want to update it, and we need
exactly one to win without using a database lock. The standard
optimistic-locking pattern:

1. Each row carries a ``version`` number.
2. On read, remember the version.
3. On write, condition on ``version == <remembered>`` and increment
   ``version`` in the same update.

The first writer wins (server's version was equal). The second writer's
condition fails because the server's version has been bumped — they
must refresh and retry.

(For a built-in alternative, use ``pynamodb.attributes.VersionAttribute``.
We do it by hand here so the mechanism is visible.)
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
    credit_limit = NumberAttribute()
    version = NumberAttribute(default=0)


bsm = one.bsm

with use_boto_session(Card, bsm):
    if not Card.exists():
        Card.create_table(wait=True)

    for c in Card.scan():
        c.delete()

    Card(card_id="CD001", holder_name="Alice", credit_limit=10000, version=0).save()

    # Two clients read the same row.
    writer_a = Card.get("CD001")
    writer_b = Card.get("CD001")
    print(f"both writers see version={writer_a.version}")

    # Writer A commits first.
    writer_a.update(
        actions=[
            Card.credit_limit.set(15000),
            Card.version.add(1),
        ],
        condition=Card.version == writer_a.version,
    )
    print(f"writer A committed; server version is now {Card.get('CD001').version}")

    # Writer B tries to commit with the stale version it read earlier.
    try:
        writer_b.update(
            actions=[
                Card.credit_limit.set(20000),
                Card.version.add(1),
            ],
            condition=Card.version == writer_b.version,
        )
    except UpdateError:
        print(f"writer B lost the race (stale version={writer_b.version}); refreshing")

    # Writer B refreshes and retries.
    writer_b.refresh()
    writer_b.update(
        actions=[
            Card.credit_limit.set(20000),
            Card.version.add(1),
        ],
        condition=Card.version == writer_b.version,
    )
    print(f"writer B retried with version={writer_b.version} and committed")

    final = Card.get("CD001")
    print(f"final state: credit_limit={final.credit_limit} version={final.version}")

    # Card.delete_table()
