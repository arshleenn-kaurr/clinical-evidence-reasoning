# Reproduce: AgenticLS

Status key as in `../genai4health/reproduce.md`. **Overall: analyses REPRODUCED (exact).** Both accepted-paper analyses were re-run from scratch copies on the archived canonical data and are byte-identical to the archived outputs. Manuscript: CAMERA-READY INGESTED / VERIFIED (see `paper/`). The Groq GPT-OSS extension is **not** part of this paper and was not analyzed.

`G` = `experiments/persistent_context/gemini_persistent_260/historical_package/agenticls_gemini_sequential/`
`A` = `experiments/persistent_context/gemini_aligned_control_40/historical_package/agenticls_aligned_persistent_control/`
`P` = `experiments/static_conflict/historical_package/evidence_not_vote_starter/`

| Component | Artifacts | Status |
|---|---|---|
| Shared 260 cohort | `P/data/replication_cases.jsonl` == `G/replication_cases_verified.jsonl` (`b3bc2dd1…`) | VERIFIED |
| Static benchmark foundation | `P/prompt_template.md`, `P/make_conditions.py`, `P/response_schema.json`, static analyses | VERIFIED; static analyses REPRODUCED (see GenAI4Health) |
| Gemini persistent 260: protocol, freeze manifests | `G/PROTOCOL_FREEZE_GEMINI.md`, `G/SHA256SUMS.txt`, `G/results/GEMINI_260_RAW_SHA256.txt` | VERIFIED |
| Raw attempts | `G/results/gemini_260_attempts.jsonl`: 1,567 = 1,560 + 5 × 429 + 2 × 503 | VERIFIED (STRUCTURE_VERIFIED) |
| Canonical results | `G/results/gemini_260_results.jsonl`: 1,560 ok, no duplicate or missing run_ids, history/message counts correct | VERIFIED (STRUCTURE_VERIFIED) |
| Execution balance | 130 fresh-first / 130 persistent-first (33/32 per stratum) | VERIFIED |
| Persistent analysis | `G/analyze_sequential_gemini.py` → `G/results/gemini_260_analysis.json` | **REPRODUCED**: EXACT_MATCH, 159/159 fields (incl. 100,000-resample bootstrap, seed 20260922) |
| Aligned control: cohort | `A/aligned_control_cases_40.jsonl` (`6d0fbdf6…`, 10 per stratum, ⊂ 260 cohort) | VERIFIED |
| Aligned control: protocol, manifests | `A/PROTOCOL_FREEZE_ALIGNED_CONTROL.md`, `A/CONTROL_FREEZE_MANIFEST.json`, `A/SHA256SUMS.txt` | VERIFIED |
| Aligned control: raw/canonical | 200 attempts (all HTTP 200), 200 ok rows | VERIFIED (STRUCTURE_VERIFIED) |
| Aligned control: branch points | 160/160 persistent rows link to the exact `G` sequential::H rows | VERIFIED |
| Aligned control: order balance | 5/5 per stratum | VERIFIED |
| Aligned control analysis | `A/analyze_aligned_control.py` → `A/results/aligned_control_analysis.json` | **REPRODUCED**: EXACT_MATCH, 46/46 fields (bootstrap 10,000, seed 2026092301) |
| Tables / figures | Figure 1 values (no plotting code in the AgenticLS packages; values verified by the number audit) | VALUES VERIFIED against archived outputs; plotting code for AgenticLS Figure 1 is not part of the recovered packages (not reconstructed; `docs/figure1_reconstruction.md` concerns the GenAI4Health figure only) |
| Manuscript | `paper/agenticls-camera-ready.pdf` | CAMERA-READY INGESTED / VERIFIED; number audit: `docs/camera_ready_number_audit.md` |

Result-level map: [`docs/result_provenance.csv`](../../docs/result_provenance.csv).

## How to reproduce (no API calls; standard library only)

Copy `G` and `A` side by side into scratch, then:

```bash
python3 analyze_sequential_gemini.py results/gemini_260_results.jsonl --out <scratch>/gemini_260_analysis.json
```

```bash
python3 analyze_aligned_control.py --cases aligned_control_cases_40.jsonl --aligned-results results/aligned_control_results.jsonl --conflict-results ../agenticls_gemini_sequential/results/gemini_260_results.jsonl --output-json <scratch>/aligned_control_analysis.json
```

Always pass `--output-json`: its default (`results/aligned_control_analysis.json`) would overwrite the archived file. Exact commands: `validation/logs/step6_7_agenticls.log`.
