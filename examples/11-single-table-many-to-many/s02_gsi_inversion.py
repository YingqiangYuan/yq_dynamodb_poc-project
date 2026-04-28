# -*- coding: utf-8 -*-
"""
11-single-table-many-to-many / s02 — Inverted GSI.

Each Customer↔Merchant relationship is stored as **one** row:

    PK=CUSTOMER#C001  SK=MERCHANT#M001

A GSI ``inversion-index`` swaps the keys: its hash key is the main
table's ``sk`` and its range key is the main table's ``pk``. With the
inverted index in place:

- "merchants for customer C001" → main-table query
  ``query("CUSTOMER#C001", SK begins_with "MERCHANT#")``
- "customers for merchant M001" → GSI query
  ``inversion_index.query("MERCHANT#M001", pk begins_with "CUSTOMER#")``

Trade-offs:

- One write per relationship — half the write cost of the adjacency
  approach.
- Reverse direction goes through a GSI, which is eventually consistent
  (the row appears in the GSI shortly after the main-table write
  commits — usually milliseconds).

Cost summary:

- Write : 1 item per edge + GSI propagation
- Read  : main-table query forward; GSI query reverse
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


class InversionIndex(GlobalSecondaryIndex):
    class Meta:
        index_name = "inversion-index"
        projection = AllProjection()

    # Hash key on the GSI = sort key on the main table; vice versa.
    sk = UnicodeAttribute(hash_key=True)
    pk = UnicodeAttribute(range_key=True)


class Edge(Model):
    class Meta:
        table_name = f"{PREFIX}_st_mtm_inversion"
        region = "us-east-1"
        billing_mode = PAY_PER_REQUEST_BILLING_MODE

    pk = UnicodeAttribute(hash_key=True)
    sk = UnicodeAttribute(range_key=True)
    first_seen = UTCDateTimeAttribute(default=lambda: datetime.now(timezone.utc))
    tx_count = NumberAttribute(default=0)

    inversion_index = InversionIndex()


RELATIONSHIPS = [
    ("C001", "M001", 12),
    ("C001", "M002", 4),
    ("C001", "M003", 9),
    ("C002", "M001", 7),
    ("C002", "M003", 3),
]


bsm = one.bsm

with use_boto_session(Edge, bsm):
    if not Edge.exists():
        Edge.create_table(wait=True)

    for e in Edge.scan():
        e.delete()

    with Edge.batch_write() as batch:
        for cust, merch, count in RELATIONSHIPS:
            batch.save(Edge(
                pk=f"CUSTOMER#{cust}",
                sk=f"MERCHANT#{merch}",
                tx_count=count,
            ))
    print(f"inserted {len(RELATIONSHIPS)} edges (single direction)")

    print("\n=== Direction A: merchants for CUSTOMER#C001 (main table) ===")
    for e in Edge.query("CUSTOMER#C001", Edge.sk.startswith("MERCHANT#")):
        print(f"  {e.sk}  tx_count={e.tx_count}")

    print("\n=== Direction B: customers for MERCHANT#M001 (inversion-index GSI) ===")
    for e in Edge.inversion_index.query(
        "MERCHANT#M001",
        Edge.pk.startswith("CUSTOMER#"),
    ):
        print(f"  {e.pk}  tx_count={e.tx_count}")

    # Edge.delete_table()
