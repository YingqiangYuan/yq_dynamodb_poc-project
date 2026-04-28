# 09-pipeline-metadata-demo — Composite demo

Replicates the **Pipeline Metadata Table** from the AxiomCard parent
project's roadmap. Validates the three real-world query patterns the
data platform needs to support, and shows the GSI-vs-scan cost story
on realistic data.

## Run order (mandatory)

These scripts share state. Run them in order:

```bash
python examples/09-pipeline-metadata-demo/s01_setup.py
python examples/09-pipeline-metadata-demo/s02_seed_data.py
python examples/09-pipeline-metadata-demo/s03_queries.py
python examples/09-pipeline-metadata-demo/s04_compare_capacity.py
```

## Files

- `models.py` — `PipelineRun` model (PK = `pipeline_name`, SK = `run_id`) plus a `status-index` GSI (PK = `run_status`, SK = `start_ts`).
- `s01_setup.py`            — create the table and its GSI; idempotent (skips if it already exists).
- `s02_seed_data.py`        — wipe and reseed 30 mock pipeline runs across three pipelines (`txn-b2s`, `credit-b2s`, `billing-b2s`), mixed status (SUCCESS / FAILED / PARTIAL), spread over the past 7 days.
- `s03_queries.py`          — runs the three query patterns the roadmap requires.
- `s04_compare_capacity.py` — same logical "all FAILED runs" question via scan vs GSI, prints `ConsumedReadCapacityUnits`.

## Query patterns demonstrated in `s03_queries.py`

1. **Latest 10 runs of a given pipeline.** Uses the main table
   (`pipeline_name` PK, `run_id` SK descending, `limit=10`).
2. **All FAILED runs across the platform.** Uses the `status-index` GSI
   (PK = `run_status="FAILED"`).
3. **7-day average quarantine rate for a pipeline.** Uses the main
   table (PK = pipeline) plus client-side aggregation in Python.

## Pipeline run schema

| Attribute | Purpose |
|---|---|
| `pipeline_name` (PK)      | Logical pipeline name, e.g. `txn-b2s` |
| `run_id` (SK)             | `<isoformat>-<uuid8>` — sortable by start time |
| `run_status`              | `SUCCESS` / `FAILED` / `PARTIAL` |
| `start_ts` / `end_ts`     | Run wall-clock window |
| `records_processed`       | Rows ingested by the run |
| `quarantine_count`        | Rows that failed validation |
| `s3_path`                 | Where the silver-layer Delta table was written |
| `delta_version`           | Delta Lake commit version produced by the run |
