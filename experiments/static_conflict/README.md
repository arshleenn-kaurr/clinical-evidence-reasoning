# static_conflict

The *Evidence Is Not a Vote* static evidence-conflict benchmark (GenAI4Health; also the foundation of AgenticLS).

Source: `historical_package/evidence_not_vote_starter/` is an intact byte-identical copy of the recovered package, minus `__pycache__/` and `.DS_Store`. All 40 entries in its `.sha256` lock files and all JSON freeze manifests verify in place.

Design (from the package's `README.md` / `analysis_contract.md`): a high-tier anchor (E0) plus synthetic lower-tier cards, under 6 conditions (`H, H_L1, H_L2, H_L4, H_L4_ALIGNED, L4_H`). Primary endpoint EDR_4; bootstrap seed 68020260909.

| Component | Folder | Status |
|---|---|---|
| Gemini primary 40 | [gemini_primary_40/](gemini_primary_40/) | RECOVERED, counts verified |
| Gemini replication 260 | [gemini_replication_260/](gemini_replication_260/) | RECOVERED, counts + hashes verified |
| Gemini guideline/veto 15 | [guideline_veto/](guideline_veto/) | RECOVERED, counts verified |
| GPT-OSS-120B primary 40 + veto 15 | [gpt_oss_sensitivity/](gpt_oss_sensitivity/) | RECOVERED, counts + hashes verified |
| Gemini latent-v2 40 | [latent_v2/](latent_v2/) | RECOVERED, counts + hashes verified |
| Gemini latent v1 40 | [latent_v2/](latent_v2/) (documented there) | SUPERSEDED / EXCLUDED FROM REPORTED ANALYSES; public release default `ARCHIVAL_ONLY` |
| Scoring, post-hoc, figure | [analysis/](analysis/) | PARTIAL: figure script missing; post-hoc script hash drift |

Each subfolder holds a README and `experiment_manifest.json` pointing into the package. No artifacts are duplicated.
