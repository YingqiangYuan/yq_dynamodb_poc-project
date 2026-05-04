# DynamoDB Background — A Cloud-Native Database

This is **extended reading**. The example folders teach you how to
*use* DynamoDB through pynamodb. This file zooms out and asks the
question those examples take for granted: **why does DynamoDB look
the way it does?** Why are there no `JOIN`s? Why do you have to
think about partition keys before writing a single line of code?
Why is "always design for your access patterns first" the mantra
every DynamoDB tutorial repeats?

The short answer: DynamoDB is what you get when you optimize a
database for **horizontal scale and predictable latency at any
size**, and accept the trade-offs that come with that goal. The long
answer is the rest of this document.

It is written for someone who is comfortable with relational
databases (Postgres, MySQL) but new to NoSQL / cloud-native
databases. No prior knowledge of distributed systems is assumed.

---

## 1. The world before DynamoDB

In a traditional relational database, your data lives on **one
machine**. You have one Postgres server with one CPU, one disk, one
memory pool. The table sits on that disk; queries run on that CPU.

When traffic grows, you scale the machine: bigger CPU, more RAM,
faster disk. This is **vertical scaling**, sometimes called
"scaling up". It works — until it doesn't:

- The biggest single machine you can buy is not infinitely big.
- Doubling the machine size does not double its price; the curve
  bends sharply upward at the high end.
- A single machine is a single point of failure.

The relational answer to that wall is **sharding**: split your big
table into chunks, put each chunk on a different machine, and have
the application route queries to the right shard. This works in
principle. In practice, sharding hurts in three places:

1. **Cross-shard queries become hard.** A query like "all orders
   placed by users from California" might touch every shard. JOINs
   across shards are the nightmare every DBA tells war stories
   about.
2. **Rebalancing is painful.** Adding a new shard means re-homing
   data — moving rows from existing shards to the new one. While
   that happens, performance degrades and you have to be careful
   about consistency.
3. **The application has to know about sharding.** "Which shard
   has user 12345?" becomes a question your code has to answer.

For Amazon in the early 2000s, this was not theoretical. The
shopping-cart service powering amazon.com had outgrown what a
single-machine relational DB could serve, and the team had felt the
sharding pain in production. There is a famous story about
shopping-cart outages during peak holiday traffic — the kind of
incident that makes a company rethink its database strategy.

In 2007, Amazon researchers published a paper titled **"Dynamo:
Amazon's Highly Available Key-value Store"**. It described the
internal system Amazon had built to power the cart and other
services that needed high availability at scale. The paper became
hugely influential — Cassandra, Riak, and Voldemort all trace their
lineage to it. In 2012, AWS launched **DynamoDB** as a managed
cloud service descended from those ideas.

So when you use DynamoDB today, you are using a database whose
design goals are:

- Scale **horizontally**, not vertically. Add machines, not bigger
  machines.
- Stay **available** even when individual machines fail.
- Deliver **predictable latency** — single-digit milliseconds —
  regardless of how big the table grows.

The price for that is the rest of this document.

---

## 2. How does DynamoDB scale? Two big ideas.

DynamoDB's scaling story rests on two distributed-systems
techniques: **consistent hashing** for data placement, and **gossip
protocols** for cluster coordination. Neither was invented for
DynamoDB, but the Dynamo paper is what made them famous in the
database world.

### 2.1 Consistent hashing — where does my row live?

Imagine you have 100 storage nodes and 1 billion rows. Two
questions: how do you decide which node stores which row, and what
happens when you add a 101st node?

**Naive approach.** Hash the row's primary key, then use modulo:
`node_index = hash(key) % 100`. Easy. But the moment you add a
101st node, the divisor changes from 100 to 101, and **almost
every key now maps to a different node**. You have to physically
move ~99% of your data. That is unacceptable at scale.

**Consistent hashing.** Instead of computing `hash % N`, you arrange
the hash space (think of a clock face going 0 → 2³² → 0) into a
**ring**. Each node "owns" a contiguous arc of the ring. To find
where a row lives, hash its key and walk clockwise around the ring
until you hit a node — that node owns the row.

```
                  Node A
                   /
                  /  arc owned by A
                 /
   arc owned ___/
   by D  \      \
          \      \
           \      \
            Node D \
             \     Node B
              \    /
               \  /
                \/
                /\
               /  \
              /    arc owned by B
             /
         Node C
```

When you **add** a new node, it slots into one place on the ring
and takes over only the arc that was previously owned by its
clockwise neighbor. Only that one slice of data moves. Adding a
node touches roughly `1/N` of your data, not all of it.

When a node **dies**, its arc collapses into its clockwise
neighbor — same property in reverse: only that arc's worth of
ownership shifts.

To balance load (real machines have wildly different capacities,
or some arcs would otherwise be much bigger than others), each
physical node is mapped to **many virtual positions** on the ring
("virtual nodes" or "vnodes"). That smooths out the arc sizes.

