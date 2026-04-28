# -*- coding: utf-8 -*-
"""
07-transactions / s03 — TransactGet for atomic snapshot reads.

A ``TransactGet`` block reads up to 100 items in one call and guarantees
the result reflects a single point in time — no row in the result was
mutated by another transaction while the read was in flight.

Use it when you need a *consistent cross-item view*: e.g. computing a
customer's total balance across multiple accounts without risking
double-counting an in-flight transfer.

API note: ``tx.get(...)`` returns a ``_ModelFuture`` immediately. The
actual model is materialized when the ``with`` block exits and ``_commit``
runs. Call ``.get()`` on the future *after* the block to retrieve it.
"""

from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, NumberAttribute
from pynamodb.constants import PAY_PER_REQUEST_BILLING_MODE
from pynamodb.connection import Connection
from pynamodb.transactions import TransactGet

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
    Account(customer_id="A003", name="Carol", balance=750).save()

    conn = Connection(region=bsm.aws_region)

    with TransactGet(connection=conn) as tx:
        f_alice = tx.get(Account, "A001")
        f_bob = tx.get(Account, "A002")
        f_carol = tx.get(Account, "A003")
    # On __exit__, the API call is made and the futures are populated.

    alice = f_alice.get()
    bob = f_bob.get()
    carol = f_carol.get()

    total = alice.balance + bob.balance + carol.balance
    print(f"  Alice = {alice.balance}")
    print(f"  Bob   = {bob.balance}")
    print(f"  Carol = {carol.balance}")
    print(f"  total = {total}  (consistent point-in-time snapshot)")

    # Account.delete_table()
