# artifacts

Indexes into the raw, canonical and summary artifacts that live inside each experiment's `historical_package/` (not duplicated here):

- [`raw/`](raw/README.md) — raw provider outputs and attempt logs (`raw_artifact_index.csv`)
- [`canonical/`](canonical/README.md) — cleaned/canonical result files (`canonical_artifact_index.csv`)
- [`summaries/`](summaries/README.md) — archived analysis outputs, tables and figures (`summary_artifact_index.csv`)

Rule: never edit, reorder, deduplicate or reformat anything these indexes point to. A correction becomes a NEW file elsewhere, never an edit in place.
