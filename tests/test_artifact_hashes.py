import pytest
import subprocess
import sys
from pathlib import Path

pytestmark = pytest.mark.archive  # requires the complete local archive (LICENSE_REVIEW inputs)


ROOT = Path(__file__).resolve().parents[1]


def test_copied_artifacts_are_byte_identical():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "verify_hashes.py")],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout
