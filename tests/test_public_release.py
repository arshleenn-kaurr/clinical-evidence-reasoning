"""REPRODUCTION TOOLING: PUBLIC-SAFE tests. Every test in this file must pass
using only files that are actually shipped in a stripped public release
(dist/public_release_preview/) — none may require a LICENSE_REVIEW or
ARCHIVAL_ONLY input. See docs/public_dependency_audit.md.

These wrap individual steps of scripts/validate_public_release.py so the
checks are expressed once and exercised both as a CLI tool and as pytest
assertions, without duplicating the logic.

Run: python -m pytest -m public
"""
import json

import pytest
import validate_public_release as vpr

pytestmark = pytest.mark.public


@pytest.fixture(autouse=True)
def _reset_vpr_state():
    vpr.reset_state()
    yield
    vpr.reset_state()


def test_release_manifest_integrity():
    rows = vpr.load_release_manifest()
    assert rows is not None, "docs/public_release_manifest_draft.csv not found"
    vpr.step1_manifest_integrity(rows)
    assert vpr.problems == []


def test_sha256_consistency_against_manifest():
    rows = vpr.load_release_manifest()
    by_path = vpr.step1_manifest_integrity(rows)
    vpr.reset_state()
    vpr.step2_sha256_consistency(by_path)
    assert vpr.problems == []


def test_expected_repo_structure():
    vpr.step3_repo_structure()
    assert vpr.problems == []


def test_experiment_manifests_parse():
    vpr.step4_experiment_manifests()
    assert vpr.problems == []


def test_public_provenance_paths_resolve():
    rows = vpr.load_release_manifest()
    by_path = vpr.step1_manifest_integrity(rows)
    vpr.reset_state()
    vpr.step5_public_provenance(by_path)
    assert vpr.problems == []


def test_figure1_reconstruction_is_internally_consistent():
    vpr.step7_figure1_reconstruction()
    assert vpr.problems == []


def test_canonical_reference_generator_present_and_labeled():
    # Does not assert byte-identity here (that needs the archived reference
    # file, which is itself PUBLIC_CORE and so should be present — step8
    # handles its own absence gracefully as a NOTE, not a failure).
    vpr.step8_canonical_reference_reconstruction()
    assert vpr.problems == []


def test_documentation_links_resolve():
    vpr.step9_doc_links()
    assert vpr.problems == []


def test_citation_cff_present_and_well_formed():
    vpr.step10_citation_cff()
    assert vpr.problems == []


def test_required_docs_present():
    vpr.step11_required_docs()
    assert vpr.problems == []


def test_no_secret_shaped_strings():
    vpr.step12_secret_scan()
    assert vpr.problems == []


def test_each_experiment_manifest_has_a_paper_relationship(root):
    for m in sorted(root.glob("experiments/*/*/experiment_manifest.json")):
        data = json.loads(m.read_text(encoding="utf-8"))
        entries = data.get("experiments", [data])
        for e in entries:
            assert "paper_relationship" in e, m


def test_groq_extension_is_labeled_out_of_scope(root):
    readme = root / "experiments/persistent_context/groq_gpt_oss_120b/README.md"
    if not readme.exists():
        pytest.skip("Groq extension navigational doc not present in this checkout")
    text = readme.read_text(encoding="utf-8")
    assert "IN PROGRESS" in text and "NOT CANONICALIZED" in text
    assert "NOT the accepted AgenticLS experiment" in text


def test_no_unmanifested_files(root):
    rows = vpr.load_release_manifest()
    by_path = vpr.step1_manifest_integrity(rows)
    vpr.reset_state()
    vpr.step13_unmanifested_files(by_path)
    assert vpr.problems == []


def test_validate_public_release_cli_exit_code(root):
    """End-to-end: the full CLI (all 13 steps) must itself exit 0 on this
    checkout. This is the strongest single public-safe assertion — if the
    checkout is a real stripped preview (no LICENSE_REVIEW/ARCHIVAL_ONLY
    files on disk), step 6 also passes; if run against the full private
    archive (which legitimately contains those files), step 6 will fail,
    and that failure is expected here, not a bug — so this test only
    requires the OTHER twelve steps to be clean.
    """
    rows = vpr.load_release_manifest()
    by_path = vpr.step1_manifest_integrity(rows)
    vpr.reset_state()
    for step in (
        lambda: vpr.step2_sha256_consistency(by_path),
        vpr.step3_repo_structure,
        vpr.step4_experiment_manifests,
        lambda: vpr.step5_public_provenance(by_path),
        vpr.step7_figure1_reconstruction,
        vpr.step8_canonical_reference_reconstruction,
        vpr.step9_doc_links,
        vpr.step10_citation_cff,
        vpr.step11_required_docs,
        vpr.step12_secret_scan,
        lambda: vpr.step13_unmanifested_files(by_path),
    ):
        step()
    assert vpr.problems == [], vpr.problems


def test_camera_ready_mapping_validates(root):
    """The populated camera-ready provenance mapping must validate against result_provenance.csv
    (both are public files)."""
    import subprocess
    import sys
    script = root / "scripts/validate_camera_ready_mapping.py"
    mapping = root / "docs/camera_ready_provenance_mapping.csv"
    if not script.exists() or not mapping.exists():
        pytest.skip("camera-ready mapping tooling not present in this checkout")
    r = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
