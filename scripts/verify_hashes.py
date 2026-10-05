#!/usr/bin/env python3
"""Verify byte identity of migrated artifacts. Read-only.

1. Every destination_path in docs/copied_artifact_hashes.csv still has the
   sha256 recorded from its source.
2. Every historical manifest shipped inside the preserved packages verifies
   in place (paths resolved relative to each package root, as originally
   written).
3. Known cross-package integrity anchors.

Known historical discrepancy (reported, not counted as failure):
  posthoc_contrasts.py differs from the script_sha256 recorded in
  analysis/posthoc_contrasts/manifest.json. See docs/migration_plan.md.

Exit code 1 on any unexpected mismatch.
"""
import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "experiments/static_conflict/historical_package/evidence_not_vote_starter"
GEMINI = ROOT / "experiments/persistent_context/gemini_persistent_260/historical_package/agenticls_gemini_sequential"
ALIGNED = ROOT / "experiments/persistent_context/gemini_aligned_control_40/historical_package/agenticls_aligned_persistent_control"
GROQ = ROOT / "experiments/persistent_context/groq_gpt_oss_120b/historical_package/agenticls_groq_full_ready"

ANCHORS = {
    "replication_260": ("b3bc2dd11b4d1e3b50b83ade39f093fc4d014f8b22652b506c37282a2c6a818a", [
        STATIC / "data/replication_cases.jsonl",
        GEMINI / "replication_cases_verified.jsonl",
        GROQ / "replication_cases_verified.jsonl",
    ]),
    "aligned_control_40": ("6d0fbdf6085d4373779bb5755bf3575ef812eecea98529656d3c58a30a3ff540", [
        ALIGNED / "aligned_control_cases_40.jsonl",
    ]),
}

failures = 0


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def check(label, path, expected, known=False):
    global failures
    got = sha256(path) if path.exists() else "MISSING"
    if got == expected:
        return
    if known:
        print(f"KNOWN DISCREPANCY {label}: {path.relative_to(ROOT)}")
        return
    failures += 1
    print(f"FAIL {label}: {path.relative_to(ROOT)} -> {got[:16]}")


def sha_list(manifest, base):
    """Verify `<hash>  <path>` lines, or a single bare hash for `<file>.sha256`."""
    n = 0
    for line in manifest.read_text().splitlines():
        parts = line.split(maxsplit=1)
        if not parts:
            continue
        if len(parts) == 1:
            target = manifest.with_name(manifest.name[: -len(".sha256")])
        else:
            target = base / parts[1].strip()
        check(manifest.name, target, parts[0])
        n += 1
    return n


def main():
    n = 0
    with open(ROOT / "docs/copied_artifact_hashes.csv", newline="") as fh:
        for row in csv.DictReader(fh):
            check("copy", ROOT / row["destination_path"], row["source_sha256"])
            n += 1
    print(f"copied artifacts checked: {n}")

    m = 0
    for f in sorted((STATIC / "data").glob("*.sha256")) + sorted((STATIC / "results").glob("*.sha256")):
        m += sha_list(f, STATIC)
    fm = json.loads((STATIC / "data/freeze_manifest.json").read_text())
    for name, h in fm["output_sha256"].items():
        check("freeze_manifest", STATIC / "data" / name, h); m += 1
    for k, h in fm["source_sha256"].items():
        check("freeze_manifest", STATIC / fm["source_files"][k], h); m += 1
    rm = json.loads((STATIC / "data/replication_freeze_manifest.json").read_text())
    check("replication_freeze_manifest", STATIC / rm["output"], rm["output_sha256"])
    check("replication_freeze_manifest", STATIC / rm["source_audited_csv"], rm["source_audited_csv_sha256"]); m += 2
    cm = json.loads((STATIC / "data/replication_candidate_manifest.json").read_text())
    check("replication_candidate_manifest", STATIC / "data/replication_candidates.csv", cm["replication_candidates_sha256"])
    check("replication_candidate_manifest", STATIC / "data/QA-systematic-review.jsonl", cm["raw_medal_sha256"])
    check("replication_candidate_manifest", STATIC / "data/cochrane_candidates.csv", cm["original_candidate_pool_sha256"]); m += 3
    pm = json.loads((STATIC / "analysis/posthoc_contrasts/manifest.json").read_text())
    check("posthoc manifest", STATIC / pm["script"], pm["script_sha256"], known=True); m += 1
    for p, h in pm["inputs"].items():
        check("posthoc manifest", STATIC / p, h); m += 1
    for p, v in pm["outputs"].items():
        check("posthoc manifest", STATIC / "analysis/posthoc_contrasts" / p, v["sha256"]); m += 1

    m += sha_list(GEMINI / "SHA256SUMS.txt", GEMINI)
    m += sha_list(GEMINI / "results/GEMINI_260_RAW_SHA256.txt", GEMINI)
    m += sha_list(ALIGNED / "SHA256SUMS.txt", ALIGNED)
    cf = json.loads((ALIGNED / "CONTROL_FREEZE_MANIFEST.json").read_text())
    check("control_freeze", ALIGNED / "aligned_control_cases_40.jsonl", cf["aligned_control_cases_sha256"])
    check("control_freeze", GEMINI / "results/gemini_260_results.jsonl", cf["completed_conflict_results_sha256_reference_copy"]); m += 2
    m += sha_list(GROQ / "SHA256SUMS.txt", GROQ)
    print(f"historical manifest entries checked: {m}")

    for name, (h, paths) in ANCHORS.items():
        for p in paths:
            check(f"anchor:{name}", p, h)
    print(f"anchors checked: {sum(len(p) for _, p in ANCHORS.values())}")

    print("ALL HASHES OK" if not failures else f"{failures} FAILURE(S)")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
