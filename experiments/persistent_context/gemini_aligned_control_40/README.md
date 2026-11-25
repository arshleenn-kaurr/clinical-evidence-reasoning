# Gemini aligned persistent control 40 (AgenticLS, accepted; POST_HOC)

All paths are under `historical_package/agenticls_aligned_persistent_control/` (intact copy; `SHA256SUMS.txt` 7/7 verify).

- Protocol: `PROTOCOL_FREEZE_ALIGNED_CONTROL.md` (frozen 2026-09-23; post-hoc; bootstrap 10,000 with seed 2026092301)
- Cohort: `aligned_control_cases_40.jsonl`, sha256 `6d0fbdf6…f540`, **matches the manuscript anchor**. 10 cases per quality × reference stratum; every line is byte-identical to a line of the shared 260 cohort. `CONTROL_FREEZE_MANIFEST.json` lists the case_ids.
- Branch point: the existing `sequential::H` row from `../gemini_persistent_260/` is reused (no new H call). All 160 aligned persistent rows carry `source_h_*` fields that match those rows exactly (run_id, prompt sha256, raw_text sha256, timestamp).
- Runner: `run_aligned_control_gemini.py` (`--source-results` = Gemini-260 results; the package README expects it at `../agenticls_gemini_sequential/results/`)
- Raw attempts: `results/aligned_control_attempts.jsonl`, 200, all HTTP 200
- Canonical results: `results/aligned_control_results.jsonl`, 200 ok (40 × [H_L1..H_L4_ALIGNED persistent + fresh H_L4_ALIGNED])
- Execution order: 5 fresh-first / 5 sequential-first in every stratum (`results/aligned_control_terminal.log`)
- Analysis: `analyze_aligned_control.py` → `results/aligned_control_analysis.json` (archived; not re-run)
- Executed 2026-09-23 18:52–19:06 UTC
