# -*- coding: utf-8 -*-
"""
07-transactions / s02 — money-transfer pattern.

Each item in a ``TransactWrite`` may carry its own condition. If **any**
condition fails, the entire transaction is rolled back — none of the
items are written.

Classic example: A transfers $X to B. The debit must be conditional on
A having at least $X; the credit on B's side has no precondition. If
A's balance is too low, neither row changes.
"""

from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, NumberAttribute
from pynamodb.constants import PAY_PER_REQUEST_BILLING_MODE
from pynamodb.connection import Connection
from pynamodb.transactions import TransactWrite
from pynamodb.exceptions import TransactWriteError

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


def transfer(conn: Connection, src: Account, dst: Account, amount: float) -> None:
    """Move ``amount`` from ``src`` to ``dst`` atomically."""

    with TransactWrite(connection=conn) as tx:
        tx.update(
            src,
            actions=[Account.balance.add(-amount)],
            condition=Account.balance >= amount,
        )
        tx.update(
            dst,
            actions=[Account.balance.add(amount)],
        )


bsm = one.bsm

with use_boto_session(Account, bsm):
    if not Account.exists():
        Account.create_table(wait=True)

    for a in Account.scan():
        a.delete()

    Account(customer_id="A001", name="Alice", balance=1000).save()
    Account(customer_id="A002", name="Bob", balance=500).save()

    conn = Connection(region=bsm.aws_region)

    alice = Account.get("A001")
    bob = Account.get("A002")

    # Happy path: Alice has plenty.
    transfer(conn, alice, bob, 100)
    print(f"after $100 transfer: A001={Account.get('A001').balance} A002={Account.get('A002').balance}")

    # Sad path: try to transfer more than Alice has. Both updates are
    # rolled back atomically.
    alice.refresh()
    bob.refresh()
    try:
        transfer(conn, alice, bob, 9999)
    except TransactWriteError as e:
        print(f"transfer rejected ({type(e).__name__}): insufficient balance, transaction rolled back")

    final_a = Account.get("A001")
    final_b = Account.get("A002")
    print(f"final balances: A001={final_a.balance} A002={final_b.balance}")
    # A001 unchanged at 900 (1000 - 100), A002 unchanged at 600 (500 + 100).

    # Account.delete_table()
