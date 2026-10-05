# Gemini guideline / veto boundary 15 (GenAI4Health, BOUNDARY)

All paths are under `../historical_package/evidence_not_vote_starter/`.

- Source: `data/recommendation-aha-guideline-clean.jsonl` (MEDAL AHA guideline recommendations) → `data/aha_veto_candidates.csv` (audited)
- Cohort: `data/final_veto_cases.jsonl` (15 AHA COR III cases: harm 4, no_benefit 11)
- Prompts: `data/final_veto_prompts.jsonl` (90)
- Output: `results/final_veto_gemini_3_6_flash.jsonl`: 90 rows, 90 ok. No RAW/CLEAN split.
- Scoring: `analysis/veto_gemini/`

The same 15 cases were also run on GPT-OSS (see `../gpt_oss_sensitivity/`): 15 cases observed twice, not 30 independent cases (per the post-hoc manifest).
