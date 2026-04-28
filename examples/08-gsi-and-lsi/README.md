# 08-gsi-and-lsi — Secondary indexes

A secondary index lets you query a table by a non-primary-key field
efficiently. Without one, the only way to find rows by that field is to
`scan` (read every row, filter client-side) — which is what
`05-query-and-scan/s04_scan_and_filter.py` warned against.

## GSI vs LSI at a glance

| | GSI (Global) | LSI (Local) |
|---|---|---|
| Partition key | **Different** from main table | **Same** as main table |
| Sort key | Any attribute | A different attribute |
| Created | At table creation OR added later | **Only at table creation** |
| Consistency | Eventually consistent only | Strongly consistent supported |
| Capacity | Independent from main table | Shares main table's capacity |
| Per-table count | Up to 20 | Up to 5 |
| Per-partition size limit | None | 10 GB per partition key |

In practice GSIs cover most needs. Reach for an LSI only when you must
have strong consistency on the index, or when partitioning behavior
matters for your access pattern.

## Projections — what gets copied into the index

When DynamoDB writes a row to the table, it writes a (potentially
trimmed) copy of the row into each index. The **projection** controls
which attributes get copied:

| Projection | Index stores | Cost / size | Trade-off |
|---|---|---|---|
| `KeysOnlyProjection()` | Index keys + main table keys | Smallest, cheapest | Reads return only keys; you must do a follow-up `Model.get()` for the rest of the row |
| `IncludeProjection([...])` | Keys + listed extra attributes | Pay for what you copy | Best when only a few attributes are needed alongside |
| `AllProjection()` | Every attribute | Largest, most expensive | Reads are self-sufficient; no follow-up call |

Pick the smallest projection that satisfies your read pattern.

## Scripts

- `s01_gsi_basic.py`       — define a GSI, query it via `Transaction.status_index.query("FAILED")`
- `s02_gsi_projections.py` — three GSIs on one table, one per projection type, comparing what attributes each returns
- `s03_lsi_basic.py`       — define an LSI on a different sort key (`amount`), query the biggest transactions on a card
- `s04_gsi_vs_scan.py`     — same logical query via GSI and via scan + filter, comparing `ConsumedCapacity`
