# -*- coding: utf-8 -*-
"""
07-transactions / s01 — TransactWrite basics.

A ``TransactWrite`` block bundles up to 100 writes (save / update /
delete / condition_check) and ships them as a single
``TransactWriteItems`` API call. DynamoDB applies all of them or none.

This script does two operations atomically:

- ``update`` an existing account's balance
- ``save`` a brand-new account row

Both succeed or both are rolled back.
"""

from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, NumberAttribute
from pynamodb.constants import PAY_PER_REQUEST_BILLING_MODE
from pynamodb.connection import Connection
from pynamodb.transactions import TransactWrite

from pynamodb_session_manager.api import use_boto_session

from yq_dynamodb_poc.one.api import one

PREFIX = "yq_dynamodb_poc"


class Account(Model):
    class Meta:
        table_name = f"{PREFIX}_tx_accounts"
        region = "us-east-1"
        billing_mode = PAY_PER_REQUEST_BILLING_MODE

    customer_id = UnicodeAttribute(hash_key=True)
    name = UnicodeAttribute()
    balance = NumberAttribute()


bsm = one.bsm

with use_boto_session(Account, bsm):
    if not Account.exists():
        Account.create_table(wait=True)

    for a in Account.scan():
        a.delete()

    Account(customer_id="A001", name="Alice", balance=1000).save()
    Account(customer_id="A002", name="Bob", balance=500).save()

    # Build a Connection inside the with-block so it inherits the
    # AWS credentials set by ``use_boto_session``.
    conn = Connection(region=bsm.aws_region)

    alice = Account.get("A001")

    with TransactWrite(connection=conn) as tx:
        tx.update(alice, actions=[Account.balance.set(1500)])
        tx.save(Account(customer_id="A003", name="Carol", balance=200))
    # Commit happens at __exit__. If anything raised inside the ``with``,
    # nothing is sent.

    for a in sorted(Account.scan(), key=lambda x: x.customer_id):
        print(f"  {a.customer_id} {a.name} balance={a.balance}")

    # Account.delete_table()
