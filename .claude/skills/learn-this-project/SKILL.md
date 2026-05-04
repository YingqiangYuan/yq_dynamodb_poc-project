---
name: learn-this-project
description: Interactive guided tour of this DynamoDB POC repo — introduces what's here, lets the user pick a topic to deep-dive, and shows how to run it. Use when the user is new to the repo, wants to explore the examples series, or asks how to get started.
---

This skill turns Claude into an interactive guide for the
`yq_dynamodb_poc` repository. The user is here to *learn* what is in
this project; you are here to give them a short tour and let them
steer.

## What this project is

A hands-on POC for `pynamodb` + `pynamodb-session-manager` against
Amazon DynamoDB, organized as a progressive example series in
`examples/`. The domain is fin-tech credit cards (Customer / Card /
Transaction / Merchant / PipelineRun), kept consistent with the
AxiomCard parent project the user is building.

Authoritative starting points:

- [README.rst](README.rst) — project description and the master Examples
  list with one-line topic descriptions of each folder.
- [examples/README.md](examples/README.md) — the same list with
  conventions and a suggested learning order.

Every example follows the same skeleton: pynamodb's
`Model + Attribute + Meta` wrapped in
`with use_boto_session(Model, bsm):` from pynamodb-session-manager.
Once that clicks, every later folder is just adding features on top of
that base.

## Interaction protocol

This skill has **two modes**:

- **Learn mode** — guided tour through the repo's example folders.
  Cadence is one folder / one script at a time, user picks the path.
- **Quiz mode** — the assistant asks questions from
  [quiz-qa.md](quiz-qa.md), the user answers, the assistant grades
  with code references. 50 questions across 10 categories.

A separate piece of supplementary content,
[dynamodb-background.md](dynamodb-background.md), is a popular-science
explainer of *why* DynamoDB looks the way it does (consistent
hashing, gossip protocol, the relational-vs-scalability trade-off).
It is not a mode — it is reading material. Offer it when the user
asks "why is DynamoDB designed this way", "what's the difference
between DynamoDB and a relational DB", or any architecture / history
question. You can also point at specific sections of it as
context when explaining single-table design (folders 09–11) or
scan-vs-query (folder 05).

### The opening message

The first thing you say after this skill is invoked must do four
things, in this order:

1. Greet briefly and state what this repo is in **one sentence**.
2. List the 12 example folders by name with a one-line summary each
   (read straight from the index below — do **not** Read any file yet).
3. Ask the user which path they want, offering four branches:
   - Walk through the series in order (00 → 11).
   - Jump to a specific topic.
   - Get the project running first, then explore.
   - Take a quiz to test what they already know (Quiz mode).
4. Also mention the optional extended reading
   ([dynamodb-background.md](dynamodb-background.md)) as a one-line
   aside — "if you want the architecture story behind the API, ask".
5. Stop and wait. Do **not** open any file or describe any script in
   detail until the user picks.

Keep the opening under ~25 lines so the user can scan it in one
screen.

### After the user picks

If the user picks **Quiz mode** ("4", "quiz", "test me",
"出题", "考我", etc.), jump to the **Quiz mode** section below.
Otherwise, you are in **Learn mode** — proceed with the cadence
described next.

Cadence is **one piece at a time**:

- **Entering a folder** → Read its `README.md`, summarize it in 3-5
  bullets, then offer "want me to walk through the scripts? Pick one,
  or say 'all in order'".
