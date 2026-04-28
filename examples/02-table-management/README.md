# 02-table-management — Table lifecycle

How to create, delete, inspect, and choose a billing mode for tables.

## Scripts

- `s01_create_and_delete.py` — `Model.create_table(wait=True)`, `Model.exists()`, `Model.delete_table()` — full lifecycle in one script
- `s02_describe_table.py` — `Model.describe_table()` returns the table's metadata dict (item count, size, throughput, indexes)
- `s03_billing_modes.py` — side-by-side comparison of `PAY_PER_REQUEST_BILLING_MODE` (on-demand) and `PROVISIONED_BILLING_MODE` (fixed RCU/WCU)

## Picking a billing mode

| Mode | You pay for | Pick it when |
|---|---|---|
| `PAY_PER_REQUEST_BILLING_MODE` | Each read/write request | Traffic is unpredictable, spiky, or very low. Default for POCs and most learning. |
| `PROVISIONED_BILLING_MODE` | Reserved RCU/WCU per second | Steady, predictable traffic where reserved capacity is cheaper, or you need finer cost ceilings. |

Every example in this repo defaults to `PAY_PER_REQUEST_BILLING_MODE` —
on-demand pricing means a forgotten table costs near-zero when idle.

## A note on `s01_create_and_delete.py`

This is the only script in the whole `examples/` series that actually
calls `delete_table()` at the end. Every other script wipes rows but
keeps the table to avoid the `create_table` wait on every rerun (creation
takes 5-30 seconds while DynamoDB provisions the table). Here the
delete is the point of the demo, so we make an exception.
