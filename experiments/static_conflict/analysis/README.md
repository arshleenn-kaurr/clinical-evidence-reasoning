# Static benchmark analysis

All paths are under `../historical_package/evidence_not_vote_starter/`.

| Component | Code | Outputs | Status |
|---|---|---|---|
| Prespecified scoring (PRESPECIFIED) | `score_results.py` (hash locked) | `analysis/{primary_gemini,replication_gemini,veto_gemini,gpt_oss_primary,gpt_oss_veto,latent_v2_gemini,latent_gemini}/` | RECOVERED |
| Post-hoc contrasts (POST_HOC) | `posthoc_contrasts.py` | `analysis/posthoc_contrasts/` + `manifest.json` | RECOVERED, with a **script hash discrepancy** |
| Canonical results reference | n/a | `analysis/canonical_results_reference.md` | RECOVERED; not covered by any manifest |
| Dominant-evidence (POST_HOC) | `analysis/dominant_evidence/dominant_evidence.py` | `results.txt`, `.docx` | RECOVERED; paper inclusion unverified |
| Figure 1 | **MISSING** | `figures/figure1_decision_confidence_dissociation.{pdf,png}` | PARTIAL |
| Dev scoring | `score_results.py` | `analysis/dev_gpt_oss_120b{,_v2}/` | OPERATIONAL |

**Hash discrepancy:** `analysis/posthoc_contrasts/manifest.json` records `script_sha256 f388eb83…`, but the archived `posthoc_contrasts.py` hashes differently. Its mtime (2026-09-09 20:35) is later than the manifest outputs (19:24). All 9 inputs and 8 outputs in that manifest verify. The script that produced the archived outputs was therefore probably edited afterwards. Not repaired.

**Warning:** `posthoc_contrasts.py` writes to `analysis/posthoc_contrasts/` next to itself, and `score_results.py --out-dir` defaults to `analysis`. Re-run only on a scratch copy of the package, never inside `historical_package/`. Nothing was re-run during migration.
