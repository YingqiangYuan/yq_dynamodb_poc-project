# -*- coding: utf-8 -*-
"""
10-single-table-one-to-many / s01 — create the table and seed data.

Seeds two customers, four cards, and nine transactions:

- C001: Alice — cards CD001, CD002 — txns on both
- C002: Bob   — cards CD003, CD004 — txns on CD003
"""

from datetime import datetime, timezone, timedelta

from pynamodb_session_manager.api import use_boto_session

from yq_dynamodb_poc.one.api import one

from models import Entity


def tx_sk(card_id: str, ts: datetime) -> str:
    return f"TX#{card_id}#{ts.isoformat()}"


bsm = one.bsm

base_ts = datetime(2026, 4, 27, 9, 0, tzinfo=timezone.utc)

rows = [
    # Customer profiles
    Entity(pk="CUSTOMER#C001", sk="PROFILE", entity_type="CUSTOMER",
           name="Alice", email="alice@example.com"),
    Entity(pk="CUSTOMER#C002", sk="PROFILE", entity_type="CUSTOMER",
           name="Bob", email="bob@example.com"),

    # Cards
    Entity(pk="CUSTOMER#C001", sk="CARD#CD001", entity_type="CARD",
           holder_name="Alice", credit_limit=10_000),
    Entity(pk="CUSTOMER#C001", sk="CARD#CD002", entity_type="CARD",
           holder_name="Alice", credit_limit=5_000),
    Entity(pk="CUSTOMER#C002", sk="CARD#CD003", entity_type="CARD",
           holder_name="Bob", credit_limit=20_000),
    Entity(pk="CUSTOMER#C002", sk="CARD#CD004", entity_type="CARD",
           holder_name="Bob", credit_limit=8_000),

    # Transactions on CD001
    Entity(pk="CUSTOMER#C001", sk=tx_sk("CD001", base_ts + timedelta(hours=0)),
           entity_type="TRANSACTION", amount=42.50, merchant="Starbucks",
           tx_ts=base_ts + timedelta(hours=0)),
    Entity(pk="CUSTOMER#C001", sk=tx_sk("CD001", base_ts + timedelta(hours=2)),
           entity_type="TRANSACTION", amount=129.99, merchant="Amazon",
           tx_ts=base_ts + timedelta(hours=2)),
    Entity(pk="CUSTOMER#C001", sk=tx_sk("CD001", base_ts + timedelta(hours=5)),
           entity_type="TRANSACTION", amount=8.75, merchant="Uber",
           tx_ts=base_ts + timedelta(hours=5)),
    Entity(pk="CUSTOMER#C001", sk=tx_sk("CD001", base_ts + timedelta(hours=8)),
           entity_type="TRANSACTION", amount=55.00, merchant="Whole Foods",
           tx_ts=base_ts + timedelta(hours=8)),

    # Transactions on CD002
    Entity(pk="CUSTOMER#C001", sk=tx_sk("CD002", base_ts + timedelta(hours=1)),
           entity_type="TRANSACTION", amount=999.00, merchant="Apple",
           tx_ts=base_ts + timedelta(hours=1)),
    Entity(pk="CUSTOMER#C001", sk=tx_sk("CD002", base_ts + timedelta(hours=4)),
           entity_type="TRANSACTION", amount=12.40, merchant="Spotify",
           tx_ts=base_ts + timedelta(hours=4)),

    # Transactions on CD003
    Entity(pk="CUSTOMER#C002", sk=tx_sk("CD003", base_ts + timedelta(hours=0)),
           entity_type="TRANSACTION", amount=300.00, merchant="Delta Airlines",
           tx_ts=base_ts + timedelta(hours=0)),
    Entity(pk="CUSTOMER#C002", sk=tx_sk("CD003", base_ts + timedelta(hours=3)),
           entity_type="TRANSACTION", amount=45.00, merchant="Hilton",
           tx_ts=base_ts + timedelta(hours=3)),
    Entity(pk="CUSTOMER#C002", sk=tx_sk("CD003", base_ts + timedelta(hours=6)),
           entity_type="TRANSACTION", amount=22.50, merchant="Lyft",
           tx_ts=base_ts + timedelta(hours=6)),
]

with use_boto_session(Entity, bsm):
    if not Entity.exists():
        Entity.create_table(wait=True)

    for e in Entity.scan():
        e.delete()

    with Entity.batch_write() as batch:
        for row in rows:
            batch.save(row)

    counts: dict[str, int] = {}
    for r in rows:
        counts[r.entity_type] = counts.get(r.entity_type, 0) + 1
    print(f"seeded {len(rows)} rows: {counts}")
