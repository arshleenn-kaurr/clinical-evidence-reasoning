# AgenticLS Gemini persistent-context package

This package runs the optimized 6-call × 260-case Gemini experiment from Terminal. It is independent of Claude.

## 1. Enter the folder
```bash
cd ~/Downloads/agenticls_gemini_sequential
```

## 2. Confirm the frozen cohort hash
```bash
shasum -a 256 replication_cases_verified.jsonl
```
Expected:
```text
b3bc2dd11b4d1e3b50b83ade39f093fc4d014f8b22652b506c37282a2c6a818a  replication_cases_verified.jsonl
```

## 3. Dry run, no API calls
```bash
python3 run_sequential_gemini.py \
  --cases dev_cases.jsonl \
  --output results/gemini_smoke_results.jsonl \
  --attempt-log results/gemini_smoke_attempts.jsonl \
  --dry-run
```

## 4. Set the Gemini API key without printing it
```bash
read -s "GEMINI_API_KEY?Gemini API key: "; export GEMINI_API_KEY; echo
```

## 5. Smoke test on 10 excluded cases
```bash
caffeinate -i python3 run_sequential_gemini.py \
  --cases dev_cases.jsonl \
  --output results/gemini_smoke_results.jsonl \
  --attempt-log results/gemini_smoke_attempts.jsonl
```

Expected successful assessments: 10 × 6 = 60.

## 6. Structural smoke validation
```bash
python3 validate_smoke.py results/gemini_smoke_results.jsonl
```
Do not inspect smoke effect sizes. The validator reports operational structure only.

## 7. Main run
Only after the smoke validator says PASS:
```bash
caffeinate -i python3 run_sequential_gemini.py \
  --cases replication_cases_verified.jsonl \
  --output results/gemini_260_results.jsonl \
  --attempt-log results/gemini_260_attempts.jsonl
```

Expected successful assessments: 260 × 6 = 1,560.

If the laptop, terminal, network, or quota interrupts the run, execute the IDENTICAL command again. Successful run IDs are skipped and sequential history is reconstructed from successful canonical rows.

## 8. Do not analyze a partial run
After the full main run is complete:
```bash
python3 analyze_sequential_gemini.py \
  results/gemini_260_results.jsonl \
  --out results/gemini_260_analysis.json
```
The analysis script refuses an incomplete main run by default.

## Important current API note
The historical Gemini static benchmark supplied temperature=0. Current Gemini 3.6 Flash API documentation deprecates/ignores temperature/top_p/top_k, so this runner intentionally sends none of those sampling parameters and records that difference in every row.
