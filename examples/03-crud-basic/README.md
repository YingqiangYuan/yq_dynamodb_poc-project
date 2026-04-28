# 03-crud-basic — Single-item CRUD

The four basic single-item operations plus `refresh()` for re-reading
state.

All scripts in this folder share one table,
`yq_dynamodb_poc_crud_transactions`, modeled as a credit-card transaction
with a composite primary key:

- Partition key: `card_id`  (one card has many transactions)
- Sort key:      `tx_ts`    (transaction timestamp, sorts within a card)

Each script wipes the table at the start, so you can run them in any
order.

## Scripts

- `s01_save.py`    — `instance.save()` writes one row (overwrite semantics — same key replaces)
- `s02_get.py`     — `Model.get(hash_key, range_key)` reads one row, handles `DoesNotExist`
- `s03_update.py`  — `instance.update(actions=[...])` partial update with `set` / `add` / `remove`
- `s04_delete.py`  — `instance.delete()` removes one row
- `s05_refresh.py` — `instance.refresh()` re-reads the row from DynamoDB into the same Python object

## `save()` vs `update()`

- `save()` writes the **entire** item, replacing whatever was there at that key.
- `update()` modifies **specific attributes** server-side without round-tripping the rest of the row. Cheaper, and safer when multiple writers touch the same row.

Use `update()` whenever you only need to change a few fields.
Use `save()` when you have the whole item already and want to (re)write it.
