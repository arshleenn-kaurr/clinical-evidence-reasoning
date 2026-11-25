# Gemini persistent-context 260 (AgenticLS, accepted)

All paths are under `historical_package/agenticls_gemini_sequential/` (intact copy; `SHA256SUMS.txt` 8/8 and `results/GEMINI_260_RAW_SHA256.txt` 3/3 verify in place).

- Protocol: `PROTOCOL_FREEZE_GEMINI.md` (frozen before aggregate results; primary endpoints, bootstrap 100,000 with seed 20260922, exploratory threshold sensitivity τ=70–95)
- Cohort: `replication_cases_verified.jsonl`, the **shared 260 cohort** (`b3bc2dd1…`); smoke cohort `dev_cases.jsonl`
- Runner: `run_sequential_gemini.py` (`gemini-3.6-flash`; no sampling parameters sent; provider-default thinking; `responseJsonSchema`)
- Raw attempts: `results/gemini_260_attempts.jsonl`, 1,567 = 1,560 HTTP 200 + 5 HTTP 429 + 2 HTTP 503
- Canonical results: `results/gemini_260_results.jsonl`, 1,560 ok, 1,560 unique run_ids (260 × [sequential H, H_L1, H_L2, H_L3, H_L4 + fresh H_L4])
- Backups: `results/*_FINAL_BACKUP.jsonl` (byte-identical to the above)
- Execution order: 130 fresh-first / 130 sequential-first (33/32 within each stratum), from `results/gemini_260_terminal.log`
- Analysis: `analyze_sequential_gemini.py` → `results/gemini_260_analysis.json` (archived; not re-run)
- Smoke: `results/gemini_smoke_{results,attempts}.jsonl` (60/60 ok)
- Executed 2026-09-22 04:01–06:10 UTC (row timestamps)

Prompts are constructed inside the runner. There is no separate prompt file; each row stores `prompt_sha256` and `request_sha256`.
