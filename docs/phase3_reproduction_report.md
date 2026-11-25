# Phase 3 reproduction report

Date: 2026-10-04 (UTC ≈09:30–09:50; per-step timestamps in `validation/logs/`). Scope: accepted-paper analyses only. **No API calls** were made. All re-execution used scratch copies. No archived artifact was modified: `scripts/verify_hashes.py` passes, and no file under any `historical_package/` changed during this phase. The Groq extension and camera-ready manuscripts are out of scope.

## 1. Experiments validated
GenAI4Health: Gemini primary 40, Gemini replication 260, Gemini veto 15, GPT-OSS primary 40, GPT-OSS veto 15, Gemini latent-v2 40, post-hoc contrasts, rounded reference values, Figure 1 data.
AgenticLS: Gemini persistent 260 + fresh comparator, Gemini aligned control 40 + fresh aligned comparator.

## 2. Source hashes verified
[hash_verification_report.md](hash_verification_report.md): 89 manifest entries across the three accepted-paper packages; **88 match, 1 mismatch** (`posthoc_contrasts.py` script hash; §9). Anchors: 260 cohort `b3bc2dd1…a818a` ✅ (static and Gemini copies); aligned subset `6d0fbdf6…f540` ✅. The repo-level verifier passes (222 copies, 95 historical manifest entries).

## 3. Canonical row counts ([canonical_structure_report.md](canonical_structure_report.md))
| Experiment | Canonical ok rows | Raw / attempts |
|---|---|---|
| Gemini primary 40 | 240/240 | no separate raw |
| Gemini replication 260 | 1,560/1,560 | 1,564 = 1,560 + 4 × HTTP 503; CLEAN = RAW ok rows, same order |
| Gemini veto 15 | 90/90 | no separate raw |
| GPT-OSS primary 40 | 240/240 | RAW == CLEAN |
| GPT-OSS veto 15 | 90/90 | RAW == CLEAN |
| Gemini latent-v2 40 | 240/240 | RAW == CLEAN |
| Gemini persistent 260 | 1,560/1,560 | 1,567 = 1,560 + 5 × 429 + 2 × 503; order 130/130 |
| Gemini aligned control 40 | 200/200 | 200, all HTTP 200; 5/5 per stratum; 160/160 branch points verified |

## 4. Duplicate / missing canonical IDs
None in any accepted-paper canonical file (IDs checked against the frozen prompt files for static runs and against the expected design grid for persistent runs). Malformed rows: 0. Schema problems: 0.

## 5. Analyses successfully rerun
`score_results.py` × 6 cohorts; `posthoc_contrasts.py` (two environments); `analyze_sequential_gemini.py`; `analyze_aligned_control.py`. All exited 0 with no edits, shims or wrappers. Commands: `validation/logs/`.

## 6. Exact-output matches
- Prespecified: **48/48 files EXACT_MATCH** (6 cohorts × 8 files) — [genai4health_prespecified_reproduction.md](genai4health_prespecified_reproduction.md)
- Post-hoc: **8/8 CSVs EXACT_MATCH under scipy 1.16.3**; 7/8 under scipy 1.18.1
- AgenticLS persistent 260: **EXACT_MATCH** (byte-identical; 159/159 fields)
- AgenticLS aligned control: **EXACT_MATCH** (byte-identical; 46/46 fields)

## 7. Semantic / numeric matches
- `binomial_proportions_exact.csv` under scipy 1.18.1: NUMERIC_MATCH. One cell (replication EDR1 `cp_lo`) differs by 4.2e-17, which traces to `scipy.stats.beta.ppf` changing between 1.16.x and 1.17.0 (`validation/diffs/`, `validation/logs/step5_scipy_probe.log`).
- `canonical_results_reference.md`: 122/122 numeric lines match regenerated outputs after the file's stated ROUND_HALF_UP rounding. During the check, a sign-formatting bug in **my comparator** (zero medians written `+0.0` in the reference) was fixed in `scripts/phase3_compare.py`; no data differed.

## 8. Mismatches
No result-value mismatches. The only non-identical artifacts are the regenerated post-hoc `manifest.json` files: their `script_sha256` field (and, under scipy 1.18.1, one output hash) differ from the archived manifest. This is expected, because the script records its own hash at run time.

## 9. Post-hoc script hash investigation
[posthoc_hash_investigation.md](posthoc_hash_investigation.md). The manifest expects `f388eb83…`; the recovered file is `c4fd856b…`, and no other version exists anywhere searched. The recovered script regenerates all archived outputs byte-exactly (scipy 1.16.3), so it is output-equivalent on the archived inputs. **The mismatch is not resolved**: the file was edited after the outputs were written (19:24 → 20:35), and what changed is unknown.

## 10. Figure 1
**DATA_REPRODUCED / PLOTTING_CODE_MISSING** ([figure_reproduction_status.md](figure_reproduction_status.md)). Not re-drawn.

## 11. Unresolved blockers
None block reproduction of the archived analyses. Open items:
1. Post-hoc script hash discrepancy (provenance unresolved).
2. Generator of `canonical_results_reference.md` not recovered (values verified).
3. Figure 1 plotting code not recovered.
4. Historical numpy/pandas versions unknown; scipy 1.16.x inferred.
5. Static Gemini primary/veto have no attempt logs.
6. Latent v1 and the dominant-evidence analysis: paper role unknown; not tested.
7. Camera-ready manuscripts pending: result IDs are not yet mapped to manuscript table/figure numbers.

## 12. Files modified by this phase
- **New, under `validation/`:** reports, regenerated outputs, comparisons, logs, diffs, README. `scratch/` and `.venv*/` are disposable and gitignored.
- **New scripts:** `scripts/phase3_hash_report.py`, `phase3_structure.py`, `phase3_compare.py`, `phase3_provenance.py`, `phase3_update_manifests.py`, `phase3_render_docs.py`.
- **New docs:** `environment_validation.md`, `hash_verification_report.md`, `canonical_structure_report.md`, `genai4health_prespecified_reproduction.md`, `posthoc_hash_investigation.md`, `result_provenance.{md,csv}`, `figure_reproduction_status.md`, this report.
- **Updated docs:** `recovery_status.md`, `papers/genai4health/{README,reproduce}.md`, `papers/agenticls/{README,reproduce}.md`, `public_release_audit.md` (manuscript wording), `.gitignore`, root `README.md` (link).
- **Updated manifests:** 8 accepted-paper `experiment_manifest.json` files gained separate `historical_hashes` and `phase3_reproduction` blocks. Existing fields were unchanged, and the Groq manifest was not touched.
- **Historical artifacts:** none modified.

## 13. Recommended Phase 4 tasks
1. Decide how to disclose the post-hoc script hash discrepancy (suggested wording in the investigation doc). If an older copy of the script surfaces anywhere (cloud drive, chat export), hash-check it against `f388eb83…`.
2. Recover or re-author the Figure 1 plotting code, and the generator of `canonical_results_reference.md`. Any new code must be validated against the archived figure and `.md` and marked as new.
3. When the camera-ready versions are final, map every manuscript number to a `result_id` in `docs/result_provenance.csv` and check them automatically.
4. Pin a reproduction environment (e.g. lockfile with scipy 1.16.3) and add a CI job that runs `scripts/phase3_*.py`.
5. Decide on latent v1 and the dominant-evidence analysis; optionally re-run `dominant_evidence.py` in scratch.
6. Public-release decisions (licence review, public artifact tier).
7. Separately, after the Groq run finishes: copy its deferred files and decide its canonicalization rule (out of scope here).
