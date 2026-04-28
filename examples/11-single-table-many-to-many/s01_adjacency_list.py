# -*- coding: utf-8 -*-
"""
11-single-table-many-to-many / s01 — Adjacency list.

Each Customer↔Merchant relationship is stored as **two** rows:

    PK=CUSTOMER#C001  SK=MERCHANT#M001
    PK=MERCHANT#M001  SK=CUSTOMER#C001

Both directions are then plain main-table queries:

- "merchants for customer C001"  → ``query("CUSTOMER#C001", SK begins_with "MERCHANT#")``
- "customers for merchant M001" → ``query("MERCHANT#M001",  SK begins_with "CUSTOMER#")``

Trade-offs:

- Write cost is **2x**: every relationship touches two rows.
- The pair must be inserted atomically or the graph drifts. Use
  ``TransactWrite`` (shown below) — ``batch_write`` would do it as two
  independent writes with no atomicity guarantee.

Cost summary:

- Write : 2 items per edge (atomic via TransactWrite — 2x cost of one PutItem)
- Read  : 1 main-table query, both directions
- Consistency: strong (main table)
"""

from datetime import datetime, timezone

from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, NumberAttribute, UTCDateTimeAttribute
from pynamodb.constants import PAY_PER_REQUEST_BILLING_MODE
from pynamodb.connection import Connection
from pynamodb.transactions import TransactWrite

from pynamodb_session_manager.api import use_boto_session

from yq_dynamodb_poc.one.api import one

PREFIX = "yq_dynamodb_poc"


class Edge(Model):
    class Meta:
        table_name = f"{PREFIX}_st_mtm_adjacency"
        region = "us-east-1"
        billing_mode = PAY_PER_REQUEST_BILLING_MODE

    pk = UnicodeAttribute(hash_key=True)
    sk = UnicodeAttribute(range_key=True)
    first_seen = UTCDateTimeAttribute(default=lambda: datetime.now(timezone.utc))
    tx_count = NumberAttribute(default=0)


# (customer, merchant, tx_count) — Alice shops at three merchants;
# Bob shops at two; M002 sees only one customer.
RELATIONSHIPS = [
    ("C001", "M001", 12),
    ("C001", "M002", 4),
    ("C001", "M003", 9),
    ("C002", "M001", 7),
    ("C002", "M003", 3),
]


def insert_edge(conn: Connection, customer: str, merchant: str, count: int) -> None:
    """Atomically write both directions of one edge."""

    forward = Edge(pk=f"CUSTOMER#{customer}", sk=f"MERCHANT#{merchant}", tx_count=count)
    backward = Edge(pk=f"MERCHANT#{merchant}", sk=f"CUSTOMER#{customer}", tx_count=count)
    with TransactWrite(connection=conn) as tx:
        tx.save(forward)
        tx.save(backward)


bsm = one.bsm

with use_boto_session(Edge, bsm):
    if not Edge.exists():
        Edge.create_table(wait=True)

    for e in Edge.scan():
        e.delete()

    conn = Connection(region=bsm.aws_region)
    for cust, merch, count in RELATIONSHIPS:
        insert_edge(conn, cust, merch, count)
    print(f"inserted {len(RELATIONSHIPS)} edges (= {2 * len(RELATIONSHIPS)} rows)")

    print("\n=== Direction A: merchants for CUSTOMER#C001 (main table) ===")
    for e in Edge.query("CUSTOMER#C001", Edge.sk.startswith("MERCHANT#")):
        print(f"  {e.sk}  tx_count={e.tx_count}")

    print("\n=== Direction B: customers for MERCHANT#M001 (main table) ===")
    for e in Edge.query("MERCHANT#M001", Edge.sk.startswith("CUSTOMER#")):
        print(f"  {e.sk}  tx_count={e.tx_count}")

    # Edge.delete_table()
