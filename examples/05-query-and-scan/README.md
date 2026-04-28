# 05-query-and-scan — Query vs Scan

The single most important DynamoDB performance lesson:

- **`query`** uses an index (the table's primary key, an LSI, or a GSI).
  Give it a partition key value (and optionally a sort-key condition);
  DynamoDB jumps directly to that partition. **Cost scales with the size
  of the result.**
- **`scan`** reads every row in the table, filtering client-side after
  the read. **Cost scales with the size of the table.** Use it for
  ops/admin, not for production traffic.

If you find yourself wanting to scan in production, you usually need a
GSI on the field you're filtering by — see `08-gsi-and-lsi/`.

## Scripts

All scripts share `yq_dynamodb_poc_query_transactions`
(PK = `card_id`, SK = `tx_ts`).

- `s01_query_basic.py`          — `Model.query(hash_key)` and `Model.query(hash_key, Model.tx_ts.between(start, end))`
- `s02_query_sort_and_limit.py` — `scan_index_forward=False` for descending sort; `limit=N` to cap rows
- `s03_query_pagination.py`     — manual pagination with `last_evaluated_key` for stable cursors
- `s04_scan_and_filter.py`      — `Model.scan(Model.amount > 100)` and why it is expensive

## Sort-key conditions

Available as methods on the sort-key attribute:

| Method | DynamoDB |
|---|---|
| `Model.sk == v` | `=` |
| `Model.sk < v`, `<=`, `>`, `>=` | `<`, `<=`, `>`, `>=` |
| `Model.sk.between(a, b)` | `BETWEEN a AND b` |
| `Model.sk.begins_with(prefix)` | `begins_with(...)` (string SKs only) |
