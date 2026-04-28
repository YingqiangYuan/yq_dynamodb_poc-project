# -*- coding: utf-8 -*-
"""
04-batch-operations / s03 — Unprocessed items, the manual way.

When DynamoDB throttles a ``BatchWriteItem`` request (provisioned
capacity exceeded, or transient internal limits), the call does not
fail. Instead the items it could not write come back under
``response["UnprocessedItems"]``, and the caller is expected to retry
those.

pynamodb's ``Model.batch_write`` context manager handles this for you,
with exponential backoff. This script peels back the abstraction using
the boto3 low-level client so the auto-retry behavior is not a black
box. You will rarely write code like this directly.
"""

from datetime import datetime, timezone, timedelta

from pynamodb.models import Model
from pynamodb.attributes import (
    UnicodeAttribute,
    NumberAttribute,
    UTCDateTimeAttribute,
)
from pynamodb.constants import PAY_PER_REQUEST_BILLING_MODE

from pynamodb_session_manager.api import use_boto_session

from yq_dynamodb_poc.one.api import one

PREFIX = "yq_dynamodb_poc"


class Transaction(Model):
    class Meta:
        table_name = f"{PREFIX}_batch_transactions"
        region = "us-east-1"
        billing_mode = PAY_PER_REQUEST_BILLING_MODE

    card_id = UnicodeAttribute(hash_key=True)
    tx_ts = UTCDateTimeAttribute(range_key=True)
    amount = NumberAttribute()
    merchant = UnicodeAttribute()


bsm = one.bsm

with use_boto_session(Transaction, bsm):
    if not Transaction.exists():
        Transaction.create_table(wait=True)

    for t in Transaction.scan():
        t.delete()

    base_ts = datetime(2026, 4, 1, tzinfo=timezone.utc)

    # ---- High level: pynamodb auto-retries unprocessed items ----
    items = [
        Transaction(
            card_id="CD001",
            tx_ts=base_ts + timedelta(minutes=i),
            amount=10.0 + i,
            merchant=f"M{i}",
        )
        for i in range(15)
    ]
    with Transaction.batch_write() as batch:
        for tx in items:
            batch.save(tx)
    print(f"high level: wrote {sum(1 for _ in Transaction.scan())} items total")

    # ---- Low level: boto3 batch_write_item, manually handling UnprocessedItems ----
    table_name = Transaction.Meta.table_name
    client = bsm.dynamodb_client

    request_items = {
        table_name: [
            {
                "PutRequest": {
                    "Item": {
                        "card_id": {"S": "CD002"},
                        "tx_ts": {"S": (base_ts + timedelta(minutes=i)).isoformat()},
                        "amount": {"N": str(100.0 + i)},
                        "merchant": {"S": f"LowLevel{i}"},
                    }
                }
            }
            for i in range(5)
        ]
    }

    attempt = 0
    while request_items:
        attempt += 1
        response = client.batch_write_item(RequestItems=request_items)
        unprocessed = response.get("UnprocessedItems") or {}
        # In a real throttling scenario ``unprocessed`` would be non-empty
        # and we would feed exactly those items back in (with exponential
        # backoff between attempts). On a healthy on-demand table this
        # loop almost always exits after one iteration.
        print(
            f"low level attempt {attempt}: "
            f"unprocessed={ {k: len(v) for k, v in unprocessed.items()} }"
        )
        request_items = unprocessed

    print(f"low level: total items now in table = {sum(1 for _ in Transaction.scan())}")

    # Transaction.delete_table()
