"""REPRODUCTION TOOLING: re-run archived analysis code in a pytest tmp_path
scratch copy and compare byte-for-byte against the archived outputs. Never
writes into historical_package/. No network access.

Reuses scripts/phase3_compare.py's comparator. If scipy != 1.16.3 (see
docs/reproduction_environment.md), the post-hoc binomial-proportions output
may be NUMERIC_MATCH (~1e-17) instead of EXACT_MATCH; that is accepted here
but logged, matching scripts/validate_accepted_papers.py's policy.
"""
import hashlib
import shutil
import subprocess
import sys

import phase3_compare as pc
import pytest

pytestmark = pytest.mark.archive  # requires the complete local archive (LICENSE_REVIEW inputs)



def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

COHORTS = {
    "primary_gemini": ("results/final_main_gemini_3_6_flash.jsonl", "data/final_main_cases.jsonl"),
    "replication_gemini": ("results/replication_gemini_3_6_flash_CLEAN.jsonl", "data/replication_cases.jsonl"),
    "veto_gemini": ("results/final_veto_gemini_3_6_flash.jsonl", "data/final_veto_cases.jsonl"),
    "gpt_oss_primary": ("results/final_main_gpt_oss_120b_CLEAN.jsonl", "data/final_main_cases.jsonl"),
    "gpt_oss_veto": ("results/final_veto_gpt_oss_120b_CLEAN.jsonl", "data/final_veto_cases.jsonl"),
    "latent_v2_gemini": ("results/latent_v2_main_gemini_3_6_flash_CLEAN.jsonl", "data/final_main_cases.jsonl"),
}


@pytest.fixture(scope="module")
def static_scratch(tmp_path_factory, static_pkg):
    dest = tmp_path_factory.mktemp("static") / "evidence_not_vote_starter"
    shutil.copytree(static_pkg, dest)
    return dest


@pytest.fixture(scope="module")
def gemini_scratch(tmp_path_factory, gemini_pkg):
    dest = tmp_path_factory.mktemp("gemini") / "agenticls_gemini_sequential"
    shutil.copytree(gemini_pkg, dest)
    return dest


@pytest.fixture(scope="module")
def aligned_scratch(tmp_path_factory, aligned_pkg):
    dest = tmp_path_factory.mktemp("aligned") / "agenticls_aligned_persistent_control"
    shutil.copytree(aligned_pkg, dest)
    return dest


@pytest.mark.parametrize("cohort", COHORTS)
def test_prespecified_scoring_reproduces_exactly(static_scratch, static_pkg, tmp_path, cohort):
    results, cases = COHORTS[cohort]
    out_dir = tmp_path / cohort
    p = subprocess.run([sys.executable, "-B", "score_results.py", "--results", results,
                        "--cases", cases, "--out-dir", str(out_dir)],
                       cwd=static_scratch, capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    archived_dir = static_pkg / "analysis" / cohort
    before = {f.name: sha(f) for f in archived_dir.iterdir()}
    for f in out_dir.iterdir():
        rec = pc.compare_file(f, archived_dir / f.name)
        assert rec["status"] == "EXACT_MATCH", (f.name, rec["differences"][:3])
    # The archived package itself must be unchanged by running the scratch copy.
    after = {f.name: sha(f) for f in archived_dir.iterdir()}
    assert before == after


def test_posthoc_contrasts_reproduces(static_scratch, static_pkg, tmp_path):
    p = subprocess.run([sys.executable, "-B", "posthoc_contrasts.py"],
                       cwd=static_scratch, capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    out_dir = static_scratch / "analysis" / "posthoc_contrasts"
    archived_dir = static_pkg / "analysis" / "posthoc_contrasts"
    for f in out_dir.iterdir():
        if f.name == "manifest.json":
            continue  # records its own script hash; expected to differ, see docs/posthoc_hash_investigation.md
        rec = pc.compare_file(f, archived_dir / f.name)
        assert rec["status"] in ("EXACT_MATCH", "NUMERIC_MATCH"), (f.name, rec["differences"][:3])


def test_gemini_persistent_260_analysis_reproduces_exactly(gemini_scratch, gemini_pkg, tmp_path):
    out = tmp_path / "gemini_260_analysis.json"
    p = subprocess.run([sys.executable, "-B", "analyze_sequential_gemini.py",
                        "results/gemini_260_results.jsonl", "--out", str(out)],
                       cwd=gemini_scratch, capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    rec = pc.compare_file(out, gemini_pkg / "results/gemini_260_analysis.json")
    assert rec["status"] == "EXACT_MATCH", rec["differences"][:5]


def test_aligned_control_40_analysis_reproduces_exactly(gemini_scratch, aligned_scratch, aligned_pkg, tmp_path):
    out = tmp_path / "aligned_control_analysis.json"
    p = subprocess.run([sys.executable, "-B", "analyze_aligned_control.py",
                        "--cases", "aligned_control_cases_40.jsonl",
                        "--aligned-results", "results/aligned_control_results.jsonl",
                        "--conflict-results", str(gemini_scratch / "results/gemini_260_results.jsonl"),
                        "--output-json", str(out)],
                       cwd=aligned_scratch, capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    rec = pc.compare_file(out, aligned_pkg / "results/aligned_control_analysis.json")
    assert rec["status"] == "EXACT_MATCH", rec["differences"][:5]