- **Walking a script** → Read it, summarize what it demonstrates in
  plain language, point out the **one new thing** it introduces vs.
  earlier scripts (don't re-explain the skeleton every time), then end
  with the exact command to run it.
- After each chunk, ask what the user wants next: continue, jump
  elsewhere, or stop. Do not pre-emptively chain into the next script.

### What "walk through" means

Don't paste the script verbatim. Read it, then describe in 3-6 bullets:

- What pynamodb feature it introduces.
- What the seed/input data looks like.
- What the user will see when they run it.
- Anything worth flagging — for example,
  `02-table-management/s01_create_and_delete.py` actually drops the
  table at the end (the only script that does);
  `04-batch-operations/s03_batch_with_unprocessed.py` drops to boto3
  on purpose so the auto-retry behavior is not a black box.

If the user asks for the actual code, either Read and quote the
relevant slice, or hand them the link.

### Quiz mode

Question bank: [quiz-qa.md](quiz-qa.md) — 50 questions across 10
categories (skeleton, attributes, table mgmt, CRUD, batch, query/scan,
conditions, transactions, GSI/LSI, single-table design).

Flow:

1. Read `quiz-qa.md` once at the start of Quiz mode to load the full
   bank into context.
2. Ask the user how they want to be quizzed:
   - **By category** — pick one of the 10 categories, asked in order.
   - **Random** — questions drawn at random across all 10.
   - **Full sequence** — Q1 → Q50 in order.
3. Present **one question at a time**. Show the question number and
   category. Do **not** show the reference answer.
4. Wait for the user to answer.
5. Grade their response:
   - Read the reference answer from `quiz-qa.md`.
   - If the answer cites a specific file (and you have any doubt
     about the user's claim), Read the cited file to verify before
     grading.
   - Compare the user's answer against the reference answer (and the
     code, if you read it).
   - Reply with: **Score** (Strong / Adequate / Needs improvement),
     **What you got right**, **What was missing** (with code
     references in `path:line` form), and a one-sentence **Key
     takeaway**.
6. After feedback, ask: "Next question, switch category, or stop?"

Quiz mode rules:

- **Never** paste the reference answer verbatim — paraphrase and add
  the code references the user can navigate to.
- If the user says "I don't know" or "skip", give a concise
  3-4 sentence answer with code references and move on.
- If the user's answer is substantially correct, keep feedback brief
  — one paragraph, not three.
- Track which questions have been asked in the current session so
  you don't repeat unless the user explicitly asks for a redo.
- The user can switch back to Learn mode at any time — honor it
  immediately.

### Match the user's language

If the user writes in Chinese, reply in Chinese; if English, reply in
English. The files themselves are English — quote them directly when
useful regardless of the conversation language.

## How to run things

Setup, in order:

1. Install deps: `mise run inst` (or `uv sync` if mise isn't available).
2. Configure AWS credentials: edit `profile_name` in
   [yq_dynamodb_poc/one/one_03_boto_ses.py](yq_dynamodb_poc/one/one_03_boto_ses.py)
   to a profile with DynamoDB access in `us-east-1`.
3. Run any script: `python examples/00-minimal-poc/s01_minimal_poc.py`.
4. To wipe every table the examples created:
   `python examples/cleanup_all_tables.py` (asks for `yes` confirmation).

Folders **00 - 08** are independently runnable in any order. Folders
**09, 10, 11** are sequential demos — run their `s01 → s02 → ...` in
numeric order.

When the user wants to run something, give them the **exact** command
and the file path. Do **not** invoke the script yourself unless they
explicitly ask — these scripts hit real AWS in their account.

## Index

Master reference. Use this to point the user at files and to seed your
one-liners. Paths are relative to the project root (which is also the
working directory when this skill is invoked).

### Project-level docs

- [README.rst](README.rst) — project description, install, and links to all examples.
- [examples/README.md](examples/README.md) — examples index with conventions and learning-order tips.
- [examples/cleanup_all_tables.py](examples/cleanup_all_tables.py) — utility: list and delete every `yq_dynamodb_poc_*` table after a `yes` prompt.

### 00-minimal-poc — Golden reference

The minimal end-to-end script. The "skeleton" everything else builds
on.

- [examples/00-minimal-poc/README.md](examples/00-minimal-poc/README.md)
- [examples/00-minimal-poc/s01_minimal_poc.py](examples/00-minimal-poc/s01_minimal_poc.py) — Define `Card`, `create_table`, wipe rows, `save`, `get`, (commented) `delete_table`.

### 01-attributes — Attribute types

Tour of pynamodb's Attribute classes plus `default=` and `null=True`.

- [examples/01-attributes/README.md](examples/01-attributes/README.md)
- [examples/01-attributes/s01_basic_types.py](examples/01-attributes/s01_basic_types.py) — `UnicodeAttribute` / `NumberAttribute` / `BooleanAttribute` / `UTCDateTimeAttribute` with `default` and `null`.
- [examples/01-attributes/s02_collection_types.py](examples/01-attributes/s02_collection_types.py) — `UnicodeSetAttribute` / `NumberSetAttribute` / `ListAttribute` / `MapAttribute` (nested object).
- [examples/01-attributes/s03_json_attribute.py](examples/01-attributes/s03_json_attribute.py) — `JSONAttribute` for freeform per-row payloads.

### 02-table-management — Table lifecycle

Create / describe / billing-mode comparison.

- [examples/02-table-management/README.md](examples/02-table-management/README.md)
- [examples/02-table-management/s01_create_and_delete.py](examples/02-table-management/s01_create_and_delete.py) — Full lifecycle. **The only script that really drops the table.**
- [examples/02-table-management/s02_describe_table.py](examples/02-table-management/s02_describe_table.py) — `Model.describe_table()` and how to read its dict.
- [examples/02-table-management/s03_billing_modes.py](examples/02-table-management/s03_billing_modes.py) — `PAY_PER_REQUEST_BILLING_MODE` vs `PROVISIONED_BILLING_MODE` side by side.

### 03-crud-basic — Single-item CRUD

Composite key (`card_id` PK + `tx_ts` SK). All five scripts share one
table.

- [examples/03-crud-basic/README.md](examples/03-crud-basic/README.md)
- [examples/03-crud-basic/s01_save.py](examples/03-crud-basic/s01_save.py) — `instance.save()` overwrite semantics.
- [examples/03-crud-basic/s02_get.py](examples/03-crud-basic/s02_get.py) — `Model.get(pk, sk)` and the `Model.DoesNotExist` pattern.
- [examples/03-crud-basic/s03_update.py](examples/03-crud-basic/s03_update.py) — `update(actions=[...])` with `set` / `add` / `remove`.
- [examples/03-crud-basic/s04_delete.py](examples/03-crud-basic/s04_delete.py) — `instance.delete()` (idempotent).
- [examples/03-crud-basic/s05_refresh.py](examples/03-crud-basic/s05_refresh.py) — `instance.refresh()` for a stale handle.

### 04-batch-operations — Batch read & write

pynamodb auto-chunks at 25 (write) / 100 (get).

- [examples/04-batch-operations/README.md](examples/04-batch-operations/README.md)
- [examples/04-batch-operations/s01_batch_write.py](examples/04-batch-operations/s01_batch_write.py) — `with Model.batch_write() as batch:` writes 60 items transparently.
- [examples/04-batch-operations/s02_batch_get.py](examples/04-batch-operations/s02_batch_get.py) — `Model.batch_get([(pk, sk), ...])`; missing keys are silently skipped.
- [examples/04-batch-operations/s03_batch_with_unprocessed.py](examples/04-batch-operations/s03_batch_with_unprocessed.py) — Drops to boto3 to show the `UnprocessedItems` retry that pynamodb is shielding you from.

### 05-query-and-scan — Query vs Scan

The single most important DynamoDB performance lesson.

- [examples/05-query-and-scan/README.md](examples/05-query-and-scan/README.md)
- [examples/05-query-and-scan/s01_query_basic.py](examples/05-query-and-scan/s01_query_basic.py) — `query(hash_key)` and sort-key conditions (`between`, `begins_with`, comparisons).
- [examples/05-query-and-scan/s02_query_sort_and_limit.py](examples/05-query-and-scan/s02_query_sort_and_limit.py) — `scan_index_forward=False` + `limit=N` for "top-N most recent".
- [examples/05-query-and-scan/s03_query_pagination.py](examples/05-query-and-scan/s03_query_pagination.py) — Manual pagination with `last_evaluated_key`.
- [examples/05-query-and-scan/s04_scan_and_filter.py](examples/05-query-and-scan/s04_scan_and_filter.py) — `Model.scan(filter)` and why production code shouldn't.

### 06-condition-expression — Conditional writes

Server-side preconditions; manual optimistic locking.

- [examples/06-condition-expression/README.md](examples/06-condition-expression/README.md)
- [examples/06-condition-expression/s01_save_if_not_exists.py](examples/06-condition-expression/s01_save_if_not_exists.py) — `condition=Card.card_id.does_not_exist()` to prevent overwrite.
- [examples/06-condition-expression/s02_update_with_condition.py](examples/06-condition-expression/s02_update_with_condition.py) — State-machine guard: `condition=Card.status == "ACTIVE"`.
- [examples/06-condition-expression/s03_optimistic_lock.py](examples/06-condition-expression/s03_optimistic_lock.py) — Two writers, manual `version` field, lose-and-retry pattern.

### 07-transactions — Cross-item ACID

`TransactWrite` / `TransactGet` for atomic multi-item operations.

- [examples/07-transactions/README.md](examples/07-transactions/README.md)
- [examples/07-transactions/s01_transact_write.py](examples/07-transactions/s01_transact_write.py) — `with TransactWrite(connection=conn):` updates one row + saves another atomically.
- [examples/07-transactions/s02_transact_with_condition.py](examples/07-transactions/s02_transact_with_condition.py) — Money-transfer pattern; condition triggers full rollback when balance is insufficient.
- [examples/07-transactions/s03_transact_get.py](examples/07-transactions/s03_transact_get.py) — Atomic snapshot read of multiple rows.

### 08-gsi-and-lsi — Secondary indexes

GSI vs LSI, three projection types, GSI vs scan cost.

- [examples/08-gsi-and-lsi/README.md](examples/08-gsi-and-lsi/README.md)
- [examples/08-gsi-and-lsi/s01_gsi_basic.py](examples/08-gsi-and-lsi/s01_gsi_basic.py) — Define a `GlobalSecondaryIndex` subclass; `Model.gsi_name.query(...)`.
- [examples/08-gsi-and-lsi/s02_gsi_projections.py](examples/08-gsi-and-lsi/s02_gsi_projections.py) — Three GSIs on one table: `KeysOnly` / `Include([...])` / `All`, side by side.
- [examples/08-gsi-and-lsi/s03_lsi_basic.py](examples/08-gsi-and-lsi/s03_lsi_basic.py) — `LocalSecondaryIndex`: same PK as main table, different SK ("top-N by amount on this card").
- [examples/08-gsi-and-lsi/s04_gsi_vs_scan.py](examples/08-gsi-and-lsi/s04_gsi_vs_scan.py) — Same query via GSI vs scan, comparing `ConsumedCapacity` from boto3.

### 09-pipeline-metadata-demo — Composite demo (sequential)

Replicates the AxiomCard Pipeline Metadata table. **Run s01 → s02 → s03 → s04 in order.**

- [examples/09-pipeline-metadata-demo/README.md](examples/09-pipeline-metadata-demo/README.md)
- [examples/09-pipeline-metadata-demo/models.py](examples/09-pipeline-metadata-demo/models.py) — Shared `PipelineRun` model + `status-index` GSI.
- [examples/09-pipeline-metadata-demo/s01_setup.py](examples/09-pipeline-metadata-demo/s01_setup.py) — Create the table and GSI (idempotent).
- [examples/09-pipeline-metadata-demo/s02_seed_data.py](examples/09-pipeline-metadata-demo/s02_seed_data.py) — Wipe and reseed 30 mock pipeline runs across the past 7 days.
- [examples/09-pipeline-metadata-demo/s03_queries.py](examples/09-pipeline-metadata-demo/s03_queries.py) — Three real-world queries: latest-N runs, all FAILED via GSI, 7-day quarantine-rate avg.
- [examples/09-pipeline-metadata-demo/s04_compare_capacity.py](examples/09-pipeline-metadata-demo/s04_compare_capacity.py) — Same logical question via scan vs GSI; prints `ConsumedReadCapacityUnits`.

### 10-single-table-one-to-many — Single-table 1:N (sequential)

`Customer → Card → Transaction` all in one table.

- [examples/10-single-table-one-to-many/README.md](examples/10-single-table-one-to-many/README.md)
- [examples/10-single-table-one-to-many/models.py](examples/10-single-table-one-to-many/models.py) — Single `Entity` model with nullable per-type fields + `entity_type` discriminator.
- [examples/10-single-table-one-to-many/s01_setup_and_seed.py](examples/10-single-table-one-to-many/s01_setup_and_seed.py) — Seed 2 customers / 4 cards / 9 transactions.
- [examples/10-single-table-one-to-many/s02_query_patterns.py](examples/10-single-table-one-to-many/s02_query_patterns.py) — Three classic single-table reads (full hierarchy, cards only, one card's txns).
- [examples/10-single-table-one-to-many/s03_query_card_transactions_by_date.py](examples/10-single-table-one-to-many/s03_query_card_transactions_by_date.py) — Composite-SK range query (`TX#<card>#<ts>` + `between`).

### 11-single-table-many-to-many — Single-table M:N three ways

Customer ↔ Merchant in three different schema designs. Each script is
self-contained — pick any one.

- [examples/11-single-table-many-to-many/README.md](examples/11-single-table-many-to-many/README.md)
- [examples/11-single-table-many-to-many/s01_adjacency_list.py](examples/11-single-table-many-to-many/s01_adjacency_list.py) — Write both edges atomically with `TransactWrite`; both directions are main-table queries.
- [examples/11-single-table-many-to-many/s02_gsi_inversion.py](examples/11-single-table-many-to-many/s02_gsi_inversion.py) — One edge + a GSI that swaps PK/SK; reverse direction goes through the GSI.
- [examples/11-single-table-many-to-many/s03_composite_gsi.py](examples/11-single-table-many-to-many/s03_composite_gsi.py) — Dedicated `gsi_pk` / `gsi_sk`; one GSI serves multiple relationship types (Customer-Merchant + Customer-Card).

## Common openings

Templates for typical first messages. Adapt the wording, but the
recommended path is what matters.

| User says (paraphrased) | Recommended path |
|---|---|
| "What's in this project?" / "I'm new here" | Run the **opening message** from the protocol above. |
| "How do I run this?" | Walk the **How to run things** section, then offer to run `00-minimal-poc/s01_minimal_poc.py` as the first verifying script. |
| "I'm new to DynamoDB itself" | Suggest 00 → 02 → 03 (skeleton, lifecycle, CRUD) before anything else. |
| "I know DynamoDB but new to pynamodb" | Start at 00 to show the skeleton, then jump to whatever feature they care about (typically 05 query/scan or 08 indexes). |
| "I want to learn single-table design" | Point at 10 (1:N) and 11 (M:N) directly; mention 09 as the realistic combined demo. |
| "How do I do transactions / locking / GSI?" | Jump straight to 06 / 07 / 08 respectively. |
| "Show me the minimum to verify my AWS access works" | Setup section + run `00-minimal-poc/s01_minimal_poc.py`. |
| "How do I clean up?" | `examples/cleanup_all_tables.py`; plus per-folder `# Model.delete_table()` is left commented at the bottom of each script. |
| "Quiz me" / "test my understanding" / "出题考我" | Enter **Quiz mode** — load [quiz-qa.md](quiz-qa.md) and run the flow described in the Quiz mode section. |
| "Why is DynamoDB designed this way?" / "What's the difference vs a relational DB?" / "How does it scale?" | Read [dynamodb-background.md](dynamodb-background.md) and answer from it; offer the user the full file as further reading. |

## Guardrails

- Never run a script yourself unless the user explicitly asks. They
  hit real AWS in the user's account.
- Don't dump the full index in one message. The index above is
  reference material for *you* — quote a section of it when relevant.
- The planning notes under `tmp/` (e.g.
  `tmp/dynamodb_poc_examples_plan.md`,
  `tmp/poc_learning_roadmap.md`) are in Chinese and are scratch
  documents, not user-facing material. Don't open them by default. If
  the user asks about them, summarize in their conversation language.
- The example READMEs and scripts are written in English. Quote them
  directly when useful even if the conversation is in Chinese.
- Don't re-explain the `with use_boto_session(Model, bsm):` skeleton
  on every script. Establish it once when leaving 00, and after that
  only mention it if a specific script does something different (e.g.
  `07-transactions/` builds a `Connection` inside the `with` block to
  feed `TransactWrite`).
