# Reproduce: GenAI4Health

Status key: **REPRODUCED** = archived analysis code re-run in Phase 3 from scratch copies on archived data (no API calls) and compared with archived outputs · **VERIFIED** = hash/count checked · **RECOVERED** · **PARTIAL** · **NOT YET TESTED** · **CAMERA-READY PENDING**.

**Overall: analyses REPRODUCED, with one documented discrepancy** (post-hoc script hash). Figure 1 plotting code is missing; manuscript is CAMERA-READY PENDING. Full report: [`docs/phase3_reproduction_report.md`](../../docs/phase3_reproduction_report.md).

`P` = `experiments/static_conflict/historical_package/evidence_not_vote_starter/`

| Component | Inputs | Canonical data | Analysis output | Status |
|---|---|---|---|---|
| Gemini primary 40 | `P/data/final_main_cases.jsonl` | `P/results/final_main_gemini_3_6_flash.jsonl` (240) | `P/analysis/primary_gemini/` | **REPRODUCED**: EXACT_MATCH 8/8 |
| Gemini replication 260 | `P/data/replication_cases.jsonl` (`b3bc2dd1…`) | `…_CLEAN.jsonl` (1,560; = RAW ok rows in order; RAW 1,564 incl. 4 × 503) | `P/analysis/replication_gemini/` | **REPRODUCED**: EXACT_MATCH 8/8 |
| Gemini veto 15 | `P/data/final_veto_cases.jsonl` | `P/results/final_veto_gemini_3_6_flash.jsonl` (90) | `P/analysis/veto_gemini/` | **REPRODUCED**: EXACT_MATCH 8/8 |
| GPT-OSS primary 40 | frozen primary prompts | `…gpt_oss_120b_CLEAN.jsonl` (240) | `P/analysis/gpt_oss_primary/` | **REPRODUCED**: EXACT_MATCH 8/8 |
| GPT-OSS veto 15 | frozen veto prompts | `final_veto_gpt_oss_120b_CLEAN.jsonl` (90) | `P/analysis/gpt_oss_veto/` | **REPRODUCED**: EXACT_MATCH 8/8 |
| Gemini latent-v2 40 | `P/data/latent_v2_main_prompts.jsonl` | `…latent_v2…_CLEAN.jsonl` (240) | `P/analysis/latent_v2_gemini/` | **REPRODUCED**: EXACT_MATCH 8/8 |
| Prespecified scoring | `P/score_results.py` (hash locked) | above | per cohort | **REPRODUCED** |
| Post-hoc analysis | `P/posthoc_contrasts.py` | 6 cohorts above | `P/analysis/posthoc_contrasts/` | **REPRODUCED**: 8/8 EXACT_MATCH under scipy 1.16.3; 7 EXACT + 1 NUMERIC_MATCH (4e-17) under scipy 1.18.1. **DISCREPANCY:** script hash ≠ manifest (unresolved; [investigation](../../docs/posthoc_hash_investigation.md)) |
| Rounded reference values | n/a | n/a | `P/analysis/canonical_results_reference.md` | **VALUES REPRODUCED** 122/122 lines; generating code not recovered |
| Figure 1 | n/a | n/a | `P/figures/figure1_…{pdf,png}` | **DATA_REPRODUCED / PLOTTING_CODE_MISSING** ([status](../../docs/figure_reproduction_status.md)) |
| Dominant-evidence analysis | `P/analysis/dominant_evidence/dominant_evidence.py` | | `results.txt`, `.docx` | RECOVERED; NOT YET TESTED; paper use unverified |
| Cohort/prompt provenance | MEDAL sources, audit CSVs, freeze manifests, locks | | | VERIFIED |
| Manuscript | | | | CAMERA-READY PENDING |

Result-level map: [`docs/result_provenance.csv`](../../docs/result_provenance.csv).

## How to reproduce (no API calls)

```bash
python scripts/verify_hashes.py
python scripts/phase3_hash_report.py
python scripts/phase3_structure.py
```

Then, in a **scratch copy** of `P` (never in place; the scripts write next to themselves), with numpy/pandas/scipy installed:

```bash
python score_results.py --results <canonical results> --cases <cases> --out-dir <scratch_out>/<cohort>
python posthoc_contrasts.py
```

Finally run `scripts/phase3_compare.py` against the outputs. The exact commands used are in `validation/logs/step4_prespecified.log` and `step5_posthoc.log`. To get a byte-exact `binomial_proportions_exact.csv`, use scipy 1.16.x.
