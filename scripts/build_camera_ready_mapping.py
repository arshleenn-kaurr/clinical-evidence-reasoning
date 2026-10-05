#!/usr/bin/env python3
"""RELEASE TOOLING. Builds docs/camera_ready_provenance_mapping.csv (+ unmapped-claims CSV)
from the template, docs/result_provenance.csv and validation/camera_ready_number_audit.json.

It only RECORDS what scripts/audit_camera_ready_numbers.py located in the ingested PDF; it
never touches result values. Papers without an ingested camera-ready PDF keep TODO rows with
mapping_status=PENDING_CAMERA_READY. Run the audit first.
"""
import csv, json, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "docs/camera_ready_provenance_mapping_template.csv"
PROV = ROOT / "docs/result_provenance.csv"
AUDIT = ROOT / "validation/camera_ready_number_audit.json"
OUT = ROOT / "docs/camera_ready_provenance_mapping.csv"
OUT_UNMAPPED = ROOT / "docs/camera_ready_unmapped_claims.csv"
PAPER_LABEL = {"agenticls": "AgenticLS", "genai4health": "GenAI4Health"}
# Result IDs whose printed values are shown in AgenticLS Figure 1 (panels A-C); verified by the audit's page-4 fragments.
FIG1 = {"g4h.replication.EDR1", "g4h.replication.EDR2", "g4h.replication.EDR4", "g4h.replication.conflict_minus_aligned",
        "agl.aligned40.aligned_gap", "agl.aligned40.conflict_gap_same40", "agl.aligned40.interaction", "agl.aligned40.trajectories"}
COLS = ["paper", "result_id", "camera_ready_page", "section", "table_number", "figure_number",
        "claim_text_short", "verified_against_artifact", "notes", "mapping_status"]


def main():
    audit = {p["paper"]: p for p in json.load(open(AUDIT))["papers"]}
    prov = {r["result_id"]: r for r in csv.DictReader(open(PROV, newline="", encoding="utf-8"))}
    tmpl = list(csv.DictReader(open(TEMPLATE, newline="", encoding="utf-8")))
    rows, unmapped = [], []
    for key, label in PAPER_LABEL.items():
        a = audit.get(key)
        if not a or "claims" not in a:
            for t in tmpl:
                if t["paper"] == label:
                    rows.append({**t, "mapping_status": "PENDING_CAMERA_READY",
                                 "notes": "Camera-ready PDF not yet ingested for this paper."})
            continue
        by = defaultdict(list)
        for c in a["claims"]:
            if c["result_id"]:
                for rid in c["result_id"].split(";"):
                    by[rid].append(c)
            else:
                unmapped.append({"paper": label, "claim_id": c["claim_id"], "camera_ready_page": c["page"], "section": c["section"],
                                 "printed_value": c["printed"], "audit_status": c["status"], "how_verified": c["source"],
                                 "new_provenance_row_recommended": "yes" if c["status"] != "TEXTUAL_CLAIM_VERIFIED" or "recompute" in c["source"] else "optional"})
        for rid, p in prov.items():
            own = p["paper"] == label
            cl = by.get(rid, [])
            if not cl and not own:
                continue
            if not cl:
                rows.append({"paper": label, "result_id": rid, "camera_ready_page": "N/A", "section": "N/A", "table_number": "N/A",
                             "figure_number": "N/A", "claim_text_short": "NOT_CITED_IN_CAMERA_READY",
                             "verified_against_artifact": "N/A", "notes": "Supporting/derived result; value not printed in the camera-ready PDF.",
                             "mapping_status": "NOT_CITED"})
                continue
            pages = sorted({c["page"] for c in cl})
            secs = []
            for c in cl:
                if c["section"] not in secs:
                    secs.append(c["section"])
            printed = []
            for c in cl:
                if c["printed"] not in printed:
                    printed.append(c["printed"])
            sts = sorted({c["status"] for c in cl})
            bad = [c["claim_id"] for c in cl if c["status"] in ("MISMATCH", "NOT_MACHINE_CHECKABLE")]
            notes = []
            if not own:
                notes.append(f"SHARED_RESULT (provenance paper: {p['paper']})")
            if bad:
                notes.append("AUDIT FLAG on claim(s): " + ", ".join(bad) + " (see docs/camera_ready_number_audit.md)")
            rows.append({"paper": label, "result_id": rid, "camera_ready_page": "; ".join(f"p.{x}" for x in pages),
                         "section": "; ".join(secs), "table_number": "N/A (no numbered tables)",
                         "figure_number": "1" if rid in FIG1 else "N/A",
                         "claim_text_short": f"{p['description'][:80]} - printed: " + ", ".join(printed[:8]),
                         "verified_against_artifact": f"{p['analysis_output'].split(';')[0]} | audit: {'/'.join(sts)} ({len(cl)} printed value(s))",
                         "notes": " ".join(notes), "mapping_status": "MAPPED"})
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)
    with open(OUT_UNMAPPED, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["paper", "claim_id", "camera_ready_page", "section", "printed_value", "audit_status", "how_verified", "new_provenance_row_recommended"])
        w.writeheader()
        w.writerows(unmapped)
    from collections import Counter
    print(Counter((r["paper"], r["mapping_status"]) for r in rows), "| unmapped claims:", len(unmapped))


if __name__ == "__main__":
    sys.exit(main())
