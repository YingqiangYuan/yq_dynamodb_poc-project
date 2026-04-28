# 10-single-table-one-to-many — Single-table design (1:N)

Two-level 1:N hierarchy stored in **one** DynamoDB table:

```
Customer  →  Card  →  Transaction
   1            N         N
```

A customer has many cards; a card has many transactions. All three
entity types live in the same table, distinguished by a prefix on the
sort key.

## Why single-table?

DynamoDB has no JOIN. Spread Customer/Card/Transaction across three
tables and you'd need three round-trips to answer "show me everything
for customer C001". With single-table design, that becomes one
`query(PK="CUSTOMER#C001")`.

## The key schema

| PK                  | SK                                       | entity_type   |
|---|---|---|
| `CUSTOMER#C001`     | `PROFILE`                                | `CUSTOMER`    |
| `CUSTOMER#C001`     | `CARD#CD001`                             | `CARD`        |
| `CUSTOMER#C001`     | `CARD#CD002`                             | `CARD`        |
| `CUSTOMER#C001`     | `TX#CD001#2026-04-27T10:00:00+00:00`     | `TRANSACTION` |
| `CUSTOMER#C001`     | `TX#CD001#2026-04-27T11:30:00+00:00`     | `TRANSACTION` |
| `CUSTOMER#C001`     | `TX#CD002#2026-04-27T09:15:00+00:00`     | `TRANSACTION` |

Two patterns to notice:

- **Same partition** (`PK = CUSTOMER#C001`) — every row about that
  customer lives together, so one `query` returns all of it.
- **Composite sort key** for transactions (`TX#<card_id>#<tx_ts>`) —
  the SK encodes both "which card" and "when", which makes range
  queries on a specific card's transactions efficient (see `s03`).

## Run order (mandatory)

```bash
python examples/10-single-table-one-to-many/s01_setup_and_seed.py
python examples/10-single-table-one-to-many/s02_query_patterns.py
python examples/10-single-table-one-to-many/s03_query_card_transactions_by_date.py
```

## Files

- `models.py` — single `Entity` model with all entity-specific fields nullable, plus an `entity_type` discriminator.
- `s01_setup_and_seed.py`                    — create the table; seed 2 customers, 4 cards, 9 transactions.
- `s02_query_patterns.py`                    — three classic single-table reads: full hierarchy, cards only, one card's transactions.
- `s03_query_card_transactions_by_date.py`   — composite-SK range query: a specific card's transactions within a time window.
