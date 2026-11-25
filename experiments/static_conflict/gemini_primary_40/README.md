# Gemini primary 40 (GenAI4Health, PRESPECIFIED)

All paths are under `../historical_package/evidence_not_vote_starter/`.

- Cohort: `data/final_main_cases.jsonl` (40 cases, 10 per quality × reference stratum; freeze 2026-09-09T06:12:54Z)
- Prompts: `data/final_main_prompts.jsonl` (240)
- Runner: `run_gemini.py` (model recorded in rows: `gemini-3.6-flash`; temperature 0)
- Output: `results/final_main_gemini_3_6_flash.jsonl`: 240 rows, 240 ok. No separate RAW/CLEAN file or attempt log.
- Scoring: `analysis/primary_gemini/` (`score_results.py`)

Notes: `run_gemini.py` defaults to `gemini-2.5-flash` and the model was overridden by `--model`. The primary `evaluation_lock.sha256` does not list `run_gemini.py`; later locks record a hash equal to the archived file. See `experiment_manifest.json`.
