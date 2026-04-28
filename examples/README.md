# DynamoDB POC examples

Hands-on tour of [pynamodb](https://pynamodb.readthedocs.io/) backed by
[pynamodb-session-manager](https://github.com/MacHu-GWU/pynamodb_session_manager-project),
following the AxiomCard fin-tech credit-card domain.

## Prerequisites

- `mise run inst` to install dependencies.
- `yq_dynamodb_poc.one.api.one.bsm` configured with credentials that
  can manage DynamoDB in `us-east-1` (edit `profile_name` in
  `yq_dynamodb_poc/one/one_03_boto_ses.py` to point at your account).

## How to run

Each script is a plain Python file:

```bash
python examples/00-minimal-poc/s01_minimal_poc.py
```

Folders **00 – 08** contain independently runnable scripts — pick any
one in any order. Folders **09 – 11** are sequential demos: run scripts
in numeric order (`s01 → s02 → ...`).

## Conventions every folder follows

- The first run creates the table on demand (`Model.create_table(wait=True)`).
- Each script then **wipes existing rows** at the start
  (`for x in Model.scan(): x.delete()`) so reruns are idempotent. The
  table itself is **not** dropped — that avoids the 5–30s
  `create_table` wait every time.
- Every script ends with a commented-out `# Model.delete_table()`.
  Uncomment it once you're done with that table.
- All DynamoDB calls run inside `with use_boto_session(Model, bsm):`
  using the `bsm` from `yq_dynamodb_poc.one.api.one`.
- All table names start with `yq_dynamodb_poc_` so
  `cleanup_all_tables.py` can find them.

## Folders

| #  | Folder | Topic |
|---|---|---|
| 00 | [`00-minimal-poc/`](00-minimal-poc/)                            | Golden reference: Model + Attribute + Meta + `use_boto_session` |
| 01 | [`01-attributes/`](01-attributes/)                              | Attribute types: scalar, collection, JSON |
| 02 | [`02-table-management/`](02-table-management/)                  | `create_table` / `describe_table` / billing modes |
| 03 | [`03-crud-basic/`](03-crud-basic/)                              | `save` / `get` / `update` / `delete` / `refresh` |
| 04 | [`04-batch-operations/`](04-batch-operations/)                  | `batch_write` / `batch_get`, unprocessed items |
| 05 | [`05-query-and-scan/`](05-query-and-scan/)                      | `query` vs `scan`, pagination, sort + limit |
| 06 | [`06-condition-expression/`](06-condition-expression/)          | Conditional writes, optimistic locking |
| 07 | [`07-transactions/`](07-transactions/)                          | `TransactWrite` / `TransactGet`, ACID across items |
| 08 | [`08-gsi-and-lsi/`](08-gsi-and-lsi/)                            | Secondary indexes, projections, GSI vs scan cost |
| 09 | [`09-pipeline-metadata-demo/`](09-pipeline-metadata-demo/)      | Composite demo: replicate the AxiomCard Pipeline Metadata table |
| 10 | [`10-single-table-one-to-many/`](10-single-table-one-to-many/)  | Single-table design: classic 1:N (Customer → Card → Transaction) |
| 11 | [`11-single-table-many-to-many/`](11-single-table-many-to-many/)| Single-table design: M:N three ways (adjacency / GSI inversion / composite GSI) |

## Utility

- [`cleanup_all_tables.py`](cleanup_all_tables.py) — list every
  `yq_dynamodb_poc_*` table and delete them after a confirmation prompt.

## Suggested learning order

1. **00 → 02** to internalize the pynamodb skeleton and table lifecycle.
2. **03 → 05** for everyday CRUD and read patterns.
3. **06 → 08** for correctness (conditions, transactions) and performance (indexes).
4. **09** to see all of the above applied to the real AxiomCard pipeline-metadata table.
5. **10 → 11** for single-table design — the access-pattern-first
   modeling style that distinguishes DynamoDB from a relational database.
