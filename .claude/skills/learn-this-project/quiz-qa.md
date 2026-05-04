# Quiz Q&A — DynamoDB POC

50 questions across 10 categories, all grounded in this repository's
example scripts. The focus is **how to use** pynamodb, the data
modelling choices, and the access patterns the examples demonstrate —
not DynamoDB's internal architecture (for that, see
[dynamodb-background.md](dynamodb-background.md)).

## Index

- [Category 1: pynamodb Skeleton & Project Conventions](#category-1-pynamodb-skeleton--project-conventions) — Q1–Q5
- [Category 2: Attribute Types](#category-2-attribute-types) — Q6–Q11
- [Category 3: Table Management](#category-3-table-management) — Q12–Q15
- [Category 4: CRUD Operations](#category-4-crud-operations) — Q16–Q20
- [Category 5: Batch Operations](#category-5-batch-operations) — Q21–Q24
- [Category 6: Query & Scan](#category-6-query--scan) — Q25–Q30
- [Category 7: Conditional Writes & Optimistic Locking](#category-7-conditional-writes--optimistic-locking) — Q31–Q35
- [Category 8: Transactions](#category-8-transactions) — Q36–Q38
- [Category 9: GSI & LSI](#category-9-gsi--lsi) — Q39–Q45
- [Category 10: Single-Table Design](#category-10-single-table-design) — Q46–Q50

---

## Category 1: pynamodb Skeleton & Project Conventions

### Q1. What are the three core pieces of a pynamodb model, and what does each represent?

`Model` (one Python class = one DynamoDB table), `Attribute` (one
class-level attribute = one column with a typed wrapper), and the
inner `Meta` class (table-level configuration: `table_name`, `region`,
`billing_mode`). **Class methods** on `Model` operate on the table
(`Card.create_table()`, `Card.scan()`, `Card.query(...)`,
`Card.get(pk)`); **instance methods** operate on one row (`card.save()`,
`card.delete()`, `card.update(...)`, `card.refresh()`). See
`examples/00-minimal-poc/s01_minimal_poc.py:36-51` and
`examples/00-minimal-poc/README.md` (sections "Model", "Attribute",
"Meta").

### Q2. What does `with use_boto_session(Model, bsm):` do, and why is every script wrapped in it?

It is a context manager from `pynamodb-session-manager`. Entering the
block swaps `Model`'s underlying boto3 connection for the one
configured in `bsm` (a `BotoSesManager` from `boto_session_manager`);
exiting restores the previous connection. That lets a single Python
process talk to multiple AWS accounts/profiles in sequence. To point
every example at a different account, you only need to edit
`profile_name` once in `yq_dynamodb_poc/one/one_03_boto_ses.py`. See
`examples/00-minimal-poc/s01_minimal_poc.py:62` and
`examples/00-minimal-poc/README.md` (section "Why use_boto_session?").

### Q3. Every script wipes existing rows but keeps the table. Why not just `delete_table()` then `create_table()` for a clean slate?

`create_table(wait=True)` blocks 5–30 seconds until DynamoDB reports
`ACTIVE`. Wiping rows with `for x in Model.scan(): x.delete()` is
nearly instant and still gives an idempotent script. The only
exception is `examples/02-table-management/s01_create_and_delete.py`,
which deliberately drops the table to demonstrate the lifecycle.
Every other script leaves `# Model.delete_table()` commented out at
the bottom for opt-in cleanup. See `examples/README.md` (Conventions
section).

### Q4. Why do all table names in this project start with `yq_dynamodb_poc_`?

Two reasons. (1) The prefix prevents collisions with other tables in
the same AWS account. (2) `examples/cleanup_all_tables.py` lists every
table whose name begins with `yq_dynamodb_poc_` and deletes them after
a `yes` prompt — one prefix scan cleans the whole repo. See
`examples/00-minimal-poc/s01_minimal_poc.py:33` and
`examples/cleanup_all_tables.py`.

### Q5. Given `card = Card(card_id="CD001", holder_name="Alice", credit_limit=10000)`, which line actually goes to AWS, and what call signature does `Card.get("CD001")` use under the hood?

`card.save()` is the call that hits AWS — it is one `PutItem` request
that writes the entire item, **overwriting** any prior row at the same
primary key. `Card.get(...)` is one `GetItem` request: for a hash-only
model it takes only the partition key; for a composite-key model it
takes both `(hash_key, range_key)`. If the row does not exist, `get()`
raises `Model.DoesNotExist`. See
`examples/00-minimal-poc/s01_minimal_poc.py:73-76` and
`examples/03-crud-basic/s02_get.py`.

---

## Category 2: Attribute Types

### Q6. Name the basic scalar attribute classes pynamodb ships with, and the DynamoDB type each maps to.

`UnicodeAttribute` → S (string); `NumberAttribute` → N (number, for
both integers and floats); `BooleanAttribute` → BOOL;
`UTCDateTimeAttribute` → S (an ISO-8601 timezone-aware timestamp
string). Each one handles serialization/deserialization
automatically — your model carries native Python types while DynamoDB
sees only its native types. See `examples/01-attributes/s01_basic_types.py`
and `examples/01-attributes/README.md`.

### Q7. What is the difference between `MapAttribute` and `JSONAttribute`, and when would you reach for each?

`MapAttribute` is for **fixed-shape** nested objects: you subclass it
and declare typed fields (e.g. `class Address(MapAttribute): street =
UnicodeAttribute(); city = UnicodeAttribute()`), and pynamodb
validates the shape on save. `JSONAttribute` stores **arbitrary** JSON
serialized to one string field — no schema validation — perfect for
per-row payloads whose shape varies (analytics events, freeform
metadata). Use Map when the structure is stable and you want type
checking; use JSON when each row may carry a different structure. See
`examples/01-attributes/s02_collection_types.py` and
`examples/01-attributes/s03_json_attribute.py`.

### Q8. Why does the project write `default=lambda: datetime.now(timezone.utc)` instead of `default=datetime.now(timezone.utc)`?

`default=` accepts either a value or a **callable**. Passing
`datetime.now(...)` directly evaluates it once at class-definition
time, so every row that uses the default ends up with the same frozen
timestamp. Wrapping it in a lambda defers the call to row-creation
time, giving each row a fresh `now()`. The same logic applies to
mutable defaults: prefer `default=set` and `default=list` (callables)
over `default=set()` / `default=[]` (shared instances). See
`examples/01-attributes/README.md` and
`examples/11-single-table-many-to-many/s01_adjacency_list.py:52`.

### Q9. What does `null=True` do on a pynamodb attribute, and why is it essential for single-table designs?

With `null=True`, an attribute may be left unset and the row will
still save. Without it, a `save()` that omits the attribute raises a
validation error. In single-table designs (folders 10 and 11), one
`Entity` model represents Customers, Cards, and Transactions — each
row only sets the fields relevant to its type, so every entity-specific
attribute is declared `null=True`. See
`examples/10-single-table-one-to-many/models.py` and
`examples/01-attributes/README.md`.

### Q10. What is the practical difference between a `UnicodeSetAttribute` and a `ListAttribute` of strings?

A Set (DynamoDB type SS) is **unordered** and **deduplicated** — the
same value stored twice is stored once. A List (DynamoDB type L)
preserves order and duplicates. Sets must also be non-empty
(DynamoDB rejects empty sets). Choose Sets for tag/category fields
where dedup is the goal; choose Lists when order matters or
duplicates are meaningful (e.g. an audit trail). See
`examples/01-attributes/s02_collection_types.py`.

### Q11. If a column already stores ISO-8601 strings, why prefer `UTCDateTimeAttribute` over plain `UnicodeAttribute`?

`UTCDateTimeAttribute` automatically serializes between Python
`datetime` objects on the model and the ISO-8601 string in DynamoDB.
With `UnicodeAttribute` you have to call `.isoformat()` and
`datetime.fromisoformat()` yourself everywhere, and you lose the
timezone-awareness check. The on-disk representation is identical —
the difference is purely on the Python side, which makes downstream
code (e.g. range queries with `tx_ts.between(start, end)`) cleaner.
See `examples/01-attributes/s01_basic_types.py`.

---

## Category 3: Table Management

### Q12. `PAY_PER_REQUEST_BILLING_MODE` vs `PROVISIONED_BILLING_MODE` — when is each appropriate?

**PAY_PER_REQUEST** (on-demand) charges per request and auto-scales —
you pay nothing when idle, no capacity planning needed. This is the
default in every example. **PROVISIONED** lets you pre-allocate fixed
RCU/WCU; it is cheaper at sustained high traffic but you pay even
when idle and risk throttling on traffic spikes unless you enable
auto-scaling. The rule of thumb: on-demand for unpredictable, spiky,
or POC workloads; provisioned only when you have measured a stable
baseline. See `examples/02-table-management/s03_billing_modes.py` and
`examples/02-table-management/README.md`.

### Q13. Across all 12 example folders, which single script actually drops the table at the end?

Only `examples/02-table-management/s01_create_and_delete.py`. It
exists specifically to demonstrate the full
`exists` → `create_table(wait=True)` → `delete_table` lifecycle.
Every other script leaves `# Model.delete_table()` commented out at
the bottom — wiping rows is enough for idempotent reruns and avoids
the 5–30s `create_table` wait every time. See
`examples/02-table-management/s01_create_and_delete.py` and
`examples/README.md` (Conventions section).

### Q14. What does `Model.create_table(wait=True)` do, and what changes if you set `wait=False`?

With `wait=True`, the call blocks until DynamoDB reports the table is
in the `ACTIVE` state — typically 5–30 seconds — so subsequent
reads/writes succeed. With `wait=False` (or omitted), it returns
immediately as soon as DynamoDB accepts the request; the table is in
`CREATING` state and any operation against it will fail until it
transitions to `ACTIVE`. Most example scripts use `wait=True` because
the next line is usually a `scan` or `save`. See
`examples/00-minimal-poc/s01_minimal_poc.py:65` and
`examples/02-table-management/s01_create_and_delete.py`.

### Q15. What information does `Model.describe_table()` return, and what is it useful for?

It returns a dict with table metadata: item count, table size in
bytes, billing mode, provisioned throughput (if any), the list of
attribute definitions, the key schema, and any GSI/LSI definitions
with their states. Useful for monitoring (size growth), capacity
tuning, and verifying that a deployment matches the expected schema.
See `examples/02-table-management/s02_describe_table.py`.

---

## Category 4: CRUD Operations

### Q16. `instance.save()` vs `instance.update(actions=[...])` — what is the trade-off?

`save()` is one `PutItem` call that writes the **entire** item,
replacing whatever was at that primary key — you must have all
attributes in memory. `update(actions=[...])` is one `UpdateItem`
call that modifies only the listed attributes server-side, without
round-tripping the rest of the row — cheaper bandwidth-wise, and it
avoids races on unrelated fields. Use `save()` when you have just
constructed a fresh row; use `update()` for partial mutations to
existing rows. See `examples/03-crud-basic/s01_save.py` and
`examples/03-crud-basic/s03_update.py`.

### Q17. On a composite-key table, what is `Model.get()`'s call signature, and what happens when the row doesn't exist?

`Model.get(hash_key, range_key)` — both keys are required as
positional arguments. If no row matches, pynamodb raises
`Model.DoesNotExist` (a subclass of `pynamodb.exceptions.DoesNotExist`).
The idiomatic pattern is `try: row = Model.get(pk, sk); except
Model.DoesNotExist: ...` either to return `None` or to take the
"create" branch. See `examples/03-crud-basic/s02_get.py`.

### Q18. What three action types can you pass to `update(actions=[...])`, and what does each one do?

`Attr.set(value)` — overwrite an attribute with a new value
(`Card.credit_limit.set(15000)`). `Attr.add(delta)` — atomic increment
for numbers, or union for sets (`Card.version.add(1)`). `Attr.remove()`
— delete the attribute from the row entirely. All three become parts
of one `UpdateExpression` and apply atomically. See
`examples/03-crud-basic/s03_update.py` and
`examples/06-condition-expression/s03_optimistic_lock.py:63-69`.

### Q19. When would you call `instance.refresh()`?

When another writer may have updated the row since you fetched it
and you want your local Python object to reflect server state — for
example, after a conditional update fails and you need to retry with
the new version, or after a long-running background job. `refresh()`
issues a fresh `GetItem` and copies the latest attribute values back
onto the same Python instance. See
`examples/03-crud-basic/s05_refresh.py` and
`examples/06-condition-expression/s03_optimistic_lock.py:85`.

### Q20. `instance.delete()` is described as "idempotent" — what does that mean here?

Calling `delete()` on a row that is already gone does **not** raise
— DynamoDB returns success silently. Same primary key, called any
number of times, results in the row being absent. This is convenient
for cleanup loops and is why every script can confidently start with
`for x in Model.scan(): x.delete()`. See
`examples/03-crud-basic/s04_delete.py`.

---

## Category 5: Batch Operations

### Q21. What are the per-request limits for `BatchWriteItem` and `BatchGetItem`?

`BatchWriteItem` accepts up to **25 items**, **16 MB** total per
request. `BatchGetItem` accepts up to **100 items**, **16 MB** total.
pynamodb's `with Model.batch_write() as batch:` and
`Model.batch_get([...])` auto-chunk inputs that exceed those limits,
so you can hand them arbitrarily many items and let pynamodb make as
many round-trips as needed. See
`examples/04-batch-operations/README.md` (limits table) and
`examples/04-batch-operations/s01_batch_write.py`.

### Q22. Inside `with Model.batch_write() as batch:`, why can't you pass `condition=...` to `batch.save(instance)`?

Because `batch.save(instance)` becomes a `BatchWriteItem` request
item, and DynamoDB's `BatchWriteItem` API does not support condition
expressions — that is a server-side limit, not a pynamodb one. If
you need a per-item condition (e.g. "insert only if not exists"),
fall back to single `instance.save(condition=...)` calls, or use
`TransactWrite` from `examples/07-transactions/`. See
`examples/04-batch-operations/README.md` (last section).

### Q23. `Model.batch_get([(pk, sk), (pk, sk), ...])` is called with 5 keys but only 3 rows exist — what comes back?

pynamodb returns the 3 found rows and **silently skips** the 2
missing keys — no exception, no placeholder. If you need to know
which keys were missing, you must compare the returned rows' primary
keys against your input list. This mirrors DynamoDB's `BatchGetItem`
API behavior. See `examples/04-batch-operations/s02_batch_get.py`.

### Q24. Why does `examples/04-batch-operations/s03_batch_with_unprocessed.py` deliberately drop down to boto3 instead of using pynamodb?

When DynamoDB throttles a `BatchWriteItem` request, the response
includes an `UnprocessedItems` payload — the items it did not write.
pynamodb auto-retries these transparently, which is great for
production code but hides the mechanism. The script uses the boto3
low-level client so you can see the `UnprocessedItems` payload
yourself, understand what auto-retry is doing for you, and recognize
the symptom in CloudWatch metrics. See
`examples/04-batch-operations/s03_batch_with_unprocessed.py` and
`examples/04-batch-operations/README.md` (s03 description).

---

## Category 6: Query & Scan

### Q25. `query()` vs `scan()` — what is the cost-model difference, and why is "never scan in production" the standard advice?

`query()` uses an index (the main table's primary key, an LSI, or a
GSI) and reads only the rows in one partition that match — cost
scales with the **result size**. `scan()` reads **every** row in the
table and applies any filter client-side after the read — cost
scales with **table size**, regardless of how many rows match. On a
100M-row table, a scan that returns 10 rows still pays for reading
all 100M. The fix when you need a non-key access pattern is to add
a GSI. See `examples/05-query-and-scan/README.md` and
`examples/05-query-and-scan/s04_scan_and_filter.py`.

### Q26. What sort-key conditions can `query()` use, and what about the hash key?

The hash key always uses **equality only**. The sort key supports
equality (`==`), comparisons (`<`, `<=`, `>`, `>=`), inclusive ranges
(`.between(a, b)`), and string prefixes (`.begins_with(prefix)`).
Example: `Transaction.query(card_id, Transaction.tx_ts.between(start,
end))`. See `examples/05-query-and-scan/s01_query_basic.py`.

### Q27. How do `scan_index_forward=False` and `limit=N` combine, and what real-world question do they answer?

`scan_index_forward=False` reads the sort key in **descending** order;
`limit=N` stops after N rows. Together they implement "give me the
most recent N rows for this partition" — e.g. the last 10
transactions on a card, or the latest 10 runs of a pipeline. With
`limit=N` only, you'd get the **earliest** N rows; with
`scan_index_forward=False` only, you'd read the entire partition in
reverse. See `examples/05-query-and-scan/s02_query_sort_and_limit.py`
and `examples/09-pipeline-metadata-demo/s03_queries.py`.

### Q28. What is `last_evaluated_key`, and what problem does it solve?

A single `query()` call returns at most 1 MB of data; if more
results exist, the response carries a `last_evaluated_key` cursor
pointing at where the next page starts. To fetch the next page you
call `query()` again with `last_evaluated_key=<that cursor>`. The
cursor is stable across calls, so manual pagination works for
arbitrarily large result sets and you can persist the cursor (e.g.
to a job state store) and resume later. See
`examples/05-query-and-scan/s03_query_pagination.py`.

### Q29. `Model.scan(filter=Model.amount > 100)` — does the filter run before or after the read, and what does that mean for cost?

**After.** DynamoDB reads every row in the table, then applies the
filter and returns only matches. You pay read capacity for **all**
rows scanned, not only the ones returned. So a filtered scan that
returns 1% of rows still costs 100% of a full scan. This is the
core reason the answer to "I need to query by a non-key attribute"
is almost always "build a GSI on it". See
`examples/05-query-and-scan/s04_scan_and_filter.py`.

### Q30. In `03-crud-basic`, the table has `card_id` as PK and `tx_ts` (timestamp string) as SK. Why is that schema choice useful?

Because all transactions for a given card are stored sorted by time
within the card's partition. That makes "transactions in the last 7
days for card CD001" a single
`query("CD001", tx_ts.between(start, end))` — one partition, returns
only the matching rows. If `tx_ts` were just a regular attribute
without being the sort key, the same question would require either
a scan-with-filter or a separate GSI. The PK/SK choice **is** the
performance choice. See `examples/03-crud-basic/README.md` and
`examples/05-query-and-scan/s01_query_basic.py`.

---

## Category 7: Conditional Writes & Optimistic Locking

### Q31. What does `condition=Card.card_id.does_not_exist()` on `save()` accomplish?

It tells DynamoDB to write the row **only if** no row with that
primary key already exists. If a row exists, the write is rejected
and pynamodb raises `PutError` (which wraps DynamoDB's
`ConditionalCheckFailedException`); the existing row is unchanged.
This is the safe "insert-only-don't-overwrite" pattern, equivalent
to SQL's `INSERT ... WHERE NOT EXISTS`. See
`examples/06-condition-expression/s01_save_if_not_exists.py`.

### Q32. Walk through the optimistic-locking pattern in `s03_optimistic_lock.py` with a manual `version` field.

Each row carries `version = NumberAttribute(default=0)`. Both writers
`Card.get("CD001")` and remember the version they read. Each writer
calls `update(actions=[<their changes>, Card.version.add(1)],
condition=Card.version == <remembered>)`. Writer A's condition holds,
DynamoDB applies the update and bumps version 0 → 1. Writer B's
condition (`version == 0`) now fails because the server's version is
1; pynamodb raises `UpdateError`. The losing writer calls
`instance.refresh()` to pick up the new state and retries.
First-writer-wins semantics, no database lock. See
`examples/06-condition-expression/s03_optimistic_lock.py:55-93`.

### Q33. How is `pynamodb.attributes.VersionAttribute` different from the manual version pattern shown in `s03_optimistic_lock.py`?

`VersionAttribute` automates the same pattern: pynamodb auto-bumps
it on every `save`/`update` and auto-attaches the matching condition
expression, so you do not write the `condition=` clause yourself.
The s03 script does it by hand specifically to make the mechanism
visible — once you have seen it, prefer `VersionAttribute` in real
code. See `examples/06-condition-expression/s03_optimistic_lock.py`
docstring (lines 18–19).

### Q34. What operators are available on Attribute objects when building a condition expression?

Comparisons (`==`, `!=`, `<`, `<=`, `>`, `>=`); range (`.between(a,
b)`); set membership (`.is_in(*values)`); existence (`.exists()`,
`.does_not_exist()`); substring/prefix (`.contains(v)`,
`.startswith(prefix)`); and Boolean composition (`&` for AND, `|` for
OR, `~` for NOT). They combine freely:
`(Card.status == "ACTIVE") & (Card.balance > 0)`. See
`examples/06-condition-expression/README.md`.

### Q35. What exception does pynamodb raise on a failed conditional write, and what underlying DynamoDB error does it wrap?

`save(condition=...)` failure raises `pynamodb.exceptions.PutError`;
`update(condition=...)` raises `UpdateError`; `delete(condition=...)`
raises `DeleteError`. All three wrap DynamoDB's
`ConditionalCheckFailedException`. The condition is evaluated
atomically server-side, so when the exception fires the row is
guaranteed unchanged. See
`examples/06-condition-expression/s01_save_if_not_exists.py` and
`examples/06-condition-expression/s03_optimistic_lock.py:81`.

---

## Category 8: Transactions

### Q36. When should you reach for `TransactWrite` instead of a single-item `update(condition=...)`?

Use `TransactWrite` when an **invariant spans multiple rows** that
must commit or roll back together — money transfer between two
accounts, an order plus its line items, or atomic insert of both
edges in an adjacency-list relationship. For single-row work, a
regular `update(condition=...)` is enough and costs half as much
(transactions cost ~2× the underlying operations). See
`examples/07-transactions/README.md` and
`examples/11-single-table-many-to-many/s01_adjacency_list.py:67-74`.

### Q37. Why does the transactions example explicitly construct `Connection(region=bsm.aws_region)` inside the `use_boto_session` block, rather than relying on the Model's connection like everywhere else?

`TransactWrite` and `TransactGet` operate **across multiple Models**
(and possibly multiple tables), so they take a `connection=` argument
rather than being tied to one Model's connection. The `Connection`
must be built **inside** the `with use_boto_session(...)` block so
it inherits the right credentials. See
`examples/07-transactions/README.md` (Connection section) and
`examples/07-transactions/s02_transact_with_condition.py:66`.

### Q38. The money-transfer example debits one account and credits another inside one `TransactWrite`, with a balance condition on the debit. What happens if the balance check fails?

DynamoDB rejects the entire transaction — the debit's condition
fails, the credit is **not** applied, and pynamodb raises
`TransactWriteError`. There is no half-state where the source was
debited but the target was not credited. This all-or-nothing
semantics is the entire reason to pay the 2× cost of a transaction.
See `examples/07-transactions/s02_transact_with_condition.py:39-51`.

---

## Category 9: GSI & LSI

### Q39. List the four most important differences between a Global Secondary Index (GSI) and a Local Secondary Index (LSI).

(1) **Partition key**: GSI's PK can be any attribute; LSI's PK
**must** match the main table's PK. (2) **When created**: a GSI can
be added at table creation or later; an LSI **only** at table
creation. (3) **Consistency**: GSI is eventually consistent only;
LSI supports strong-consistency reads. (4) **Capacity & limits**:
GSI has independent throughput, up to 20 per table; LSI shares the
main table's throughput, up to 5 per table, and each main-table
partition's LSI data is capped at 10 GB. See
`examples/08-gsi-and-lsi/README.md` (cheat-sheet table).

### Q40. The three projection types — `KeysOnlyProjection()`, `IncludeProjection([attrs])`, `AllProjection()` — what does each project, and what is the trade-off?

**KeysOnly** projects only the index keys plus the main-table primary
key — smallest storage, cheapest writes. Reads against the index
return only keys, so for full rows you must follow up with
`Model.get()`. **Include([attrs])** projects keys plus a chosen
subset of attributes — pick the smallest projection that satisfies
your read pattern. **All** projects every attribute — reads are
self-sufficient, but the index uses as much storage as the table,
and every write to the row propagates to the index. Choose by
access pattern: smallest projection that lets you answer the query
without a follow-up `get()`. See
`examples/08-gsi-and-lsi/s02_gsi_projections.py` and
`examples/08-gsi-and-lsi/README.md`.

### Q41. If you query a `KeysOnly` GSI, the returned model instances appear to have most attributes set to `None`. Why?

The GSI physically stores only the projected attributes (here, just
the keys). Unprojected attributes do not exist on the index — when
pynamodb hydrates the result it sets them to `None`. To get the full
row, take the keys from the GSI result and follow up with
`Model.get(hash_key, range_key)` against the main table. That
follow-up `get()` is the price you pay for the cheaper KeysOnly
projection. See `examples/08-gsi-and-lsi/s02_gsi_projections.py`.

### Q42. GSI reads are eventually consistent, but LSI reads can be strongly consistent. Why this difference?

An LSI lives in the **same physical partition** as its main-table
row (because it shares the partition key) — DynamoDB updates the
row and its LSI entry together, so a strongly-consistent read can
serve from either. A GSI lives in **separate partitions** with its
own replication, and updates propagate asynchronously — a row
written to the main table appears in the GSI a moment later. That
asynchronous hop is what "eventually consistent" means. See
`examples/08-gsi-and-lsi/README.md`.

### Q43. Walk through how to declare a GSI on a pynamodb model.

Subclass `GlobalSecondaryIndex`, declare an inner `Meta` with
`index_name`, a `projection` (one of the three projection
classes), and optionally `read_capacity_units` /
`write_capacity_units`. Inside the subclass, declare the index's
hash/range key attributes (e.g.
`run_status = UnicodeAttribute(hash_key=True)`,
`start_ts = UTCDateTimeAttribute(range_key=True)`). Finally, attach
it as a class attribute on the Model. Querying becomes
`Model.<index_attr_name>.query(hash_key, ...)`. See
`examples/08-gsi-and-lsi/s01_gsi_basic.py:35-43` and
`examples/09-pipeline-metadata-demo/models.py`.

### Q44. In `s04_gsi_vs_scan.py` the same logical question is answered two ways with `ConsumedCapacity` printed for each. Why does the GSI win, and what does the script concretely print?

A `scan` reads every row in the table and applies the filter
client-side, so `ConsumedReadCapacityUnits` scales with table size.
A query against the `status-index` GSI jumps straight to the
partition for `run_status="FAILED"` and returns only matching
rows, so capacity scales with **result size**. The script uses
boto3 with `ReturnConsumedCapacity="TOTAL"` and prints both numbers
side by side, so you can see the GSI is dramatically cheaper for
the same logical answer. See
`examples/08-gsi-and-lsi/s04_gsi_vs_scan.py` and
`examples/09-pipeline-metadata-demo/s04_compare_capacity.py`.

### Q45. When is an LSI the right choice over a GSI?

When (1) you are querying **within a single partition** (same hash
key as the main table) on an alternate sort key — e.g. "top-N
transactions by amount on this card" — and (2) you need **strongly
consistent** reads on that secondary sort. If your access pattern
crosses partitions (e.g. "all FAILED runs across the platform")
or the read can tolerate ~milliseconds of lag, use a GSI instead.
Also remember that LSIs must be defined at table creation and can
never be added later. See `examples/08-gsi-and-lsi/s03_lsi_basic.py`.

---

## Category 10: Single-Table Design

### Q46. The 09 / 10 / 11 folders explicitly say "run scripts in numeric order". Why are they sequential while folders 00–08 are not?

Each script in 09/10/11 depends on the table state created by the
previous one — s01 sets up the table, s02 seeds data, s03 runs
queries against that data, and so on. They model real pipeline
stages. Making each one self-bootstrap would require duplicating
setup/seed logic everywhere and would defeat the purpose of
demonstrating staged behavior. Folders 00–08 each demonstrate one
isolated feature, so every script is self-contained and idempotent.
See `examples/README.md` (Folders section).

### Q47. In `examples/10-single-table-one-to-many`, one `Entity` model holds Customers, Cards, and Transactions. What two tricks make that work?

(1) An **`entity_type` discriminator** attribute (`"CUSTOMER"`,
`"CARD"`, `"TRANSACTION"`) tells the reader what kind of row each
result is. (2) **Every entity-specific attribute is `null=True`** —
`name`/`email` for customers, `holder_name`/`credit_limit` for cards,
`amount`/`merchant`/`tx_ts` for transactions — so a single row
carries only the fields relevant to its type. The shared keys
across all entity types are `pk` and `sk`. See
`examples/10-single-table-one-to-many/models.py`.

### Q48. Walk through the PK/SK pattern used in 10-single-table-one-to-many and what each query unlocks.

All rows for one customer share `PK = "CUSTOMER#<cust_id>"`. The SK
encodes the row's role: `"PROFILE"` for the customer record,
`"CARD#<card_id>"` for each card, `"TX#<card_id>#<ts>"` for each
transaction (note: the card_id is repeated inside the transaction's
SK). That gives three queries off one partition — full hierarchy
= `query("CUSTOMER#C001")`; cards only = `query("CUSTOMER#C001",
SK.begins_with("CARD#"))`; one card's transactions in time order =
`query("CUSTOMER#C001", SK.begins_with("TX#CD001#"))`. See
`examples/10-single-table-one-to-many/README.md` and `s02_query_patterns.py`.

### Q49. Why is a transaction's SK formed as `TX#<card_id>#<ts>` rather than just `TX#<ts>`?

With the card_id embedded in the SK prefix, transactions for one
card sit together in sort order, so
`SK.begins_with("TX#CD001#")` returns one card's transactions, and
`SK.between("TX#CD001#<start>", "TX#CD001#<end>")` returns one
card's transactions in a time window — both single-partition
queries on the main table. With just `TX#<ts>`, the card_id would
only be findable via a filter or a separate GSI. The composite SK
trades a longer string for a much more useful access pattern. See
`examples/10-single-table-one-to-many/s03_query_card_transactions_by_date.py`.

### Q50. Folder 11 shows three ways to model Customer↔Merchant many-to-many. Compare adjacency list and inverted GSI on write cost and consistency.

**Adjacency list** (s01) writes both edges:
`PK=CUSTOMER#C SK=MERCHANT#M` and `PK=MERCHANT#M SK=CUSTOMER#C`. That
is 2× write cost per relationship, but both directions are
main-table queries (strongly consistent, no GSI lag). The two
writes must be wrapped in `TransactWrite` so the pair stays atomic.
**Inverted GSI** (s02) writes one edge plus an index that swaps
PK/SK — 1× write cost, but the reverse direction goes through the
GSI and is eventually consistent. Pick adjacency when reverse-lookup
must be strongly consistent or write volume is moderate; pick
inverted GSI when writes are heavy and a small consistency lag on
the reverse side is acceptable. See
`examples/11-single-table-many-to-many/s01_adjacency_list.py:67-74`
and `s02_gsi_inversion.py`.
