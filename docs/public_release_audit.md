# Public release audit

Classification only; nothing was deleted or redacted. Labels: **SAFE_PUBLIC · LIKELY_PUBLIC · NEEDS_LICENSE_REVIEW · PRIVATE_ARCHIVE_ONLY · UNKNOWN**. Paths: `P` = static package, `G` = Gemini persistent, `A` = aligned control, `Q` = Groq package (all under `experiments/…/historical_package/`).

## Scans performed

| Check | Result |
|---|---|
| API keys (`AIza…`, `gsk_…`, `sk-…`, Bearer tokens) | **None found** in any package. Gemini static runner puts the key in a URL query at runtime and the persistent runners use the `x-goog-api-key` header; neither is persisted. |
| Absolute local paths / username | Only `Q/nohup.out` (8× `/Users/<local-username>/…` in tracebacks, redacted here; the real value was the machine-local username). None in `P`, `G`, `A` text files; `.pyc` not copied. The Groq live resume log is not copied. |
| Email addresses | None in research files. |
| "Do not distribute" / confidential notices | None found in recovered artifacts. Manuscripts are CAMERA-READY PENDING and not yet reviewed. |
| Document metadata | `P/analysis/dominant_evidence/…docx` author "Un-named"; figure PDF creator Matplotlib. |
| Provider identifiers | Gemini `responseId`, `modelVersion` (G, A attempts); Groq `chatcmpl-…`, `x-request-id`, `x_groq.id/seed`, `system_fingerprint` (Q). No account/org/project IDs observed. Static dev 429 errors include Google quota metadata (no project number). |

## Classification

| Artifact | Label | Reason |
|---|---|---|
| `P/data/QA-systematic-review.jsonl` (3.5 MB, raw MEDAL Cochrane QA: DOIs, questions, notes) | NEEDS_LICENSE_REVIEW | Third-party dataset redistribution; Cochrane-derived text. The MEDAL licence is not recorded in the package. |
| `P/data/recommendation-aha-guideline-clean.jsonl` (1.2 MB, verbatim AHA recommendation text + source PDF names) | NEEDS_LICENSE_REVIEW | Copyrighted guideline text via MEDAL. |
| `P/data/cochrane_candidates*.csv`, `aha_veto_candidates.csv`, `replication_candidates*.csv` | NEEDS_LICENSE_REVIEW | Contain source notes plus author audit fields. |
| Frozen cohorts (`final_main_cases`, `final_veto_cases`, `replication_cases`/`_verified`, `dev_cases`, `aligned_control_cases_40`) | NEEDS_LICENSE_REVIEW (likely publishable as derived benchmark) | Anonymized questions, but anchors paraphrase Cochrane/AHA findings with effect estimates and DOIs. |
| Generated prompt files (`P/data/*prompts.jsonl`, 4.3 MB max) | NEEDS_LICENSE_REVIEW | Embed the cohort text. |
| Raw / clean model outputs (all packages) | NEEDS_LICENSE_REVIEW (provider terms) → likely LIKELY_PUBLIC | Model rationales may restate case text; Gemini and Groq output-redistribution terms should be checked. |
| Attempt logs with provider IDs (`G`, `A`, `Q`) | LIKELY_PUBLIC | IDs are not secrets; useful provenance. |
| Protocols, contracts, freeze manifests, `.sha256` locks | SAFE_PUBLIC | Author-written; no third-party text beyond hashes and file names. |
| Runners and analysis code | SAFE_PUBLIC (pending licence choice) | No secrets. |
| Scored CSVs, post-hoc tables, `canonical_results_reference.md`, analysis JSONs | LIKELY_PUBLIC | `merged_scored_results.csv` files embed rationales (1.7 MB max). |
| Figure 1 PDF/PNG | SAFE_PUBLIC | Author-generated. |
| `dominant_evidence_analysis.docx` | UNKNOWN | Post-hoc write-up; paper inclusion unverified. |
| Latent v1 artifacts | UNKNOWN | Unreported/unknown experiment; decide before publishing. |
| Dev/smoke outputs (static `results/dev_*`, `analysis/dev_*`, Gemini/aligned smoke) | LIKELY_PUBLIC (optional) | Operational. |
| Checkpoints / backups (`*_checkpoint_*`, `*_FINAL_BACKUP`, `*_PRE_RESUME_BACKUP`, `groq_interim_snapshot/`, `*.orig`, `*.pre_*`) | PRIVATE_ARCHIVE_ONLY | Redundant interim states; keep for provenance, not the public core. |
| `Q/nohup.out` | PRIVATE_ARCHIVE_ONLY | Absolute paths with username. |
| Groq extension (all) | PRIVATE_ARCHIVE_ONLY until complete | Unpublished, in-progress experiment; unresolved duplicate rows. |
| `__pycache__/`, `.DS_Store`, `.pid`, duplicate zips | not copied | Generated / scratch. |

## Size

Repo ≈ 53 MB. Largest file is 5.9 MB (`G/results/gemini_260_attempts.jsonl`, plus an identical `_FINAL_BACKUP`). No file needs Git LFS (GitHub's limit is 100 MB per file).
