# 06-condition-expression — Conditional writes & optimistic locking

A condition expression is a server-side predicate evaluated **atomically**
against the row before a write is applied. If it evaluates false, the
write is rejected and the row is left untouched.

## Why you need them

DynamoDB has no `BEGIN TRANSACTION; SELECT ... FOR UPDATE` like a SQL
database. Instead, you express the precondition as a condition expression
on each write. Two common uses:

1. **"Insert only if the row does not exist."** Prevents `save()` from
   silently overwriting an existing row.
2. **Optimistic locking.** Two readers grab the same row, both want to
   update it. Each writes back with `condition=Model.version == read_version`
   and `actions=[Model.version.add(1)]`. The first writer wins; the second
   gets a `ConditionalCheckFailedException`, refreshes, and retries.

## Scripts

- `s01_save_if_not_exists.py`   — `save(condition=Card.card_id.does_not_exist())` raises `PutError` on conflict
- `s02_update_with_condition.py` — `update(actions=[...], condition=Card.status == "ACTIVE")` raises `UpdateError` if the row's state has drifted
- `s03_optimistic_lock.py`       — manual `version` field, simulates two concurrent writers and the loser's retry path

## Common condition operators

| Expression | DynamoDB |
|---|---|
| `Card.x == v` / `!=` / `<` / `<=` / `>` / `>=` | comparisons |
| `Card.x.between(a, b)` | `BETWEEN a AND b` |
| `Card.x.is_in(*vals)` | `IN (...)` |
| `Card.x.exists()` / `.does_not_exist()` | `attribute_exists` / `attribute_not_exists` |
| `Card.x.contains(v)` | `contains(...)` (set / list / string) |
| `Card.x.startswith(prefix)` | `begins_with(...)` |
| `cond_a & cond_b` / `cond_a \| cond_b` / `~cond` | `AND` / `OR` / `NOT` |

## Tip: `pynamodb.attributes.VersionAttribute`

pynamodb ships a `VersionAttribute` that automates the optimistic-locking
pattern shown in `s03`. We do it manually here so you understand what's
happening underneath; in production code, `VersionAttribute` is the more
ergonomic choice.
