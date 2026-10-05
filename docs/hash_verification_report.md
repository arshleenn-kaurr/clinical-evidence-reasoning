# Hash verification report (Phase 3, step 2)

Generated 2026-10-04T10:32:45+00:00 by `scripts/phase3_hash_report.py`; machine-readable: `validation/hash_verification_report.json`. Repo-level `scripts/verify_hashes.py` was also run (log: `validation/logs/step2_verify_hashes.log`).

Scope: accepted-paper packages only (Groq extension out of scope).

- Manifest entries checked: **89**
- Matching: **88**
- Mismatching: **1**

## Integrity anchors

| Anchor | Path | Expected | Match |
|---|---|---|---|
| replication_260 | `experiments/static_conflict/historical_package/evidence_not_vote_starter/data/replication_cases.jsonl` | `b3bc2dd11b4d1e3b50b83ade39f093fc4d014f8b22652b506c37282a2c6a818a` | ✅ |
| replication_260 | `experiments/persistent_context/gemini_persistent_260/historical_package/agenticls_gemini_sequential/replication_cases_verified.jsonl` | `b3bc2dd11b4d1e3b50b83ade39f093fc4d014f8b22652b506c37282a2c6a818a` | ✅ |
| aligned_control_40 | `experiments/persistent_context/gemini_aligned_control_40/historical_package/agenticls_aligned_persistent_control/aligned_control_cases_40.jsonl` | `6d0fbdf6085d4373779bb5755bf3575ef812eecea98529656d3c58a30a3ff540` | ✅ |

## Mismatches

- `experiments/static_conflict/historical_package/evidence_not_vote_starter/posthoc_contrasts.py` per `analysis/posthoc_contrasts/manifest.json`: expected `f388eb835b2444b1a93abd20d868f62be95c1033c2bc6dccd2da0a0c60ce4f8c`, actual `c4fd856bd56fe0ed28209cfd692f4dc05f0ba3a2f1a3a4266dd8441f37b1f0cf`. This is the known `posthoc_contrasts.py` discrepancy; it was **not** passed over silently: see [posthoc_hash_investigation.md](posthoc_hash_investigation.md).

## Entries by manifest

| Package | Manifest | Entries | Match |
|---|---|---|---|
| evidence_not_vote_starter | `data/dev_cases.jsonl.sha256` | 1 | 1 |
| evidence_not_vote_starter | `data/evaluation_lock.sha256` | 7 | 7 |
| evidence_not_vote_starter | `data/final_main_cases.jsonl.sha256` | 1 | 1 |
| evidence_not_vote_starter | `data/final_veto_cases.jsonl.sha256` | 1 | 1 |
| evidence_not_vote_starter | `data/latent_ablation_lock.sha256` | 7 | 7 |
| evidence_not_vote_starter | `data/latent_v2_evaluation_lock.sha256` | 6 | 6 |
| evidence_not_vote_starter | `data/replication_candidates.csv.sha256` | 1 | 1 |
| evidence_not_vote_starter | `data/replication_cases.jsonl.sha256` | 1 | 1 |
| evidence_not_vote_starter | `data/replication_evaluation_lock.sha256` | 6 | 6 |
| evidence_not_vote_starter | `results/gpt_oss_primary_results.sha256` | 2 | 2 |
| evidence_not_vote_starter | `results/gpt_oss_veto_results.sha256` | 2 | 2 |
| evidence_not_vote_starter | `results/latent_main_results.sha256` | 1 | 1 |
| evidence_not_vote_starter | `results/latent_v2_results.sha256` | 2 | 2 |
| evidence_not_vote_starter | `results/replication_results.sha256` | 2 | 2 |
| evidence_not_vote_starter | `data/freeze_manifest.json` | 5 | 5 |
| evidence_not_vote_starter | `data/replication_freeze_manifest.json` | 2 | 2 |
| evidence_not_vote_starter | `data/replication_candidate_manifest.json` | 3 | 3 |
| evidence_not_vote_starter | `analysis/posthoc_contrasts/manifest.json` | 18 | 17 |
| agenticls_gemini_sequential | `SHA256SUMS.txt` | 8 | 8 |
| agenticls_gemini_sequential | `results/GEMINI_260_RAW_SHA256.txt` | 3 | 3 |
| agenticls_aligned_persistent_control | `SHA256SUMS.txt` | 7 | 7 |
| agenticls_aligned_persistent_control | `CONTROL_FREEZE_MANIFEST.json` | 3 | 3 |
