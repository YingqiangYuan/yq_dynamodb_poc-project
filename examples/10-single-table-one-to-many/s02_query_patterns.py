# -*- coding: utf-8 -*-
"""
10-single-table-one-to-many / s02 — three classic single-table queries.

All three patterns are a single ``query`` against the main table — no
joins, no scans, no follow-up calls. That is the entire point of
single-table design.

1. Full hierarchy for a customer (profile + every card + every transaction)
   ``query(PK = CUSTOMER#C001)``
2. Just the cards under a customer
   ``query(PK = CUSTOMER#C001, SK begins_with "CARD#")``
3. Just the transactions on one specific card
   ``query(PK = CUSTOMER#C001, SK begins_with "TX#CD001#")``
"""

from pynamodb_session_manager.api import use_boto_session

from yq_dynamodb_poc.one.api import one

from models import Entity


def fmt(e: Entity) -> str:
    if e.entity_type == "CUSTOMER":
        return f"  [CUSTOMER]    {e.pk}  name={e.name} email={e.email}"
    if e.entity_type == "CARD":
        return (f"  [CARD]        {e.pk} / {e.sk}  "
                f"holder={e.holder_name} limit={e.credit_limit}")
    return (f"  [TRANSACTION] {e.pk} / {e.sk}  "
            f"amount={e.amount} merchant={e.merchant}")


bsm = one.bsm

with use_boto_session(Entity, bsm):
    print("=== Q1: full hierarchy for CUSTOMER#C001 ===")
    for e in Entity.query("CUSTOMER#C001"):
        print(fmt(e))

    print("\n=== Q2: cards under CUSTOMER#C001 ===")
    for e in Entity.query("CUSTOMER#C001", Entity.sk.startswith("CARD#")):
        print(fmt(e))

    print("\n=== Q3: transactions on CD001 (under CUSTOMER#C001) ===")
    for e in Entity.query("CUSTOMER#C001", Entity.sk.startswith("TX#CD001#")):
        print(fmt(e))
