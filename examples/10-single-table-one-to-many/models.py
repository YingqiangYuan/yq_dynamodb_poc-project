# -*- coding: utf-8 -*-
"""
Shared single-table model for the 1:N demo.

One Python class for three entity types (Customer / Card / Transaction).
Every field that is specific to one entity type is ``null=True``;
``entity_type`` is the discriminator.
"""

from pynamodb.models import Model
from pynamodb.attributes import (
    UnicodeAttribute,
    NumberAttribute,
    UTCDateTimeAttribute,
)
from pynamodb.constants import PAY_PER_REQUEST_BILLING_MODE

PREFIX = "yq_dynamodb_poc"


class Entity(Model):
    class Meta:
        table_name = f"{PREFIX}_st_otm"
        region = "us-east-1"
        billing_mode = PAY_PER_REQUEST_BILLING_MODE

    pk = UnicodeAttribute(hash_key=True)
    sk = UnicodeAttribute(range_key=True)
    entity_type = UnicodeAttribute()  # CUSTOMER / CARD / TRANSACTION

    # Customer fields
    name = UnicodeAttribute(null=True)
    email = UnicodeAttribute(null=True)

    # Card fields
    holder_name = UnicodeAttribute(null=True)
    credit_limit = NumberAttribute(null=True)

    # Transaction fields
    amount = NumberAttribute(null=True)
    merchant = UnicodeAttribute(null=True)
    tx_ts = UTCDateTimeAttribute(null=True)
