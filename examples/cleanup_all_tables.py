# -*- coding: utf-8 -*-
"""
Delete every DynamoDB table whose name starts with ``yq_dynamodb_poc_``
in the project's configured AWS account. Asks for confirmation before
deleting anything.

Usage::

    python examples/cleanup_all_tables.py
"""

import sys

from yq_dynamodb_poc.one.api import one

PREFIX = "yq_dynamodb_poc_"


def list_matching_tables(client) -> list[str]:
    matched: list[str] = []
    paginator = client.get_paginator("list_tables")
    for page in paginator.paginate():
        for name in page.get("TableNames", []):
            if name.startswith(PREFIX):
                matched.append(name)
    return matched


def main() -> int:
    bsm = one.bsm
    client = bsm.dynamodb_client

    tables = list_matching_tables(client)
    if not tables:
        print(f"no tables matching prefix '{PREFIX}' in {bsm.aws_region}")
        return 0

    print(f"about to delete {len(tables)} tables in {bsm.aws_region}:")
    for name in tables:
        print(f"  - {name}")

    answer = input("type 'yes' to confirm: ").strip().lower()
    if answer != "yes":
        print("aborted")
        return 1

    for name in tables:
        client.delete_table(TableName=name)
        print(f"delete issued: {name}")

    print(
        f"done. {len(tables)} tables issued for deletion "
        "(DynamoDB will finish removing them a few seconds later)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
