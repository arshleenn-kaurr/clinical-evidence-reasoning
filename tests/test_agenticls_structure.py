"""REPRODUCTION TOOLING: AgenticLS canonical-structure tests.

Reuses scripts/phase3_structure.py's structural checker. Read-only on
historical_package/.
"""
import phase3_structure as ps
import pytest

pytestmark = pytest.mark.archive  # requires the complete local archive (LICENSE_REVIEW inputs)



def test_gemini_persistent_260_structure():
    out = ps.gemini_260()
    assert out["status"] == "STRUCTURE_VERIFIED", out["problems"]
    assert out["successful_rows"] == out["expected_successful"] == 1560
    assert out["unique_run_ids"] == 1560
    assert out["duplicate_run_ids"] == []
    assert out["missing_run_ids"] == []


def test_gemini_persistent_260_attempts_counts():
    out = ps.gemini_260()
    att = out["attempts"]
    assert att["rows"] == 1567
    assert att["http_status"] == {"200": 1560, "429": 5, "503": 2}
    assert att["ok_attempt_run_ids_equal_canonical"] is True


def test_gemini_persistent_260_arm_order_balance():
    out = ps.gemini_260()
    eo = out["execution_order"]
    assert eo["cases_in_log"] == 260
    assert eo["conflicting_labels"] == 0
    assert eo["overall"] == {"fresh": 130, "sequential": 130}


def test_aligned_control_40_structure():
    out = ps.aligned_40()
    assert out["status"] == "STRUCTURE_VERIFIED", out["problems"]
    assert out["successful_rows"] == out["expected_successful"] == 200
    assert out["unique_run_ids"] == 200
    assert out["duplicate_run_ids"] == []
    assert out["missing_run_ids"] == []


def test_aligned_control_40_ten_per_stratum():
    out = ps.aligned_40()
    assert out["cases_per_stratum"] == {
        "High|do_not_support": 10, "High|support": 10,
        "Moderate|do_not_support": 10, "Moderate|support": 10,
    }


def test_aligned_control_40_execution_order_5_5_per_stratum():
    out = ps.aligned_40()
    for stratum, counts in out["execution_order"]["by_stratum"].items():
        assert counts == {"fresh": 5, "sequential": 5}, stratum


def test_aligned_control_40_attempts_all_succeed():
    out = ps.aligned_40()
    assert out["attempts"]["rows"] == 200
    assert out["attempts"]["http_status"] == {"200": 200}


def test_aligned_control_40_branch_points_verified():
    out = ps.aligned_40()
    assert out["branch_point_links_verified"] == "160/160"
