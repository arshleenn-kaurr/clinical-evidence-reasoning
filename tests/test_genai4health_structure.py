"""REPRODUCTION TOOLING: GenAI4Health canonical-structure tests.

Reuses scripts/phase3_structure.py's structural checker (counts, IDs,
condition coverage, raw->canonical mapping) rather than duplicating it.
Read-only on historical_package/.
"""
import phase3_structure as ps
import pytest

pytestmark = pytest.mark.archive  # requires the complete local archive (LICENSE_REVIEW inputs)


CASES = [
    ("gemini_primary_40", "results/final_main_gemini_3_6_flash.jsonl", None,
     "data/final_main_cases.jsonl", "data/final_main_prompts.jsonl", 40, None),
    ("gemini_replication_260", "results/replication_gemini_3_6_flash_CLEAN.jsonl",
     "results/replication_gemini_3_6_flash_RAW.jsonl", "data/replication_cases.jsonl",
     "data/replication_prompts.jsonl", 260, (1564, 1560, {"503": 4})),
    ("gemini_veto_15", "results/final_veto_gemini_3_6_flash.jsonl", None,
     "data/final_veto_cases.jsonl", "data/final_veto_prompts.jsonl", 15, None),
    ("gpt_oss_primary_40", "results/final_main_gpt_oss_120b_CLEAN.jsonl",
     "results/final_main_gpt_oss_120b_RAW.jsonl", "data/final_main_cases.jsonl",
     "data/final_main_prompts.jsonl", 40, None),
    ("gpt_oss_veto_15", "results/final_veto_gpt_oss_120b_CLEAN.jsonl",
     "results/final_veto_gpt_oss_120b_RAW.jsonl", "data/final_veto_cases.jsonl",
     "data/final_veto_prompts.jsonl", 15, None),
    ("gemini_latent_v2_40", "results/latent_v2_main_gemini_3_6_flash_CLEAN.jsonl",
     "results/latent_v2_main_gemini_3_6_flash_RAW.jsonl", "data/final_main_cases.jsonl",
     "data/latent_v2_main_prompts.jsonl", 40, None),
]


@pytest.mark.parametrize("name,canon,raw,cases,prompts,n,expect_raw", CASES, ids=[c[0] for c in CASES])
def test_structure_verified(name, canon, raw, cases, prompts, n, expect_raw):
    _, out = ps.static_exp(name, canon, raw, cases, prompts, n, expect_raw)
    assert out["status"] == "STRUCTURE_VERIFIED", out["problems"]
    assert out["successful_rows"] == out["expected_successful"] == n * 6
    assert out["duplicate_ids"] == []
    assert out["missing_ids_vs_prompts"] == []
    assert out["unexpected_ids_vs_prompts"] == []
    assert out["cases_missing"] == []
    assert out["cases_with_incomplete_conditions"] == []
    assert out["malformed_rows"] == 0
    assert out["schema_problem_counts"] == {}


def test_replication_raw_has_exactly_four_503_failures():
    _, out = ps.static_exp(*CASES[1])
    rtc = out["raw_to_canonical"]
    assert rtc["raw_rows"] == 1564
    assert rtc["raw_ok"] == 1560
    assert rtc["raw_error_http_status"] == {"503": 4}
    assert rtc["canonical_line_set_equals_raw_ok_line_set"] is True
