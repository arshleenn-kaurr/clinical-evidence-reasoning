# Canonical structure report (Phase 3, step 3)

Generated 2026-10-04T10:32:46+00:00 by `scripts/phase3_structure.py`. Structural only; no outcome summaries computed. Machine-readable: `validation/canonical_structure_report.json`.

## GenAI4Health

| Experiment | Canonical file | Success / expected | Unique IDs | Dup IDs | Missing IDs | Cases | Incomplete cases | Malformed | Schema problems | Raw→canonical | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| gemini_primary_40 | `final_main_gemini_3_6_flash.jsonl` | 240/240 | 240 | 0 | 0 | 40/40 | 0 | 0 | 0 | n/a (no separate RAW) | **STRUCTURE_VERIFIED** |
| gemini_replication_260 | `replication_gemini_3_6_flash_CLEAN.jsonl` | 1560/1560 | 1560 | 0 | 0 | 260/260 | 0 | 0 | 0 | RAW 1564 rows (1560 ok, errors {'503': 4}); CLEAN = RAW ok rows in order: True; byte-identical: False | **STRUCTURE_VERIFIED** |
| gemini_veto_15 | `final_veto_gemini_3_6_flash.jsonl` | 90/90 | 90 | 0 | 0 | 15/15 | 0 | 0 | 0 | n/a (no separate RAW) | **STRUCTURE_VERIFIED** |
| gpt_oss_primary_40 | `final_main_gpt_oss_120b_CLEAN.jsonl` | 240/240 | 240 | 0 | 0 | 40/40 | 0 | 0 | 0 | RAW 240 rows (240 ok, errors 0); CLEAN = RAW ok rows in order: True; byte-identical: True | **STRUCTURE_VERIFIED** |
| gpt_oss_veto_15 | `final_veto_gpt_oss_120b_CLEAN.jsonl` | 90/90 | 90 | 0 | 0 | 15/15 | 0 | 0 | 0 | RAW 90 rows (90 ok, errors 0); CLEAN = RAW ok rows in order: True; byte-identical: True | **STRUCTURE_VERIFIED** |
| gemini_latent_v2_40 | `latent_v2_main_gemini_3_6_flash_CLEAN.jsonl` | 240/240 | 240 | 0 | 0 | 40/40 | 0 | 0 | 0 | RAW 240 rows (240 ok, errors 0); CLEAN = RAW ok rows in order: True; byte-identical: True | **STRUCTURE_VERIFIED** |

Expected IDs are the `prompt_id`s of the frozen prompt files; every output ID matches exactly (none missing, none unexpected).

## AgenticLS

### Gemini persistent 260

- Canonical rows: 1560/1560 ok; unique run_ids 1560; duplicates 0; missing 0; cases 260 (incomplete 0)
- Arm × condition: {'fresh:H_L4': 260, 'sequential:H': 260, 'sequential:H_L1': 260, 'sequential:H_L2': 260, 'sequential:H_L3': 260, 'sequential:H_L4': 260}
- Sequential history/message-count/cumulative-evidence problems: 0
- Attempts: 1567 rows; HTTP {'200': 1560, '429': 5, '503': 2}; ok-attempt run_ids == canonical: True
- Execution order (terminal log): overall {'fresh': 130, 'sequential': 130}; by stratum {'High|do_not_support': {'sequential': 32, 'fresh': 33}, 'High|support': {'sequential': 33, 'fresh': 32}, 'Moderate|do_not_support': {'fresh': 32, 'sequential': 33}, 'Moderate|support': {'fresh': 33, 'sequential': 32}}
- FINAL_BACKUP identical: results True, attempts True
- **STRUCTURE_VERIFIED**

### Gemini aligned control 40

- Cohort sha256 `6d0fbdf6085d4373779bb5755bf3575ef812eecea98529656d3c58a30a3ff540`; lines ⊂ 260 cohort: True; per stratum {'High|do_not_support': 10, 'High|support': 10, 'Moderate|do_not_support': 10, 'Moderate|support': 10}
- Canonical rows: 200/200; unique 200; duplicates 0; missing 0
- Arm × condition: {'fresh_aligned:H_L4_ALIGNED': 40, 'aligned_sequential:H_L1_ALIGNED': 40, 'aligned_sequential:H_L2_ALIGNED': 40, 'aligned_sequential:H_L3_ALIGNED': 40, 'aligned_sequential:H_L4_ALIGNED': 40}
- Attempts: 200; HTTP {'200': 200}
- Branch points (source_h_* → Gemini-260 sequential::H: run_id, prompt sha256, raw_text sha256, timestamp): **160/160**
- Execution order: overall {'fresh': 20, 'sequential': 20}; by stratum {'High|do_not_support': {'fresh': 5, 'sequential': 5}, 'High|support': {'fresh': 5, 'sequential': 5}, 'Moderate|do_not_support': {'fresh': 5, 'sequential': 5}, 'Moderate|support': {'fresh': 5, 'sequential': 5}}
- **STRUCTURE_VERIFIED**
