"""REPRODUCTION TOOLING (test fixtures), not historical execution code."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

S = ROOT / "experiments/static_conflict/historical_package/evidence_not_vote_starter"
G = ROOT / "experiments/persistent_context/gemini_persistent_260/historical_package/agenticls_gemini_sequential"
A = ROOT / "experiments/persistent_context/gemini_aligned_control_40/historical_package/agenticls_aligned_persistent_control"


def load_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


@pytest.fixture(scope="session")
def root():
    return ROOT


@pytest.fixture(scope="session")
def static_pkg():
    return S


@pytest.fixture(scope="session")
def gemini_pkg():
    return G


@pytest.fixture(scope="session")
def aligned_pkg():
    return A
