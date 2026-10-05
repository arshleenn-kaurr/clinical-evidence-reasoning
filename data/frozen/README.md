# Frozen inputs (registry)

[`cohort_registry.csv`](cohort_registry.csv) groups frozen inputs by sha256.

## Shared cohorts (byte-identical copies, one scientific cohort)

| Cohort | sha256 | Copies (each kept for package provenance) |
|---|---|---|
| 260-case replication cohort | `b3bc2dd11b4d1e3b50b83ade39f093fc4d014f8b22652b506c37282a2c6a818a` (expected anchor: **matches**) | static `data/replication_cases.jsonl` (origin; frozen 2026-09-09T09:54:17Z by `freeze_replication.py`); Gemini-persistent `replication_cases_verified.jsonl`; Groq `replication_cases_verified.jsonl` |
| 10-case dev/smoke cohort | `f8a1b605632294c2d76891bd89842d2e9ffa816997cedbace69f3b329031312b` | static `data/dev_cases.jsonl`; Gemini-persistent and Groq `dev_cases.jsonl` |
| 40-case aligned-control subset | `6d0fbdf6085d4373779bb5755bf3575ef812eecea98529656d3c58a30a3ff540` (manuscript anchor: **matches**) | aligned-control package only. Every line is byte-identical to a line of the 260 cohort. |

The three 260-cohort files differ only in filename, not in content. They are one cohort, not different cohorts.

Other frozen inputs (single copy, static package): `final_main_cases.jsonl` (primary 40), `final_veto_cases.jsonl` (veto 15), and the raw MEDAL sources `QA-systematic-review.jsonl` and `recommendation-aha-guideline-clean.jsonl`.
