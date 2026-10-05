# Gemini replication 260 (GenAI4Health; cohort shared with AgenticLS)

All paths are under `../historical_package/evidence_not_vote_starter/`.

- Cohort: `data/replication_cases.jsonl`, sha256 `b3bc2dd1…a818a`. **SHARED**: byte-identical to the cohorts used by `persistent_context/gemini_persistent_260` and `groq_gpt_oss_120b` (see `data/frozen/`).
- Selection: `prepare_replication_candidates.py` → `data/replication_candidates*.csv` → `freeze_replication.py` (manifests `data/replication_candidate_manifest.json`, `data/replication_freeze_manifest.json`; "supplementary replication extension"; "selection_uses_model_outputs": false).
- Prompts: `data/replication_prompts.jsonl` (1,560). Lock: `data/replication_evaluation_lock.sha256` (6/6 verify).
- Raw: `results/replication_gemini_3_6_flash_RAW.jsonl` (1,564 rows = 1,560 ok + 4 HTTP 503). Byte-identical to `results/replication_gemini_3_6_flash.jsonl`.
- Canonical: `results/replication_gemini_3_6_flash_CLEAN.jsonl` (1,560). Hashes in `results/replication_results.sha256` verify.
- Checkpoint: `results/replication_gemini_3_6_flash_checkpoint_676.jsonl`. Its name says 676 but it contains 675 rows; documented, not altered.
- Scoring: `analysis/replication_gemini/`
