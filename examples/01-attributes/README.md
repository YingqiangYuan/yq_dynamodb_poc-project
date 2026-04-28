# 01-attributes — Attribute types

A tour of the pynamodb `Attribute` types you reach for most often.
The previous folder used only `UnicodeAttribute` and `NumberAttribute`;
this folder adds the rest, plus the `default` and `null` modifiers.

## Scripts

- `s01_basic_types.py` — `UnicodeAttribute` / `NumberAttribute` / `BooleanAttribute` / `UTCDateTimeAttribute`, plus `default=` and `null=True`
- `s02_collection_types.py` — `ListAttribute`, `MapAttribute` (nested objects), `UnicodeSetAttribute`, `NumberSetAttribute`
- `s03_json_attribute.py` — `JSONAttribute` for arbitrary JSON payloads (e.g. `transaction_metadata`, whose shape varies per row)

## Cheat sheet

| Attribute | DynamoDB type | Use it for |
|---|---|---|
| `UnicodeAttribute` | `S` | Strings (IDs, names, codes) |
| `NumberAttribute` | `N` | Integers and floats |
| `BooleanAttribute` | `BOOL` | True/False flags |
| `UTCDateTimeAttribute` | `S` (ISO-8601) | Timestamps (always UTC) |
| `UnicodeSetAttribute` | `SS` | Unordered set of strings (tags, roles) |
| `NumberSetAttribute` | `NS` | Unordered set of numbers |
| `ListAttribute` | `L` | Ordered list of values |
| `MapAttribute` | `M` | Nested object with named fields |
| `JSONAttribute` | `S` (serialized JSON) | Arbitrary nested data with no fixed schema |

## Modifiers

- `null=True` — the column may be missing or null. Without this, pynamodb refuses to save a row that omits the field.
- `default=<value-or-callable>` — value used when the field is unset on a new instance. Use a **callable** (`default=set`, `default=list`, `default=lambda: datetime.now(UTC)`) for mutable defaults so each row gets its own copy.

`MapAttribute` vs `JSONAttribute`: use `MapAttribute` when the nested
shape is fixed and you want pynamodb to validate it; use `JSONAttribute`
when the payload is freeform.
