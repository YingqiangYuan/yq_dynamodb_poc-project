# -*- coding: utf-8 -*-
"""
11-single-table-many-to-many / s03 — Composite GSI / materialized graph.

The previous approach (``s02``) inverts a single relationship using a
GSI keyed on the main table's own ``sk`` / ``pk``. That works for one
relationship type, but if you have several (Customer-Merchant,
Customer-Card, Merchant-Card, …) you'd need one GSI per relationship.

The composite-GSI pattern adds dedicated ``gsi_pk`` / ``gsi_sk`` fields
to every row and populates them deliberately. A *single* GSI keyed on
those fields then serves the reverse direction of **all** relationship
types at once.

Schema:

    PK     = <type>#<id>     # source side
    SK     = <type>#<id>     # target side
    gsi_pk = <type>#<id>     # = SK (the target — what we want to look up by)
    gsi_sk = <type>#<id>     # = PK (the source — gives us back the source list)

Two relationship types share the same table and the same GSI:

    Customer-Merchant: PK=CUSTOMER#..., SK=MERCHANT#..., gsi_pk=MERCHANT#..., gsi_sk=CUSTOMER#...
    Customer-Card    : PK=CUSTOMER#..., SK=CARD#...,     gsi_pk=CARD#...,     gsi_sk=CUSTOMER#...

Reverse queries from the same GSI:

    "Who shops at M001?"     → gsi_pk = MERCHANT#M001
    "Who owns card CD007?"   → gsi_pk = CARD#CD007

Cost summary:

- Write : 1 item per edge + GSI propagation
- Read  : main-table query forward; one GSI for ALL reverse queries
- Consistency: strong forward, eventual reverse
"""

from datetime import datetime, timezone

from pynamodb.models import Model
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection
from pynamodb.attributes import UnicodeAttribute, NumberAttribute, UTCDateTimeAttribute
from pynamodb.constants import PAY_PER_REQUEST_BILLING_MODE

from pynamodb_session_manager.api import use_boto_session

from yq_dynamodb_poc.one.api import one

PREFIX = "yq_dynamodb_poc"


class InverseIndex(GlobalSecondaryIndex):
    class Meta:
        index_name = "inverse-index"
        projection = AllProjection()

    gsi_pk = UnicodeAttribute(hash_key=True)
    gsi_sk = UnicodeAttribute(range_key=True)


class Edge(Model):
    class Meta:
        table_name = f"{PREFIX}_st_mtm_composite"
        region = "us-east-1"
        billing_mode = PAY_PER_REQUEST_BILLING_MODE

    pk = UnicodeAttribute(hash_key=True)
    sk = UnicodeAttribute(range_key=True)
    gsi_pk = UnicodeAttribute()
    gsi_sk = UnicodeAttribute()
    relationship_type = UnicodeAttribute()  # CUST_MERCHANT / CUST_CARD / ...
    first_seen = UTCDateTimeAttribute(default=lambda: datetime.now(timezone.utc))
    tx_count = NumberAttribute(default=0)

    inverse_index = InverseIndex()


# Customer ↔ Merchant
CM_EDGES = [
    ("C001", "M001", 12),
    ("C001", "M002", 4),
    ("C001", "M003", 9),
    ("C002", "M001", 7),
    ("C002", "M003", 3),
]

# Customer ↔ Card (1:N modeled the same way to prove the GSI is reusable)
CC_EDGES = [
    ("C001", "CD001"),
    ("C001", "CD002"),
    ("C002", "CD003"),
    ("C002", "CD004"),
]


bsm = one.bsm

with use_boto_session(Edge, bsm):
    if not Edge.exists():
        Edge.create_table(wait=True)

    for e in Edge.scan():
        e.delete()

    with Edge.batch_write() as batch:
        for cust, merch, count in CM_EDGES:
            batch.save(Edge(
                pk=f"CUSTOMER#{cust}",
                sk=f"MERCHANT#{merch}",
                gsi_pk=f"MERCHANT#{merch}",
                gsi_sk=f"CUSTOMER#{cust}",
                relationship_type="CUST_MERCHANT",
                tx_count=count,
            ))
        for cust, card in CC_EDGES:
            batch.save(Edge(
                pk=f"CUSTOMER#{cust}",
                sk=f"CARD#{card}",
                gsi_pk=f"CARD#{card}",
                gsi_sk=f"CUSTOMER#{cust}",
                relationship_type="CUST_CARD",
            ))
    print(f"inserted {len(CM_EDGES)} customer-merchant + {len(CC_EDGES)} customer-card edges")

    print("\n=== Forward (main table): everything related to CUSTOMER#C001 ===")
    for e in Edge.query("CUSTOMER#C001"):
        print(f"  {e.sk:<18} type={e.relationship_type}")

    print("\n=== Reverse (one GSI, two relationship types) ===")

    print("  who shops at MERCHANT#M001?")
    for e in Edge.inverse_index.query("MERCHANT#M001"):
        print(f"    {e.gsi_sk}  tx_count={e.tx_count}")

    print("  who owns CARD#CD001?")
    for e in Edge.inverse_index.query("CARD#CD001"):
        print(f"    {e.gsi_sk}")

    # Edge.delete_table()
