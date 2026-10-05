"""REPRODUCTION TOOLING: provenance / manifest integrity tests. Read-only."""
import csv
import json

import phase3_hash_report as hr
import pytest


@pytest.mark.archive  # validate_result_provenance.main() checks LICENSE_REVIEW source paths too
def test_result_provenance_csv_schema_and_paths():
    import validate_result_provenance as vrp
    assert vrp.main() == 0


@pytest.mark.public  # reads only docs/result_provenance.csv itself, which is PUBLIC_CORE
def test_result_provenance_csv_has_both_papers(root):
    rows = list(csv.DictReader(open(root / "docs/result_provenance.csv", encoding="utf-8")))
    papers = {r["paper"] for r in rows}
    assert papers == {"GenAI4Health", "AgenticLS"}
    assert len(rows) == len(set(r["result_id"] for r in rows)), "result_id must be unique"


@pytest.mark.archive  # historical_hashes dict keys are LICENSE_REVIEW cohort/results paths
def test_experiment_manifests_reference_existing_files(root):
    manifest_dirs = [
        "experiments/static_conflict/gemini_primary_40",
        "experiments/static_conflict/gemini_replication_260",
        "experiments/static_conflict/guideline_veto",
        "experiments/static_conflict/gpt_oss_sensitivity",
        "experiments/static_conflict/latent_v2",
        "experiments/static_conflict/analysis",
        "experiments/persistent_context/gemini_persistent_260",
        "experiments/persistent_context/gemini_aligned_control_40",
    ]

    # Fields that are known to hold repo-relative paths (either as a string/
    # list of paths, or as a dict keyed by path -> sha256). Free-text fields
    # like "notes" are deliberately excluded: they may legitimately contain
    # a "/" (e.g. "RAW/CLEAN") without being a path reference.
    PATH_KEYS = {
        "cohort_file", "runner_file", "protocol_file", "prompt_file", "analysis_files",
        "raw_attempt_file", "canonical_result_file", "frozen_inputs", "runner", "protocol",
        "canonical_results", "raw_attempts", "analysis_scripts", "archived_analysis_outputs",
        "reproduced_outputs", "archived_posthoc_outputs", "reproduced_outputs_scipy_1.18.1",
        "reproduced_outputs_scipy_1.16.3",
    }

    def check_paths(obj, problems, ctx, in_path_field=False):
        if isinstance(obj, dict):
            for k, v in obj.items():
                check_paths(v, problems, f"{ctx}.{k}", in_path_field=(k in PATH_KEYS))
                if in_path_field and k != "null" and "/" in k and not (root / k).exists():
                    problems.append(f"{ctx} (dict key): {k}")
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                check_paths(v, problems, f"{ctx}[{i}]", in_path_field=in_path_field)
        elif in_path_field and isinstance(obj, str) and "/" in obj and obj.upper() not in ("NULL", "NONE", "UNKNOWN"):
            if not (root / obj).exists():
                problems.append(f"{ctx}: {obj}")

    for d in manifest_dirs:
        manifest = root / d / "experiment_manifest.json"
        assert manifest.exists(), manifest
        data = json.loads(manifest.read_text())
        problems = []
        check_paths(data, problems, d)
        assert not problems, problems


@pytest.mark.archive  # hashes LICENSE_REVIEW cohort files directly
def test_hash_verification_report_anchors_match():
    rows = list(hr.entries())
    anchors_ok = all(hr.sha(target) == expected for _, _, target, expected in rows if target.exists())
    # At least the two frozen cohort anchors must be present and correct.
    assert any(str(t).endswith("replication_cases.jsonl") and hr.sha(t) == "b3bc2dd11b4d1e3b50b83ade39f093fc4d014f8b22652b506c37282a2c6a818a" for _, _, t, _ in rows)
    assert any(str(t).endswith("aligned_control_cases_40.jsonl") and hr.sha(t) == "6d0fbdf6085d4373779bb5755bf3575ef812eecea98529656d3c58a30a3ff540" for _, _, t, _ in rows)


@pytest.mark.archive  # hashes LICENSE_REVIEW/ARCHIVAL_ONLY files directly
def test_hash_verification_report_only_documented_mismatch():
    rows = list(hr.entries())
    mismatches = [(pkg, manifest, target) for pkg, manifest, target, expected in rows
                  if hr.sha(target) != expected]
    undocumented = [m for m in mismatches if "posthoc_contrasts.py" not in str(m[2])]
    assert undocumented == [], f"undocumented hash mismatch(es): {undocumented}"
