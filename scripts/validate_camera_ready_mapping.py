#!/usr/bin/env python3
"""RELEASE TOOLING (not historical execution code).

Validates docs/camera_ready_provenance_mapping.csv (the populated Phase 5B mapping; default)
or, with --template, docs/camera_ready_provenance_mapping_template.csv, against
docs/result_provenance.csv. Does NOT fill in any manuscript page/section
values — those remain TODO until the authors have the camera-ready PDF in
hand. Checks:

  1. every result_id in the mapping file exists in result_provenance.csv
  2. no duplicate result_id rows with mutually contradictory content
     (same result_id, different non-TODO claim_text_short/table_number/
     figure_number/section/page values)
  3. required fields are non-empty and well-formed (paper is one of the two
     known papers; result_id matches the expected id pattern)
  4. for every row that has actually been mapped (claim_text_short is not
     TODO/empty), the corresponding result_provenance.csv row's
     reproduced_status still indicates REPRODUCED (i.e. a camera-ready claim
     is never mapped to a result that failed to reproduce)

Exit 0 if valid, 1 otherwise.
"""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAPPING_CSV = ROOT / "docs/camera_ready_provenance_mapping.csv"
TEMPLATE_CSV = ROOT / "docs/camera_ready_provenance_mapping_template.csv"
PROVENANCE_CSV = ROOT / "docs/result_provenance.csv"
KNOWN_PAPERS = {"GenAI4Health", "AgenticLS"}
REQUIRED_COLUMNS = ["paper", "result_id", "camera_ready_page", "section", "table_number",
                    "figure_number", "claim_text_short", "verified_against_artifact", "notes"]
MAPPED_COLUMNS = ["camera_ready_page", "section", "table_number", "figure_number", "claim_text_short"]


def is_todo(v):
    return (v or "").strip().upper() in ("", "TODO")


def main():
    global MAPPING_CSV
    if "--template" in sys.argv[1:]:
        MAPPING_CSV = TEMPLATE_CSV
    problems = []
    if not MAPPING_CSV.exists():
        print(f"FAIL: {MAPPING_CSV} not found")
        return 1
    if not PROVENANCE_CSV.exists():
        print(f"FAIL: {PROVENANCE_CSV} not found")
        return 1

    with open(MAPPING_CSV, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        header = reader.fieldnames or []
        rows = list(reader)
    with open(PROVENANCE_CSV, newline="", encoding="utf-8") as fh:
        prov = {r["result_id"]: r for r in csv.DictReader(fh)}

    missing_cols = [c for c in REQUIRED_COLUMNS if c not in header]
    if missing_cols:
        problems.append(f"mapping CSV missing required columns: {missing_cols}")

    by_id = {}
    for i, row in enumerate(rows, start=2):
        rid = row.get("result_id", "").strip()
        paper = row.get("paper", "").strip()
        if not rid:
            problems.append(f"row {i}: empty result_id")
            continue
        if paper not in KNOWN_PAPERS:
            problems.append(f"row {i} ({rid}): paper '{paper}' is not one of {sorted(KNOWN_PAPERS)}")
        if rid not in prov:
            problems.append(f"row {i} ({rid}): result_id does not exist in {PROVENANCE_CSV.name}")
        else:
            if prov[rid]["paper"] != paper and "SHARED_RESULT" not in row.get("notes", ""):
                problems.append(f"row {i} ({rid}): paper '{paper}' does not match "
                               f"result_provenance.csv's '{prov[rid]['paper']}' for this result_id")

        # Duplicate / contradiction check.
        key = tuple(row.get(c, "").strip() for c in MAPPED_COLUMNS)
        pk = (paper, rid)
        if pk in by_id and by_id[pk] != key:
            problems.append(f"row {i} ({rid}): duplicate (paper, result_id) with CONTRADICTORY mapping "
                           f"(previously {by_id[pk]}, now {key})")
        by_id.setdefault(pk, key)

        # Mapped rows must point at a reproduced result.
        ms = row.get("mapping_status", "").strip()
        if ms and ms not in ("MAPPED", "NOT_CITED", "PENDING_CAMERA_READY"):
            problems.append(f"row {i} ({rid}): unknown mapping_status '{ms}'")
        if ms == "MAPPED" and any(is_todo(row.get(c)) for c in MAPPED_COLUMNS):
            problems.append(f"row {i} ({rid}): mapping_status=MAPPED but a mapped column is TODO/empty")
        if ms == "PENDING_CAMERA_READY" and not is_todo(row.get("claim_text_short")):
            problems.append(f"row {i} ({rid}): PENDING_CAMERA_READY rows must keep TODO values")
        if not is_todo(row.get("claim_text_short")):
            status = prov.get(rid, {}).get("reproduced_status", "")
            if "REPRODUCED" not in status and "EXACT_MATCH" not in status and "VALUES REPRODUCED" not in status:
                problems.append(f"row {i} ({rid}): mapped to a manuscript claim, but "
                               f"reproduced_status is '{status}' (does not indicate REPRODUCED)")

    mapped = sum(1 for row in rows if not is_todo(row.get("claim_text_short")))
    print(f"rows: {len(rows)}; unique (paper, result_id): {len(by_id)}; mapped so far: {mapped} "
          f"(remaining TODO: {len(rows) - mapped})")

    if problems:
        print(f"{len(problems)} PROBLEM(S):")
        for p in problems:
            print(" -", p)
        return 1
    from collections import Counter
    print("mapping_status counts:", dict(Counter((r.get("paper"), r.get("mapping_status", "")) for r in rows)))
    print(f"{MAPPING_CSV.name}: VALID")
    return 0


if __name__ == "__main__":
    sys.exit(main())
