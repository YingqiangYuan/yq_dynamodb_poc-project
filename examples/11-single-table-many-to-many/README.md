# 11-single-table-many-to-many — Single-table design (M:N)

Three different ways to model an M:N relationship in a single DynamoDB
table, with the same data and the same two-direction queries each time.

## The relationship

```
Customer  ←→  Merchant
   M             N
```

A customer has shopped at many merchants; a merchant has served many
customers. Two queries to support:

- **A**: given a customer, list the merchants they shop at.
- **B**: given a merchant, list the customers it serves.

## The three approaches

| Script | Approach | Pros | Cons |
|---|---|---|---|
| `s01_adjacency_list.py` | **Adjacency list** — write both edges (A→B and B→A) into the main table | Both directions are fast main-table queries; symmetric latency | 2× write cost; ATR (atomic transactional write) needed to keep the two edges consistent |
| `s02_gsi_inversion.py`  | **Inverted GSI** — write one edge; a GSI swaps PK/SK | Single source of truth; one write per edge | Reverse direction goes through the GSI (eventually consistent, slightly higher latency) |
| `s03_composite_gsi.py`  | **Composite GSI** — dedicated `gsi_pk` / `gsi_sk` fields you populate | One GSI serves multiple relationship types (Customer-Merchant + Customer-Card + …) | Higher design upfront — you must enumerate access patterns before building the schema |

Each script is **self-contained**: setup + seed + both directions of
query in one file. Run independently.

## Which one should I pick in real code?

- Few relationship types, write rate moderate → **inverted GSI**.
  Cheapest write path; GSI eventual consistency is rarely a problem.
- Many relationship types in one denormalized graph → **composite GSI**.
  Pays off when you'd otherwise need 4-5 GSIs.
- Strict requirement that both directions are strongly consistent and
  on the main table → **adjacency list**, paired with `TransactWrite`
  for the dual insert.
