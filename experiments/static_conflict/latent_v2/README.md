# Latent-anchor sensitivity (Gemini)

All paths are under `../historical_package/evidence_not_vote_starter/`.

## latent-v2 40 (GenAI4Health, SENSITIVITY)
- Builder: `make_latent_v2.py` → `data/latent_v2_main_prompts.jsonl`, `data/latent_v2_anchor_audit.csv`. Lock: `data/latent_v2_evaluation_lock.sha256` (6/6 verify).
- Raw / Clean: `results/latent_v2_main_gemini_3_6_flash_RAW.jsonl` / `…_CLEAN.jsonl`: 240 ok each, byte-identical.
- Scoring: `analysis/latent_v2_gemini/`

## latent v1 40 — STATUS: SUPERSEDED / EXCLUDED FROM REPORTED ANALYSES

**Public release default: `ARCHIVAL_ONLY`.** Per the accepted-paper record: quality metadata remained visible, confidence intervals were inadvertently removed from some reconstructed anchors, and this run was not used as evidence in the reported manuscript. It was superseded by latent-v2 above.

- Builder: `make_latent_ablation.py` → `data/latent_main_prompts.jsonl`, `data/latent_anchor_audit.csv`. Lock: `data/latent_ablation_lock.sha256` (7/7 verify).
- Raw: `results/latent_main_gemini_3_6_flash_RAW.jsonl` (240 ok; no CLEAN). Scoring: `analysis/latent_gemini/`
- Retained for historical provenance only; not deleted, not further analyzed. Not among the accepted-paper's reported components.

Both entries are in `experiment_manifest.json`.

(The dominant-evidence analysis under `../analysis/` is a separate artifact whose exact manuscript-generation role remains uncertain and is unchanged by this correction — see `../analysis/README.md`.)
