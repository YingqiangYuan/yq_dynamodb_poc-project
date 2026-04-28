# -*- coding: utf-8 -*-
"""
02-table-management / s02 — Model.describe_table().

Returns the same dict that boto3's ``DescribeTable`` API returns: status,
item count, total size in bytes, billing mode, indexes, and so on.
Useful for ops scripts that need to verify table state before acting.

Note: ``ItemCount`` and ``TableSizeBytes`` are refreshed roughly every six
hours, so they lag behind reality. For an exact count run
``Model.count()`` (which scans the table — not free).
"""

import json

from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute
from pynamodb.constants import PAY_PER_REQUEST_BILLING_MODE

from pynamodb_session_manager.api import use_boto_session

from yq_dynamodb_poc.one.api import one

PREFIX = "yq_dynamodb_poc"


class Card(Model):
    class Meta:
        table_name = f"{PREFIX}_describe_cards"
        region = "us-east-1"
        billing_mode = PAY_PER_REQUEST_BILLING_MODE

    card_id = UnicodeAttribute(hash_key=True)


bsm = one.bsm

with use_boto_session(Card, bsm):
    if not Card.exists():
        Card.create_table(wait=True)

    description = Card.describe_table()
    print(json.dumps(description, indent=2, default=str))

    print("\nKey fields:")
    print(f"  table_name       = {description['TableName']}")
    print(f"  table_status     = {description['TableStatus']}")
    print(f"  item_count       = {description['ItemCount']}  (refreshed every ~6h)")
    print(f"  table_size_bytes = {description['TableSizeBytes']}  (refreshed every ~6h)")
    print(
        "  billing_mode     = "
        f"{description.get('BillingModeSummary', {}).get('BillingMode', 'PROVISIONED')}"
    )

    # Card.delete_table()
