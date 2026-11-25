# experiments

Organized by scientific design, not by paper:

- [`static_conflict/`](static_conflict/) — static conflicting-evidence / evidence-hierarchy benchmark (GenAI4Health; also the foundation AgenticLS builds on).
- [`persistent_context/`](persistent_context/) — sequential-vs-batch / persistent-context experiments. Two of its three runs (`gemini_persistent_260/`, `gemini_aligned_control_40/`) are the accepted AgenticLS experiments; the third (`groq_gpt_oss_120b/`) is a separate **post-acceptance cross-model extension, status IN PROGRESS / NOT CANONICALIZED**, out of scope for both papers' results.

Each leaf experiment folder holds a `README.md`, a machine-readable `experiment_manifest.json`, and (except for `analysis/`) a `historical_package/` — an intact, byte-identical, read-only copy of the recovered execution package. See `docs/data_provenance.md` for the frozen-input → raw-output → canonical-output → analysis chain, and `docs/recovery_status.md` for per-experiment status.
