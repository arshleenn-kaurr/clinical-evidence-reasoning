# validation/ (Phase 3)

Re-execution of archived accepted-paper analyses from **scratch copies**, with **no API calls**. Archived artifacts are never written. See `docs/phase3_reproduction_report.md`.

| Path | Content |
|---|---|
| `hash_verification_report.json` | Step 2 per-entry manifest verification |
| `canonical_structure_report.json` | Step 3 structural checks |
| `genai4health/prespecified/<cohort>/` | Regenerated `score_results.py` outputs |
| `genai4health/posthoc/` | Regenerated `posthoc_contrasts.py` outputs (scipy 1.18.1) |
| `genai4health/posthoc_scipy1.16.3/` | Same, sensitivity environment (scipy 1.16.3) |
| `genai4health/*_comparison.json` | Per-file / per-cell comparison vs archive |
| `genai4health/figure1_data_from_reproduced_outputs.csv` | Figure 1 data table from regenerated outputs |
| `agenticls/*.json` | Regenerated analyses and per-field comparisons |
| `logs/` | Exact commands, timestamps, pip freezes, scipy probe |
| `diffs/` | (empty: no unexplained diffs) |
| `scratch/`, `.venv*/` | Disposable, gitignored |
