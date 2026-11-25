# Data provenance

## Chain

```
MEDAL Cochrane QA (data/QA-systematic-review.jsonl, sha256 983ba600… = replication_candidate_manifest raw_medal_sha256)
 ├─ prepare_cases.py → cochrane_candidates.csv (audited in place; sha256 1423f5be…) ─ freeze_cases/freeze_split → dev 10 / primary 40   [freeze_manifest.json]
 └─ prepare_replication_candidates.py → replication_candidates.csv (340; excludes original pool) → audited → freeze_replication.py
        → replication_cases.jsonl (260; b3bc2dd1…)                                                                               [replication_freeze_manifest.json]
            ├─ static Gemini replication (GenAI4Health)
            ├─ copied verbatim as replication_cases_verified.jsonl → Gemini persistent 260 (AgenticLS)
            │      └─ 40-line subset → aligned_control_cases_40.jsonl (6d0fbdf6…) → aligned control (AgenticLS)
            └─ copied verbatim → Groq GPT-OSS extension
MEDAL AHA guidelines (recommendation-aha-guideline-clean.jsonl) → aha_veto_candidates.csv (4885ed9c…) → veto 15
```

Every hash in this chain was verified against the recovered files (`scripts/verify_hashes.py`).

## Migration (2026-10-04)

| Package | Source | Copies |
|---|---|---|
| evidence_not_vote_starter | Drive zip, sha256 `226f0c2b…` | 167 |
| agenticls_gemini_sequential | Drive zip `c86ffbc9…` (restored from Trash by author) | 19 |
| agenticls_aligned_persistent_control | Drive zip `dbcb2b62…` (restored from Trash by author) | 14 |
| agenticls_groq_full_ready | local folder | 22 (+3 deferred) |

Each copy's sha256 equals its source (zip member bytes or file); see `copied_artifact_hashes.csv`. Zip member mtimes were applied to copies. Original zips and folders were not modified.

TODO: record the MEDAL dataset version/licence and the original download location (not stated in the package).
