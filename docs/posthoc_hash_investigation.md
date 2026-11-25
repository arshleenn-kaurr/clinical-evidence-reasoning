# posthoc_contrasts.py hash investigation (Phase 3, step 5)

> **Public-facing summary (Phase 4.1, step 12):** The archived post-hoc analysis manifest records an earlier script hash that is no longer available. The recovered script differs from that recorded hash but regenerates all archived post-hoc outputs byte-for-byte under the verified reproduction environment (SciPy 1.16.3). The historical code change cannot be reconstructed and is retained as a provenance limitation. The mismatch is **not** claimed to be resolved.

Nothing was edited or replaced. All runs used scratch copies (`validation/scratch/posthoc_run*/`).

| Item | Value |
|---|---|
| Manifest recording the conflicting hash | `experiments/static_conflict/historical_package/evidence_not_vote_starter/analysis/posthoc_contrasts/manifest.json`, field `script_sha256` |
| manifest_expected_hash | `f388eb835b2444b1a93abd20d868f62be95c1033c2bc6dccd2da0a0c60ce4f8c` |
| recovered_script_hash | `c4fd856bd56fe0ed28209cfd692f4dc05f0ba3a2f1a3a4266dd8441f37b1f0cf` |
| other_candidate_hashes | **none found** |

## Search for other versions

- Recovered package: one `posthoc_contrasts.py`; no `.orig` / `.pre_*` / backup copy; no `__pycache__/posthoc_contrasts*.pyc` (other scripts have `.pyc` files, this one does not).
- All recovered zips (`evidence_not_vote_starter`, `agenticls_gemini_sequential`, `agenticls_aligned_persistent_control`, both Groq exports): no other member with this name.
- Local disk (Spotlight `mdfind` + `find` in Downloads/Desktop/Documents, excluding this repo): none.
- References: only the script itself and its own manifest. No README or other doc mentions it.

## Timestamps (zip member mtimes, 2026-09-09 local)

| Time | Artifact |
|---|---|
| 19:16 | `figures/figure1_decision_confidence_dissociation.{pdf,png}` |
| 19:24 | all 8 `analysis/posthoc_contrasts/*.csv` + `manifest.json` (records `f388eb83…`) |
| 20:35 | `posthoc_contrasts.py` (hashes to `c4fd856b…`) **and** `analysis/canonical_results_reference.md` |
| 23:37 | `analysis/dominant_evidence/*` |

## Code indicators (observations, not proof)

- The recovered script imports `from decimal import Decimal, ROUND_HALF_UP` but never uses it. `canonical_results_reference.md` states it uses ROUND_HALF_UP to 2 dp, and it shares the 20:35 timestamp. No recovered code writes that `.md` file.
- `import re` sits apart from the other imports, next to the anonymization helper. This is consistent with incremental editing, but the anonymization output already exists in the 19:24 manifest.

## Reproduction of archived outputs with the recovered script

| Environment | 8 output CSVs vs archive | Regenerated `manifest.json` vs archive |
|---|---|---|
| numpy 2.5.3 / pandas 3.0.6 / **scipy 1.18.1** | 7 EXACT_MATCH + 1 NUMERIC_MATCH (`binomial_proportions_exact.csv`: one cell, replication EDR1 `cp_lo`, 0.09365428649272982 → …986, Δ = 4.2e-17) | differs in `script_sha256` and that one output hash |
| numpy 2.5.3 / pandas 3.0.6 / **scipy 1.16.3** | **8/8 EXACT_MATCH** | differs **only** in `script_sha256` |

A direct probe of `100*scipy.stats.beta.ppf(0.025, 2, 258)` returns the archived value on scipy 1.16.2/1.16.3 and the new value on 1.17.0–1.18.1 (`validation/logs/step5_scipy_probe.log`). The one-ULP difference therefore comes from the scipy version, not the script.

The archived `canonical_results_reference.md` values were also checked: all 122 numeric lines match the regenerated outputs after ROUND_HALF_UP rounding (`validation/genai4health/posthoc_comparison.json`).

## Conclusion

- **The recovered script reproduces every archived post-hoc output byte-for-byte** (scipy 1.16.x), and to within 4e-17 under current scipy.
- **The manifest mismatch is NOT resolved.** The archived outputs were written by a file hashing to `f388eb83…`. The recovered file was modified afterwards (20:35), and the earlier version is not recoverable. Whatever changed did not alter any output for the archived inputs (for example comments/docstrings, or code paths that don't affect the 8 CSVs), but the content of the change cannot be determined.
- Likely provenance: an in-place edit of `posthoc_contrasts.py` between 19:24 and 20:35, possibly connected to producing `canonical_results_reference.md` (unused `Decimal` import, same timestamp). **Confidence:** high that the recovered script is output-equivalent on the archived inputs; low on what the edit was.
- Not done: no replacement, no edit, and the archived manifest is left as is. Suggested disclosure: "the archived post-hoc script differs from the version hash recorded at output time; it regenerates all archived outputs exactly."
