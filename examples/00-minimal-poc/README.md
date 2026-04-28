# 00-minimal-poc — Golden Reference

The smallest possible starting point for the whole `examples/` series.
This folder answers two questions:

1. **How does pynamodb map a DynamoDB table to a Python class?**
2. **Why is every script wrapped in `with use_boto_session(Model, bsm):`?**

## Script

- `s01_minimal_poc.py` — `create_table` → wipe rows → `save` → `get` → (commented) `delete_table`

Run it directly:

```bash
python examples/00-minimal-poc/s01_minimal_poc.py
```

## The three core concepts of pynamodb

pynamodb is an ORM for DynamoDB. One DynamoDB table corresponds to one
Python class that inherits from `Model`. Once you understand these three
pieces, the rest of pynamodb is just more of the same:

### 1. Model — one table

```python
class Card(Model):
    ...
```

`Card` represents a DynamoDB table. **Class methods** operate on the table
(`Card.create_table()`, `Card.scan()`, `Card.query(...)`, `Card.get(pk)`).
**Instance methods** operate on a single row (`card.save()`, `card.delete()`,
`card.update(actions=[...])`).

### 2. Attribute — one column

```python
card_id      = UnicodeAttribute(hash_key=True)
holder_name  = UnicodeAttribute()
credit_limit = NumberAttribute()
```

Each class attribute is a column. `hash_key=True` marks the partition key,
`range_key=True` marks the sort key. pynamodb ships with many attribute types
(`UnicodeAttribute`, `NumberAttribute`, `BooleanAttribute`,
`UTCDateTimeAttribute`, `ListAttribute`, `MapAttribute`, `JSONAttribute`, …).
See `01-attributes/` for the full tour.

### 3. Meta — table configuration

```python
class Meta:
    table_name = "yq_dynamodb_poc_cards"
    region = "us-east-1"
    billing_mode = PAY_PER_REQUEST_BILLING_MODE
```

The inner `Meta` class describes the table itself: name, region, billing mode
(on-demand vs provisioned), read/write capacity, and so on. pynamodb reads it
during `create_table` and on every client call.

## Why `use_boto_session`?

By default pynamodb uses boto3's default credential chain (environment
variables, `~/.aws/credentials`, EC2 instance role). In real projects we
often need to **switch AWS accounts / profiles within a single Python
process** — for example to talk to a dev table and a staging table from the
same script.

`pynamodb_session_manager.use_boto_session(Model, bsm)` is a context manager:

- **Entering** the `with` block swaps the underlying connection on `Model`
  for the one configured in `bsm` (a `boto_session_manager.BotoSesManager`
  instance).
- **Exiting** restores the previous connection.

```python
with use_boto_session(Card, bsm):
    Card.create_table(wait=True)            # uses bsm's credentials
    Card(card_id="CD001", ...).save()
# Outside the with block, Card goes back to the default connection.
```

Every example script in this repo wraps its DynamoDB work in this `with`,
pulling credentials from `yq_dynamodb_poc.one.api.one.bsm`. To point the
examples at a different AWS account, edit `profile_name` in
`yq_dynamodb_poc/one/one_03_boto_ses.py` once and every example follows.

## Conventions used by every later folder

| Convention | Notes |
|---|---|
| `PREFIX = "yq_dynamodb_poc"` | All table names look like `yq_dynamodb_poc_<thing>`, so a single prefix scan can clean everything up. |
| Wipe rows at script start, do not drop the table | `for x in Model.scan(): x.delete()` — reruns are idempotent, and you avoid the `create_table` wait every time. |
| Keep `# Model.delete_table()` commented at the end | Uncomment it when you want a clean slate; `examples/cleanup_all_tables.py` will provide a bulk-delete-by-prefix helper. |
| Wrap all DynamoDB calls in `with use_boto_session(Model, bsm):` | Routes every call through the project's AWS account. |
| Business domain: fin-tech credit card | `Customer`, `Card`, `Transaction`, `Merchant`, `PipelineRun` — keeps the examples coherent with the AxiomCard parent project. |

Once this folder makes sense, everything from `01-attributes/` to
`11-single-table-many-to-many/` is just adding features on top of the same
"Model + Attribute + Meta + `use_boto_session`" skeleton.
