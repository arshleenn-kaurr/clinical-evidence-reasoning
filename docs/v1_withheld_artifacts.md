# Artifacts withheld from public v1, and why

Generated from `docs/licensing_decision_matrix.csv`, `docs/public_release_manifest_draft.csv` and `docs/public_v1_scope.csv`. **Unresolved redistribution status is never converted into approval**; the default for v1 is exclusion. No author decision on any of these has been supplied.

## 1. `LICENSE_REVIEW` — 64 files, all excluded from every public build

| Artifact family | Files | Dispositions | Reason withheld |
|---|---|---|---|
| model_output | 32 | UNKNOWN=32 | Provider (Google/Groq) terms on output redistribution not reviewed; rationale text may restate MEDAL/Cochrane/AHA content. |
| derived_analysis_table | 9 | RELEASE_DERIVED_ONLY=9 | Per-row tables embed or are joined to restricted case text; aggregate substitutes already ship (`RELEASE_DERIVED_ONLY`). |
| frozen_cohort | 7 | UNKNOWN=7 | Anonymized but paraphrases Cochrane/AHA findings; MEDAL/Cochrane/AHA terms not reviewed. |
| candidate_audit_csv | 7 | UNKNOWN=7 | Embeds Cochrane/AHA source notes. |
| generated_prompt | 6 | UNKNOWN=6 | Prompts embed anchor text derived from restricted sources. |
| raw_source_dataset | 2 | UNKNOWN=2 | Verbatim MEDAL exports (Cochrane QA pairs; AHA guideline text). |
| illustrative_example | 1 | RELEASE_RECONSTRUCTION_SCRIPT_ONLY=1 | Real audited case; a synthetic replacement is a possible substitute (author preference). |

What stays public instead: hashes, schemas, aggregate result tables, construction/analysis code, and the 9 `RELEASE_DERIVED_ONLY` aggregate substitutes (`docs/restricted_artifact_substitutes.md`).

## 2. `ARCHIVAL_ONLY` — 55 files, excluded

- Groq GPT-OSS persistent-context extension (in progress, not canonicalized, not part of either accepted paper).
- Latent-v1 outputs (SUPERSEDED / EXCLUDED FROM REPORTED ANALYSES).
- Operational logs embedding the local developer's absolute paths/username (including the Phase 5B ingestion log).
- Superseded code backups; three post-hoc dominant-evidence files whose manuscript role was UNKNOWN. Observation (not a reclassification): the AgenticLS camera-ready now prints dominant-evidence numbers (App. E.4) that reproduce from the canonical outputs and agree with `analysis/dominant_evidence/results.txt`; the classification is left unchanged pending author decision.

## 3. Camera-ready PDFs — `PUBLIC_RELEASE_PENDING_PERMISSION` (1 file)

`papers/agenticls/paper/agenticls-camera-ready.pdf`. Redistribution permission (authors, workshop terms) is not established. GenAI4Health: no camera-ready ingested. The PDF's SHA256 is public in `metadata.json`/docs; the file is not.

## 4. `DEFER_FROM_V1` — 100 public-eligible files not in v1

Redundant reproduction intermediates, stale logs, dev/smoke output, superseded latent-v1 code fragments, internal migration bookkeeping, unimplemented stubs. Public-eligible later; see `docs/public_v1_scope.md`.

## 5. Open decisions that would change this list

- Redistribution rights for the 54 `UNKNOWN`-disposition files (MEDAL / Cochrane / AHA / provider terms) — authors, likely legal input.
- Whether the AgenticLS (and later GenAI4Health) PDF may be posted — authors / workshop.
- Whether author emails printed in the paper may appear in `papers/*/paper/metadata.json` and the number audit's quoted fragments in the public repo.
