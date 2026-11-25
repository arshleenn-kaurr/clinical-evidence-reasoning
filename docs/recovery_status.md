# Recovery and reproduction status

Legend: STRUCTURE_VERIFIED (Phase 3 step 3) · ANALYSIS_REPRODUCED (archived analysis code re-run from scratch copies on archived canonical data, no API calls) · EXACT_MATCH / SEMANTIC_MATCH (comparison against archived outputs) · DISCREPANCY · BLOCKED.

| Experiment | Paper | Inputs | Runner | Raw outputs | Canonical outputs | Analysis | Hash verified | Structure | Analysis reproduced | Match | Discrepancy / blocked | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Gemini primary 40 | GenAI4Health | ✅ | ✅ | ✅ 240 (no attempt log) | raw file used (no CLEAN split) | ✅ | ✅ | STRUCTURE_VERIFIED | ANALYSIS_REPRODUCED | EXACT_MATCH (8/8) | none | REPRODUCED |
| Gemini replication 260 | GenAI4Health (cohort shared with AgenticLS) | ✅ | ✅ | ✅ 1,564 (1,560 + 4 × 503) | ✅ 1,560 | ✅ | ✅ | STRUCTURE_VERIFIED | ANALYSIS_REPRODUCED | EXACT_MATCH (8/8) | none | REPRODUCED |
| Gemini veto 15 | GenAI4Health | ✅ | ✅ | ✅ 90 (no attempt log) | raw file used | ✅ | ✅ | STRUCTURE_VERIFIED | ANALYSIS_REPRODUCED | EXACT_MATCH (8/8) | none | REPRODUCED |
| GPT-OSS primary 40 | GenAI4Health | ✅ | ✅ | ✅ 240 | ✅ 240 | ✅ | ✅ | STRUCTURE_VERIFIED | ANALYSIS_REPRODUCED | EXACT_MATCH (8/8) | none | REPRODUCED |
| GPT-OSS veto 15 | GenAI4Health | ✅ | ✅ | ✅ 90 | ✅ 90 | ✅ | ✅ | STRUCTURE_VERIFIED | ANALYSIS_REPRODUCED | EXACT_MATCH (8/8) | none | REPRODUCED |
| Gemini latent-v2 40 | GenAI4Health | ✅ | ✅ | ✅ 240 | ✅ 240 | ✅ | ✅ | STRUCTURE_VERIFIED | ANALYSIS_REPRODUCED | EXACT_MATCH (8/8) | none | REPRODUCED |
| Static post-hoc analysis | GenAI4Health | n/a | n/a | n/a | n/a | ✅ | ⚠️ script hash ≠ manifest | n/a | ANALYSIS_REPRODUCED | EXACT_MATCH 8/8 (scipy 1.16.3); 7 EXACT + 1 NUMERIC (scipy 1.18.1, Δ 4e-17) | DISCREPANCY: script hash (unresolved; see posthoc_hash_investigation.md) | REPRODUCED WITH DOCUMENTED DISCREPANCY |
| canonical_results_reference.md | GenAI4Health | n/a | ❌ generator not recovered | n/a | n/a | values | not in any manifest | n/a | values reproduced | 122/122 lines | generator missing | VALUES REPRODUCED |
| Figure 1 | GenAI4Health | n/a | ❌ plotting code | n/a | n/a | PDF/PNG | n/a | n/a | data reproduced | annotations agree | plotting code missing | DATA_REPRODUCED / PLOTTING_CODE_MISSING |
| Gemini latent v1 40 | SUPERSEDED / EXCLUDED FROM REPORTED ANALYSES | ✅ | ✅ | ✅ 240 | ❌ | ✅ | ✅ | not tested | not tested | n/a | not used as evidence in the reported manuscript (quality metadata visible; CIs inadvertently removed from some reconstructed anchors); superseded by latent-v2; public release default ARCHIVAL_ONLY | RECOVERED |
| Gemini persistent 260 + fresh | AgenticLS | ✅ | ✅ | ✅ 1,567 (1,560 + 5 × 429 + 2 × 503) | ✅ 1,560 | ✅ | ✅ | STRUCTURE_VERIFIED | ANALYSIS_REPRODUCED | EXACT_MATCH (159/159 fields) | none | REPRODUCED |
| Gemini aligned control 40 + fresh aligned | AgenticLS | ✅ | ✅ | ✅ 200, 0 failures | ✅ 200 | ✅ | ✅ | STRUCTURE_VERIFIED | ANALYSIS_REPRODUCED | EXACT_MATCH (46/46 fields) | none | REPRODUCED |
| Groq GPT-OSS persistent 260 | none (extension) | ✅ | ✅ | ⏳ live (deferred) | ❌ | ❌ | ✅ (frozen files) | out of scope | out of scope | n/a | out of scope for Phase 3 | IN PROGRESS |
| Manuscripts (both papers) | both | | | | | | | | | | | CAMERA-READY PENDING |
