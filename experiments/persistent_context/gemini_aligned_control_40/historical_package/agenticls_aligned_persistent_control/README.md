# AgenticLS aligned persistent-context control

This is a post-hoc 40-case matched control for the completed Gemini persistent conflict experiment.

## Why this design is stronger than using the old primary 40
The 40 cases are deterministically selected from the exact 260-case cohort already used in the persistent conflict experiment. Therefore the new aligned results can be compared against existing conflict persistent/fresh results on the **same cases**.

The runner also reuses each case's already-successful persistent `H` response as the exact branch point. Only the aligned evidence updates are newly generated.

## Files
- `aligned_control_cases_40.jsonl` — frozen balanced control subset
- `run_aligned_control_gemini.py` — resume-safe runner
- `validate_aligned_control.py` — operational validation only
- `analyze_aligned_control.py` — scientific analysis after completion
- `PROTOCOL_FREEZE_ALIGNED_CONTROL.md` — frozen design and interpretation
- `SHA256SUMS.txt` — package hashes

## Required existing file
You need the completed conflict persistent result file from the prior experiment, usually:

`../agenticls_gemini_sequential/results/gemini_260_results.jsonl`

The runner uses only the existing successful sequential H response for each selected case as the branch point. The analyzer later uses the full same-case conflict results for the matched control contrast.

## Recommended sequence

1. Put this folder beside your existing `agenticls_gemini_sequential` folder in Downloads.
2. Load your Gemini API key.
3. Dry-run.
4. Run a 2-case smoke test to separate output paths.
5. Validate the smoke operationally. Do not interpret scientific values.
6. Run all 40 cases.
7. Validate for exactly 200 successful new calls.
8. Only then run the scientific analyzer.

The main run is resume-safe: rerun the identical command and output paths after any interruption or clean quota stop.
