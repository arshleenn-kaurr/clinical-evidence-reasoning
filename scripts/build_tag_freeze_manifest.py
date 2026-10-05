#!/usr/bin/env python3
"""RELEASE TOOLING. Writes (or with --check verifies) docs/tag_freeze_manifest.json: the exact
inputs each PROPOSED tag would freeze. Creates no tag. The final commit hash is null until a
git repository exists. Circularity note: files that themselves contain hashes of this manifest
(docs/public_release_manifest_draft.csv, docs/public_v1_scope.csv, preview MANIFEST.csv) are not
hashed here; the tag's commit hash is what freezes them.
"""
import hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/tag_freeze_manifest.json"


def sha(rel):
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def group(paths):
    return {p: sha(p) for p in paths}


STATIC = ["experiments/static_conflict/gemini_primary_40/experiment_manifest.json",
          "experiments/static_conflict/gemini_replication_260/experiment_manifest.json",
          "experiments/static_conflict/gpt_oss_sensitivity/experiment_manifest.json",
          "experiments/static_conflict/guideline_veto/experiment_manifest.json",
          "experiments/static_conflict/latent_v2/experiment_manifest.json",
          "experiments/static_conflict/analysis/experiment_manifest.json"]
PERSIST = ["experiments/persistent_context/gemini_persistent_260/experiment_manifest.json",
           "experiments/persistent_context/gemini_aligned_control_40/experiment_manifest.json"]
COMMON = ["docs/result_provenance.csv", "docs/camera_ready_provenance_mapping.csv", "docs/camera_ready_unmapped_claims.csv",
          "CITATION.cff", "requirements-reproduction.lock.txt"]


def build():
    audit = json.load(open(ROOT / "validation/camera_ready_number_audit.json"))
    ast = {p["paper"]: p["status"] for p in audit["papers"]}
    meta_a = json.load(open(ROOT / "papers/agenticls/paper/metadata.json"))
    return {
        "_status": "PROPOSAL ONLY. No tag has been created; no git repository exists. Commit hash is null until tagging.",
        "generated_by": "scripts/build_tag_freeze_manifest.py (--check re-verifies every hash)",
        "tags": {
            "agenticls-2026-camera-ready": {
                "status": "INPUTS_FROZEN_LOCALLY (revised PDF; number-audit status %s); tag DEFERRED by author policy until the GenAI4Health camera-ready is complete (no tags before then unless the authors decide otherwise)" % ast.get("agenticls"),
                "commit": None,
                "superseded_pdf_sha256": [v["pdf_sha256"] for v in meta_a.get("superseded_versions", [])],
                "camera_ready_pdf": {"path": meta_a["pdf_filename"] and "papers/agenticls/paper/" + meta_a["pdf_filename"], "sha256": meta_a["pdf_sha256"],
                                     "size_bytes": meta_a["pdf_size_bytes"], "redistribution": "PUBLIC_RELEASE_PENDING_PERMISSION (not in public tree)"},
                "paper_metadata": group(["papers/agenticls/paper/metadata.json"]),
                "experiment_manifests": group(STATIC + PERSIST),
                "paper_artifacts": group(["docs/camera_ready_number_audit.md", "validation/camera_ready_number_audit.json", "docs/camera_ready_claim_scope_audit.md"] + COMMON),
                "shared_cohort_sha256": "b3bc2dd11b4d1e3b50b83ade39f093fc4d014f8b22652b506c37282a2c6a818a",
                "aligned_subset_sha256": "6d0fbdf6085d4373779bb5755bf3575ef812eecea98529656d3c58a30a3ff540",
            },
            "genai4health-2026-camera-ready": {
                "status": "WAITING_FOR_CAMERA_READY_PDF (only the anonymized submission has been seen; not ingested)",
                "commit": None,
                "camera_ready_pdf": None,
                "paper_metadata": None,
                "experiment_manifests": group(STATIC),
                "paper_artifacts": group(["docs/result_provenance.csv", "docs/camera_ready_provenance_mapping.csv", "CITATION.cff"]),
            },
            "v1.0.0": {
                "status": "DEFERRED: MIT license selected; waiting for the GenAI4Health camera-ready (author policy: no v1.0.0, paper tags or GitHub Release before then unless the authors decide otherwise)",
                "commit": None,
                "contains": "V1_CORE + V1_SUPPORTING per docs/public_v1_scope.csv at the tagged commit; PDFs excluded",
                "experiment_manifests": group(STATIC + PERSIST),
                "paper_artifacts": group(COMMON),
                "excluded_from_freeze": ["experiments/persistent_context/groq_gpt_oss_120b (in-progress extension; its navigational docs ship for boundary clarity only)"],
            },
        },
    }


def main():
    new = build()
    if "--check" in sys.argv:
        old = json.load(open(OUT))
        if old != new:
            print("tag_freeze_manifest.json is STALE or a frozen input changed")
            return 1
        print("tag_freeze_manifest.json: all frozen hashes verified")
        return 0
    OUT.write_text(json.dumps(new, indent=2) + "\n", encoding="utf-8")
    print("wrote", OUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
