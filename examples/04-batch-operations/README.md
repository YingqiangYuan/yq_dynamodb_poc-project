# 04-batch-operations — Batch read & write

When you have more than a handful of items, batching cuts per-call
overhead and respects DynamoDB's per-request limits.

## DynamoDB limits

| Operation | Per request limit |
|---|---|
| `BatchWriteItem` | 25 items, 16 MB total |
| `BatchGetItem`   | 100 items, 16 MB total |

pynamodb's `batch_write` context manager and `batch_get` method auto-chunk
larger inputs and auto-retry unprocessed items, so you can hand them
arbitrarily many items.

## Scripts

- `s01_batch_write.py`            — `with Model.batch_write() as batch:` writes 60 items in chunks of 25 transparently
- `s02_batch_get.py`              — `Model.batch_get([(pk, sk), ...])` reads many rows in one call; missing keys are silently skipped
- `s03_batch_with_unprocessed.py` — peek under pynamodb's auto-retry: when DynamoDB throttles, `BatchWriteItem` returns `UnprocessedItems`. The boto3 low-level call is shown so the auto-retry behavior is not a black box.

## `save()` in a batch ≠ `save()` outside a batch

- A standalone `instance.save()` is one `PutItem` call — condition expressions are allowed.
- `batch.save(instance)` is a `BatchWriteItem` request item — **no condition expressions allowed** (DynamoDB API limitation). If you need a condition per item, fall back to single saves or use a `TransactWrite` (see `07-transactions/`).
