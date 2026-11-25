#!/usr/bin/env python3
"""Phase 3, step 2: per-entry hash verification report for the accepted-paper
packages (static, Gemini persistent, aligned control). Read-only.
Writes validation/hash_verification_report.json."""
import datetime
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKGS = {
    "evidence_not_vote_starter": ROOT / "experiments/static_conflict/historical_package/evidence_not_vote_starter",
    "agenticls_gemini_sequential": ROOT / "experiments/persistent_context/gemini_persistent_260/historical_package/agenticls_gemini_sequential",
    "agenticls_aligned_persistent_control": ROOT / "experiments/persistent_context/gemini_aligned_control_40/historical_package/agenticls_aligned_persistent_control",
}
ANCHORS = [
    ("replication_260", "b3bc2dd11b4d1e3b50b83ade39f093fc4d014f8b22652b506c37282a2c6a818a", "evidence_not_vote_starter", "data/replication_cases.jsonl"),
    ("replication_260", "b3bc2dd11b4d1e3b50b83ade39f093fc4d014f8b22652b506c37282a2c6a818a", "agenticls_gemini_sequential", "replication_cases_verified.jsonl"),
    ("aligned_control_40", "6d0fbdf6085d4373779bb5755bf3575ef812eecea98529656d3c58a30a3ff540", "agenticls_aligned_persistent_control", "aligned_control_cases_40.jsonl"),
]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def entries():
    s = PKGS["evidence_not_vote_starter"]
    for m in sorted((s / "data").glob("*.sha256")) + sorted((s / "results").glob("*.sha256")):
        for line in m.read_text().splitlines():
            parts = line.split(maxsplit=1)
            if parts:
                tgt = m.with_name(m.name[:-7]) if len(parts) == 1 else s / parts[1].strip()
                yield "evidence_not_vote_starter", str(m.relative_to(s)), tgt, parts[0]
    fm = json.loads((s / "data/freeze_manifest.json").read_text())
    for k, h in fm["output_sha256"].items():
        yield "evidence_not_vote_starter", "data/freeze_manifest.json", s / "data" / k, h
    for k, h in fm["source_sha256"].items():
        yield "evidence_not_vote_starter", "data/freeze_manifest.json", s / fm["source_files"][k], h
    rm = json.loads((s / "data/replication_freeze_manifest.json").read_text())
    yield "evidence_not_vote_starter", "data/replication_freeze_manifest.json", s / rm["output"], rm["output_sha256"]
    yield "evidence_not_vote_starter", "data/replication_freeze_manifest.json", s / rm["source_audited_csv"], rm["source_audited_csv_sha256"]
    cm = json.loads((s / "data/replication_candidate_manifest.json").read_text())
    yield "evidence_not_vote_starter", "data/replication_candidate_manifest.json", s / "data/replication_candidates.csv", cm["replication_candidates_sha256"]
    yield "evidence_not_vote_starter", "data/replication_candidate_manifest.json", s / "data/QA-systematic-review.jsonl", cm["raw_medal_sha256"]
    yield "evidence_not_vote_starter", "data/replication_candidate_manifest.json", s / "data/cochrane_candidates.csv", cm["original_candidate_pool_sha256"]
    pm = json.loads((s / "analysis/posthoc_contrasts/manifest.json").read_text())
    yield "evidence_not_vote_starter", "analysis/posthoc_contrasts/manifest.json", s / pm["script"], pm["script_sha256"]
    for p, h in pm["inputs"].items():
        yield "evidence_not_vote_starter", "analysis/posthoc_contrasts/manifest.json", s / p, h
    for p, v in pm["outputs"].items():
        yield "evidence_not_vote_starter", "analysis/posthoc_contrasts/manifest.json", s / "analysis/posthoc_contrasts" / p, v["sha256"]
    for pkg, man in [("agenticls_gemini_sequential", "SHA256SUMS.txt"), ("agenticls_gemini_sequential", "results/GEMINI_260_RAW_SHA256.txt"), ("agenticls_aligned_persistent_control", "SHA256SUMS.txt")]:
        base = PKGS[pkg]
        for line in (base / man).read_text().splitlines():
            parts = line.split(maxsplit=1)
            if parts:
                yield pkg, man, base / parts[1].strip(), parts[0]
    a = PKGS["agenticls_aligned_persistent_control"]
    cf = json.loads((a / "CONTROL_FREEZE_MANIFEST.json").read_text())
    yield "agenticls_aligned_persistent_control", "CONTROL_FREEZE_MANIFEST.json", a / "aligned_control_cases_40.jsonl", cf["aligned_control_cases_sha256"]
    yield "agenticls_aligned_persistent_control", "CONTROL_FREEZE_MANIFEST.json", PKGS["agenticls_gemini_sequential"] / "results/gemini_260_results.jsonl", cf["completed_conflict_results_sha256_reference_copy"]
    yield "agenticls_aligned_persistent_control", "CONTROL_FREEZE_MANIFEST.json", PKGS["agenticls_gemini_sequential"] / "replication_cases_verified.jsonl", cf["source_replication_cases_sha256"]


def main():
    rows = []
    for pkg, manifest, target, expected in entries():
        got = sha(target)
        rows.append({"package": pkg, "manifest": manifest, "target": str(target.relative_to(ROOT)),
                     "expected_sha256": expected, "actual_sha256": got, "match": got == expected})
    anchors = [{"anchor": n, "expected_sha256": h, "path": str((PKGS[p] / f).relative_to(ROOT)),
                "actual_sha256": sha(PKGS[p] / f), "match": sha(PKGS[p] / f) == h} for n, h, p, f in ANCHORS]
    mism = [r for r in rows if not r["match"]]
    report = {
        "generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "scope": "accepted-paper packages only (Groq extension out of scope)",
        "n_manifest_entries": len(rows), "n_match": len(rows) - len(mism), "n_mismatch": len(mism),
        "mismatches": mism, "anchors": anchors, "entries": rows,
    }
    out = ROOT / "validation/hash_verification_report.json"
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(f"{len(rows)} entries, {len(mism)} mismatch(es); anchors: {[a['match'] for a in anchors]}")
    for m in mism:
        print("MISMATCH", m["manifest"], m["target"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