**Replication** comes for free with this scheme. If you want each
row stored on `K` machines for durability, you just take the next
`K` nodes clockwise from where the hash lands, and replicate to all
of them. Same lookup procedure, three writes instead of one.

This is the mechanism that lets DynamoDB say "we'll handle 10
items or 10 trillion items, you don't have to think about it" —
because adding capacity is a small, local operation, not a
cluster-wide reshuffle.

### 2.2 Gossip — how does the cluster agree on who's alive?

Now that data is spread across hundreds or thousands of nodes, a
new question arises: **how does each node know the cluster's
current shape?** Who is alive, who is dead, who owns which arc?

The naive answer is "have a coordinator" — one master node that
holds the truth and tells everyone else. But a single coordinator
is a single point of failure, exactly the thing this design is
trying to avoid.

The Dynamo answer is the **gossip protocol** (sometimes called
"epidemic protocol"). Every second or so, each node picks a few
random peers and exchanges what it knows: which nodes I have seen
recently, which I think are dead, what version of the cluster
membership I am holding. Information spreads like a rumor at a
party — not instantly, but exponentially fast, and without any
central authority.

A few properties make gossip a good fit:

- **No single point of failure.** Every node is symmetric.
- **Self-healing.** A node that comes back from a network blip
  catches up with reality after a few rounds of gossip.
- **Scales gracefully.** Each node only talks to a small constant
  number of peers each round, regardless of cluster size.

The trade-off is that gossip is **eventually consistent**: at any
instant, two different nodes may have slightly different views of
the cluster. That's acceptable here — the cluster's shape changes
rarely, so the lag of a few seconds rarely matters.

Membership and failure detection are gossiped. Combined with
consistent hashing, this is the backbone that lets DynamoDB
expand and contract its node count without operators getting
involved and without the application noticing.

---

## 3. The trade-off: relational expressiveness for unbounded scale

Now we get to the painful part. Consistent hashing scales
beautifully — but it imposes a constraint that ripples through
everything else in the database: **a row's location is determined
entirely by its primary key**.

That has consequences:

### 3.1 No JOINs

A `JOIN` between two tables typically requires reading rows from
both tables and matching them on a foreign key. In a single-machine
relational DB, that is straightforward. In a sharded system where
the rows you need might be on completely different nodes, a JOIN
turns into a fan-out scatter-gather across the entire cluster —
exactly the latency-killing pattern Dynamo is designed to avoid.

DynamoDB's answer is: **don't.** There is no `JOIN` operator. If
you need data from two entities together, you put them in the
**same partition** by design (this is what "single-table design"
in folders 10 and 11 is doing) so a single query returns the lot.

### 3.2 No ad-hoc queries on non-key columns

In relational DBs you can write "give me all users where
`signup_date > 2024-01-01 AND country = 'US'`" against any
indexed column at any time. In DynamoDB, the only fast way to
find a row is **by its primary key** (or by a secondary index you
explicitly built).

If you want to answer "all FAILED pipeline runs across the
platform", you must have built a GSI on `run_status` ahead of
time (this is what
`examples/09-pipeline-metadata-demo/models.py` does). A scan with
a filter is technically possible — and `examples/05-query-and-scan/s04_scan_and_filter.py`
demonstrates it — but it reads every row in the table to find the
matches, so it is fine for an admin script and a disaster in a
hot path.

This is why **access patterns come first** in DynamoDB schema
design. You enumerate every query your application needs, then
pick keys and indexes that serve those queries efficiently. With
a relational DB you start from the data; with DynamoDB you start
from the queries.

### 3.3 Multi-row transactions are limited

Cross-row ACID transactions exist (folder 07's `TransactWrite` /
`TransactGet`), but they are bounded — up to 100 items per
transaction, ~4 MB total, ~2× the cost of the underlying
operations. They are designed for invariants that span a small
number of rows (a money transfer, an order plus its line items),
not for "this entire workflow needs to be atomic".

### 3.4 The schema is dynamic, not declared

A DynamoDB table only declares its **key schema** (PK, SK,
indexes). The other attributes are per-row. Two rows in the
same table can have entirely different sets of attributes — and
single-table design **relies** on that flexibility (folder 10's
`Entity` model is one Python class for Customers, Cards, and
Transactions). What you gain in flexibility, you lose in
schema-enforced data integrity; you have to validate at the
application layer.

### 3.5 What you get in exchange

For workloads that fit, the compensations are large:

- **Linear horizontal scale.** From a few KB to petabytes,
  same code, no operator action.
- **Predictable latency.** Single-digit milliseconds, regardless
  of table size.
- **Zero capacity planning if you want it.** On-demand billing
  (`PAY_PER_REQUEST_BILLING_MODE`, the default in every example
  in this repo) auto-scales, charges per request, and pays
  nothing when idle.
- **No replicas to babysit.** Replication is built in;
  consistency is configurable per read.
- **No sharding logic in your application.** The library just
  asks "give me the row at this key", and consistent hashing
  finds it.

