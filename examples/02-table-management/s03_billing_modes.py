# -*- coding: utf-8 -*-
"""
02-table-management / s03 — billing modes side by side.

Two ways to size a DynamoDB table:

- ``PAY_PER_REQUEST_BILLING_MODE`` (on-demand)
    No capacity to set. You pay per request. Default for this project.

- ``PROVISIONED_BILLING_MODE`` (provisioned)
    You reserve ``read_capacity_units`` and ``write_capacity_units`` per
    second. Cheaper if traffic is steady; throttles if you exceed the
    reserved capacity.

Switching between the two is allowed but rate-limited (DynamoDB lets you
flip a table at most once every 24 hours).
"""

from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute
from pynamodb.constants import (
    PAY_PER_REQUEST_BILLING_MODE,
    PROVISIONED_BILLING_MODE,
)

from pynamodb_session_manager.api import use_boto_session

from yq_dynamodb_poc.one.api import one

PREFIX = "yq_dynamodb_poc"


class OnDemandCard(Model):
    """On-demand: no capacity to set."""

    class Meta:
        table_name = f"{PREFIX}_billing_ondemand"
        region = "us-east-1"
        billing_mode = PAY_PER_REQUEST_BILLING_MODE

    card_id = UnicodeAttribute(hash_key=True)


class ProvisionedCard(Model):
    """Provisioned: reserve RCU/WCU per second."""

    class Meta:
        table_name = f"{PREFIX}_billing_provisioned"
        region = "us-east-1"
        billing_mode = PROVISIONED_BILLING_MODE
        read_capacity_units = 5
        write_capacity_units = 5

    card_id = UnicodeAttribute(hash_key=True)


bsm = one.bsm

with use_boto_session(OnDemandCard, bsm):
    if not OnDemandCard.exists():
        OnDemandCard.create_table(wait=True)
    desc = OnDemandCard.describe_table()
    print(f"[on-demand]   {desc['TableName']}")
    print(
        "  billing_mode = "
        f"{desc.get('BillingModeSummary', {}).get('BillingMode', 'PROVISIONED')}"
    )
    print(f"  throughput   = {desc.get('ProvisionedThroughput')}")

with use_boto_session(ProvisionedCard, bsm):
    if not ProvisionedCard.exists():
        ProvisionedCard.create_table(wait=True)
    desc = ProvisionedCard.describe_table()
    print(f"\n[provisioned] {desc['TableName']}")
    print(
        "  billing_mode = "
        f"{desc.get('BillingModeSummary', {}).get('BillingMode', 'PROVISIONED')}"
    )
    print(f"  throughput   = {desc.get('ProvisionedThroughput')}")

# OnDemandCard.delete_table()
# ProvisionedCard.delete_table()
