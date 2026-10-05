#!/usr/bin/env python3
"""RELEASE TOOLING (not historical execution code).

Schema/integrity validator for docs/result_provenance.csv:
  - every row has the required columns and a non-empty paper/result_id/
    prespecified_or_posthoc/reproduced_status;
  - result_id is unique;
  - every semicolon-separated path in source_cohort / source_raw_file /
    source_canonical_file / analysis_script / analysis_output / protocol
    exists in the repository (relative to repo root), when non-empty;
  - camera_ready_location / table_number / figure_number / section are
    present (reserved for after camera-ready; "TODO" or "" are both valid
    placeholders).

Read-only. Exit 0 if valid, 1 otherwise.
"""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "docs/result_provenance.csv"

REQUIRED_COLUMNS = [
    "paper", "result_id", "description", "experiment", "source_cohort",
    "source_raw_file", "source_canonical_file", "analysis_script",
    "analysis_output", "protocol", "prespecified_or_posthoc",
    "reproduced_status", "value", "notes",
]
RESERVED_CAMERA_READY_COLUMNS = ["camera_ready_location", "table_number", "figure_number", "section"]
PATH_COLUMNS = ["source_cohort", "source_raw_file", "source_canonical_file", "analysis_script", "analysis_output", "protocol"]


def check_paths(value):
    missing = []
    for part in value.split(";"):
        p = part.strip()
        if not p or p.upper().startswith("NOT RECOVERED") or p.upper() == "MISSING":
            continue
        if not (ROOT / p).exists():
            missing.append(p)
    return missing


def main():
    if not CSV_PATH.exists():
        print(f"FAIL: {CSV_PATH} not found")
        return 1
    with open(CSV_PATH, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        header = reader.fieldnames or []
        rows = list(reader)

    problems = []
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in header]
    if missing_cols:
        problems.append(f"missing required columns: {missing_cols}")
    missing_reserved = [c for c in RESERVED_CAMERA_READY_COLUMNS if c not in header]

    seen_ids = set()
    for i, row in enumerate(rows, start=2):  # 1-indexed + header
        for col in ("paper", "result_id", "prespecified_or_posthoc", "reproduced_status"):
            if col in row and not row[col].strip():
                problems.append(f"row {i}: empty required field '{col}'")
        rid = row.get("result_id", "")
        if rid in seen_ids:
            problems.append(f"row {i}: duplicate result_id '{rid}'")
        seen_ids.add(rid)
        for col in PATH_COLUMNS:
            if col not in row or not row[col].strip():
                continue
            missing = check_paths(row[col])
            for m in missing:
                problems.append(f"row {i} ({rid}): {col} references missing path '{m}'")

    print(f"rows: {len(rows)}, unique result_ids: {len(seen_ids)}")
    if missing_reserved:
        print(f"NOTE: reserved camera-ready columns not present (will be added when camera-ready is final): {missing_reserved}")
    if problems:
        print(f"{len(problems)} PROBLEM(S):")
        for p in problems:
            print(" -", p)
        return 1
    print("result_provenance.csv: VALID")
    return 0


if __name__ == "__main__":
    sys.exit(main())