For high-traffic, key-driven user-facing applications — shopping
carts, gaming leaderboards, session stores, IoT telemetry,
fin-tech transaction logs — that bargain is excellent. For
analytics, ad-hoc reporting, or rich domain queries with many
JOINs — it's the wrong tool.

---

## 4. What this means for schema design (and for this repo)

The trade-off above is why every chapter of every DynamoDB book
hammers two principles:

1. **Enumerate access patterns first.** Before drawing any
   schema, list every query your application will make. "Get
   user by id." "List user's last 10 orders." "Show all FAILED
   pipeline runs in the past 7 days." Each one becomes a
   constraint on your key design.

2. **Single-table design.** Where a relational DB would have
   `customers`, `cards`, `transactions` as three tables joined
   by foreign keys, DynamoDB often puts them all in **one**
   table, with carefully chosen PK/SK encodings so that one
   query answers a whole hierarchy of questions.

That is exactly what folders 09, 10, and 11 in this repo
demonstrate:

- **`09-pipeline-metadata-demo`** — a real-world composite demo
  modelled on the AxiomCard pipeline metadata table, showing PK
  + SK choices and a GSI for cross-partition queries
  (`status-index`).
- **`10-single-table-one-to-many`** — Customer → Card →
  Transaction in one table, one `Entity` model with an
  `entity_type` discriminator, composite SK pattern
  `TX#<card_id>#<ts>` so card-scoped time-range queries are
  cheap.
- **`11-single-table-many-to-many`** — three approaches to
  Customer ↔ Merchant relationships, each making a different
  trade-off between write cost and read consistency.

Read those folders not as "how do I use pynamodb" but as "how do
I reason about access patterns and turn them into keys".

---

## 5. Where DynamoDB sits in the modern landscape

A short field guide so you know when to reach for it and when to
reach for something else:

| Category | Examples | Strength |
|---|---|---|
| Cloud-native NoSQL (key/document) | **DynamoDB**, Cosmos DB, Cassandra, ScyllaDB | Massive scale, predictable latency, key-based access |
| Managed relational | RDS (Postgres/MySQL), Aurora, CloudSQL | Rich queries, JOINs, mature tooling, transactions |
| Document DBs | MongoDB, DocumentDB, Firestore | Flexible schemas, nested documents, moderate scale |
| Analytics / OLAP | Redshift, BigQuery, Snowflake | Complex aggregations over huge fact tables |
| In-memory | Redis, ElastiCache | Sub-ms latency, smaller data, ephemeral |

**Cassandra** and **ScyllaDB** are the open-source descendants of
the Dynamo paper — same consistent-hashing + gossip core, but
self-hosted instead of managed. If you have read about Cassandra,
most of the mental model transfers directly to DynamoDB, with
DynamoDB trading some of Cassandra's tunability for AWS
operational simplicity.

**RDS / Aurora / Postgres** is the right answer when you need
JOINs, ad-hoc reporting, complex transactions across many rows,
or schema-enforced integrity. Many real systems use **both**: a
DynamoDB table for the hot, key-driven write/read path, and a
relational warehouse for analytics and reporting.

---

## 6. Tying it back to the example scripts

Every example folder in this repo is a small concrete consequence
of the trade-offs described above:

- **00 / 01 / 02** — The skeleton: Model + Attribute + Meta. The
  on-demand billing default exists because consistent-hashing-driven
  scale makes it possible.
- **03 / 04** — `save` / `get` / `update` / `batch_write` /
  `batch_get`. All key-based. There is no "give me all rows where
  …" because the scaling model would not allow it.
- **05** — `query` vs `scan`. The whole reason to memorize the
  difference is that a scan ignores the consistent-hashing
  partitioning and pays for it.
- **06 / 07** — Conditional writes and transactions. Server-side
  preconditions and bounded multi-row ACID — the tools for
  invariants that key-based access alone cannot enforce.
- **08** — GSI / LSI. The escape hatch for non-key access
  patterns: declare a secondary index up front so the same
  consistent-hashing trick works for a different key.
- **09 / 10 / 11** — Schema design driven by access patterns.
  Single-table design is what you arrive at when you take the
  "no JOINs, key-based access only" constraint seriously.

Once the architecture clicks, the API stops looking like an
arbitrary set of methods and starts looking like a direct
projection of the design goals. That is the goal of this
document — not to make you a distributed-systems expert, but to
give you the *why* behind the *what*.

---

## Further reading

- **The Dynamo paper (2007)** — "Dynamo: Amazon's Highly
  Available Key-value Store" by DeCandia et al. The original.
  Worth reading at least once for the historical context, even
  if some details have evolved in the managed DynamoDB service.
- **The DynamoDB Book** by Alex DeBrie — the canonical
  practitioner's guide to access-pattern-driven schema design.
- **AWS DynamoDB Developer Guide** — official docs; the sections
  on partition keys, secondary indexes, and best practices map
  directly onto the topics covered above.
