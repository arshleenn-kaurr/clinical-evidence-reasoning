#!/bin/bash
set -euo pipefail
mkdir -p results
python3 run_sequential_gemini.py \
  --cases dev_cases.jsonl \
  --output results/gemini_smoke_results.jsonl \
  --attempt-log results/gemini_smoke_attempts.jsonl
python3 validate_smoke.py results/gemini_smoke_results.jsonl
