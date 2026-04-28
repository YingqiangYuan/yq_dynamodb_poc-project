# -*- coding: utf-8 -*-
"""
08-gsi-and-lsi / s03 — basic LSI.

An LSI shares the main table's partition key but uses a **different**
sort key. It lets you re-sort the rows of a single partition by a
different attribute.

Main table:  PK = card_id, SK = tx_ts        (transactions sorted by time)
LSI:         PK = card_id, SK = amount       (transactions sorted by amount)

Use case: "find the top-3 biggest transactions on this card."

LSI caveats:

- Must be created at table-creation time. You cannot add or remove an
  LSI later — you have to recreate the table.
- The hash key must match the main table's hash key.
- Up to 5 LSIs per table; up to 10 GB of data per partition key (the
  main table normally has no per-partition cap).
- Strongly consistent reads are supported on an LSI (unlike GSIs).
"""

from datetime import datetime, timezone, timedelta

from pynamodb.models import Model
from pynamodb.indexes import LocalSecondaryIndex, AllProjection
from pynamodb.attributes import (
    UnicodeAttribute,
    NumberAttribute,
    UTCDateTimeAttribute,
)
from pynamodb.constants import PAY_PER_REQUEST_BILLING_MODE

from pynamodb_session_manager.api import use_boto_session

from yq_dynamodb_poc.one.api import one

PREFIX = "yq_dynamodb_poc"


class AmountIndex(LocalSecondaryIndex):
    class Meta:
        index_name = "amount-index"
        projection = AllProjection()

    # Hash key MUST match the main table's hash key.
    card_id = UnicodeAttribute(hash_key=True)
    # New sort key: amount.
    amount = NumberAttribute(range_key=True)


class Transaction(Model):
    class Meta:
        table_name = f"{PREFIX}_lsi_transactions"
        region = "us-east-1"
        billing_mode = PAY_PER_REQUEST_BILLING_MODE

    card_id = UnicodeAttribute(hash_key=True)
    tx_ts = UTCDateTimeAttribute(range_key=True)
    amount = NumberAttribute()
    merchant = UnicodeAttribute()

    amount_index = AmountIndex()


bsm = one.bsm

with use_boto_session(Transaction, bsm):
    if not Transaction.exists():
        Transaction.create_table(wait=True)

    for t in Transaction.scan():
        t.delete()

    base_ts = datetime(2026, 4, 1, tzinfo=timezone.utc)
    amounts = [50, 250, 10, 99, 500, 5, 175]

    with Transaction.batch_write() as batch:
        for i, amt in enumerate(amounts):
            batch.save(Transaction(
                card_id="CD001",
                tx_ts=base_ts + timedelta(hours=i),
                amount=amt,
                merchant=f"M{i}",
            ))

    # Top 3 biggest transactions on CD001 — query the LSI sorted by
    # amount descending and limit to 3.
    top3 = list(Transaction.amount_index.query(
        "CD001",
        scan_index_forward=False,
        limit=3,
    ))
    print(f"top 3 biggest transactions on CD001:")
    for tx in top3:
        print(f"  amount={tx.amount} merchant={tx.merchant} tx_ts={tx.tx_ts.isoformat()}")

    # Transaction.delete_table()
