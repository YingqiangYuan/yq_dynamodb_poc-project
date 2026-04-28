# 07-transactions — Cross-item ACID transactions

`TransactWrite` and `TransactGet` give you ACID semantics across multiple
items (and even multiple tables in the same region). Either every action
in the transaction commits, or none do.

## When to use a transaction (and when not to)

**Use it** when the application invariant spans more than one row:
- Money transfer: debit one account, credit another, both or neither.
- Inventory reservation: decrement stock, create order row, both or neither.
- Hierarchical update: write a parent and children atomically.

**Don't use it** for single-row work — `update()` with a condition
expression is cheaper and simpler.

## Limits

| Limit | Value |
|---|---|
| Items per `TransactWriteItems` | 100 |
| Items per `TransactGetItems` | 100 |
| Transaction size (request) | 4 MB |
| Cost | 2× the equivalent non-transactional operation |

## Scripts

All scripts share `yq_dynamodb_poc_tx_accounts` (PK = `customer_id`),
modeling deposit-account-style rows with a `balance` field.

- `s01_transact_write.py`         — atomic `save` + `update` across two rows
- `s02_transact_with_condition.py` — money-transfer pattern with `condition=Account.balance >= amount`; demos rollback when the precondition fails
- `s03_transact_get.py`           — atomic snapshot read of multiple rows; the data you get back is consistent at one point in time

## Boilerplate: getting a `Connection`

`TransactWrite` / `TransactGet` need an explicit
`pynamodb.connection.Connection`. Build it **inside** the
`use_boto_session` block so it picks up the active credentials:

```python
from pynamodb.connection import Connection
from pynamodb.transactions import TransactWrite

with use_boto_session(Account, bsm):
    conn = Connection(region=bsm.aws_region)
    with TransactWrite(connection=conn) as tx:
        tx.update(account_a, actions=[Account.balance.add(-100)])
        tx.update(account_b, actions=[Account.balance.add(+100)])
```
