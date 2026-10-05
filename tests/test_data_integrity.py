"""REPRODUCTION TOOLING: data-integrity tests. Read-only on historical_package/."""
import hashlib

import pytest

pytestmark = pytest.mark.archive  # requires the complete local archive (LICENSE_REVIEW inputs)


REPLICATION_260_SHA256 = "b3bc2dd11b4d1e3b50b83ade39f093fc4d014f8b22652b506c37282a2c6a818a"
ALIGNED_CONTROL_40_SHA256 = "6d0fbdf6085d4373779bb5755bf3575ef812eecea98529656d3c58a30a3ff540"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_260_cohort_hash_matches_manuscript_anchor(static_pkg):
    assert sha(static_pkg / "data/replication_cases.jsonl") == REPLICATION_260_SHA256


def test_260_cohort_identical_across_packages(static_pkg, gemini_pkg):
    a = static_pkg / "data/replication_cases.jsonl"
    b = gemini_pkg / "replication_cases_verified.jsonl"
    assert sha(a) == sha(b) == REPLICATION_260_SHA256


def test_aligned_control_40_hash_matches_manuscript_anchor(aligned_pkg):
    assert sha(aligned_pkg / "aligned_control_cases_40.jsonl") == ALIGNED_CONTROL_40_SHA256


def test_aligned_control_40_lines_are_subset_of_260_cohort(aligned_pkg, gemini_pkg):
    cohort_lines = set((gemini_pkg / "replication_cases_verified.jsonl").read_text(encoding="utf-8").splitlines())
    aligned_lines = [l for l in (aligned_pkg / "aligned_control_cases_40.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(aligned_lines) == 40
    assert all(l in cohort_lines for l in aligned_lines)


def test_dev_cohort_identical_across_packages(static_pkg, gemini_pkg):
    a = sha(static_pkg / "data/dev_cases.jsonl")
    b = sha(gemini_pkg / "dev_cases.jsonl")
    assert a == b == "f8a1b605632294c2d76891bd89842d2e9ffa816997cedbace69f3b329031312b"


def test_expected_case_counts(static_pkg):
    import json
    def load(p):
        return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(load(static_pkg / "data/final_main_cases.jsonl")) == 40
    assert len(load(static_pkg / "data/final_veto_cases.jsonl")) == 15
    assert len(load(static_pkg / "data/replication_cases.jsonl")) == 260


def test_expected_prompt_counts(static_pkg):
    import json
    def load(p):
        return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(load(static_pkg / "data/final_main_prompts.jsonl")) == 240
    assert len(load(static_pkg / "data/final_veto_prompts.jsonl")) == 90
    assert len(load(static_pkg / "data/replication_prompts.jsonl")) == 1560
    assert len(load(static_pkg / "data/latent_v2_main_prompts.jsonl")) == 240
