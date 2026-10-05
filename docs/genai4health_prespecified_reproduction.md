# GenAI4Health prespecified reproduction (Phase 3, step 4)

`score_results.py` (archived; sha256 locked in `data/evaluation_lock.sha256` and `data/replication_evaluation_lock.sha256`) was run from a scratch copy of the static package with `--out-dir validation/genai4health/prespecified/<cohort>/`. The historical package was not written to, and the scratch copy was confirmed unchanged afterwards. Commands: `validation/logs/step4_prespecified.log`. Environment: [environment_validation.md](environment_validation.md).

Inputs were the files the archived outputs were produced from, identified by the archived `merged_scored_results.csv` row counts (replication = 1,560 rows, so the CLEAN file):

| Cohort | `--results` | `--cases` | Files | Status |
|---|---|---|---|---|
| primary_gemini | `results/final_main_gemini_3_6_flash.jsonl` | `data/final_main_cases.jsonl` | 8/8 EXACT_MATCH | **EXACT_MATCH** |
| replication_gemini | `results/replication_gemini_3_6_flash_CLEAN.jsonl` | `data/replication_cases.jsonl` | 8/8 EXACT_MATCH | **EXACT_MATCH** |
| veto_gemini | `results/final_veto_gemini_3_6_flash.jsonl` | `data/final_veto_cases.jsonl` | 8/8 EXACT_MATCH | **EXACT_MATCH** |
| gpt_oss_primary | `results/final_main_gpt_oss_120b_CLEAN.jsonl` | `data/final_main_cases.jsonl` | 8/8 EXACT_MATCH | **EXACT_MATCH** |
| gpt_oss_veto | `results/final_veto_gpt_oss_120b_CLEAN.jsonl` | `data/final_veto_cases.jsonl` | 8/8 EXACT_MATCH | **EXACT_MATCH** |
| latent_v2_gemini | `results/latent_v2_main_gemini_3_6_flash_CLEAN.jsonl` | `data/final_main_cases.jsonl` | 8/8 EXACT_MATCH | **EXACT_MATCH** |

Each cohort's 8 outputs (`accuracy_by_condition`, `evidence_dilution_rate`, `order_sensitivity`, `veto_failure_rate`, `aligned_control`, `confidence_shift`, `flip_threshold`, `merged_scored_results`) are byte-identical to the archive, including the fixed-seed (68020260909) percentile bootstrap CIs. Per-file hashes: `validation/genai4health/prespecified_comparison.json`.

Not re-run: latent v1 (`analysis/latent_gemini/`; paper role unknown) and the dev scoring folders.

Known limitation (historical code, not changed): `score_results.py` percentile-bootstrap CIs degenerate for proportions near 0/1 (e.g. 0/15). The post-hoc script reports exact CIs for this reason.
