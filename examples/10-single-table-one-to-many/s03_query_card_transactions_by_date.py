# -*- coding: utf-8 -*-
"""
10-single-table-one-to-many / s03 — composite-SK range query.

The transaction sort keys look like ``TX#<card_id>#<iso_timestamp>``.
That layout enables a single-query "transactions on card X between time
A and time B" pattern using SK ``between``:

    query(PK="CUSTOMER#C001",
          SK between "TX#CD001#<A>" and "TX#CD001#<B>")

Because the SK encodes ``(card_id, tx_ts)`` in that order, fixing the
``card_id`` segment turns the range into a clean time window on that
specific card.

This is the trick that makes single-table design work for
multi-attribute filtering — pre-encode the access pattern into the SK.
"""

from datetime import datetime, timezone, timedelta

from pynamodb_session_manager.api import use_boto_session

from yq_dynamodb_poc.one.api import one

from models import Entity


bsm = one.bsm

# Same reference time as the seed script.
base_ts = datetime(2026, 4, 27, 9, 0, tzinfo=timezone.utc)
window_start = base_ts + timedelta(hours=2)
window_end = base_ts + timedelta(hours=6)

start_sk = f"TX#CD001#{window_start.isoformat()}"
end_sk = f"TX#CD001#{window_end.isoformat()}"

with use_boto_session(Entity, bsm):
    print(
        f"transactions on CD001 between {window_start.isoformat()} "
        f"and {window_end.isoformat()}:"
    )
    rows = list(Entity.query(
        "CUSTOMER#C001",
        Entity.sk.between(start_sk, end_sk),
    ))
    for e in rows:
        print(f"  {e.tx_ts.isoformat()}  amount={e.amount}  merchant={e.merchant}")
    print(f"({len(rows)} rows)")
