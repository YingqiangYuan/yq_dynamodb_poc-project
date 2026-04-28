# -*- coding: utf-8 -*-
"""
02-table-management / s01 — create / exists / delete.

The only script in the repo that really drops the table at the end.
Every other script wipes rows but keeps the table to avoid the
``create_table`` wait on every rerun.
"""

import time

from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute
from pynamodb.constants import PAY_PER_REQUEST_BILLING_MODE

from pynamodb_session_manager.api import use_boto_session

from yq_dynamodb_poc.one.api import one

PREFIX = "yq_dynamodb_poc"


class Card(Model):
    class Meta:
        table_name = f"{PREFIX}_lifecycle_cards"
        region = "us-east-1"
        billing_mode = PAY_PER_REQUEST_BILLING_MODE

    card_id = UnicodeAttribute(hash_key=True)


bsm = one.bsm

with use_boto_session(Card, bsm):
    print(f"exists before? {Card.exists()}")

    if not Card.exists():
        # ``wait=True`` blocks until DynamoDB reports ACTIVE — creation is
        # asynchronous server-side, typically 5-30 seconds.
        t0 = time.time()
        Card.create_table(wait=True)
        print(f"create_table took {time.time() - t0:.1f}s")

    print(f"exists after create? {Card.exists()}")

    # ``delete_table`` has no ``wait=True`` flag. The call returns
    # immediately and the table goes through DELETING for a few seconds
    # before disappearing — poll ``exists()`` if you need to wait.
    Card.delete_table()
    print("delete_table issued")

    for _ in range(30):
        if not Card.exists():
            break
        time.sleep(1)
    print(f"exists after delete? {Card.exists()}")
