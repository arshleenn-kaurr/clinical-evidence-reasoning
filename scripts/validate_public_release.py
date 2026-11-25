#!/usr/bin/env python3
"""RELEASE TOOLING (not historical execution code).

PUBLIC RELEASE VALIDATION — the companion to scripts/validate_accepted_papers.py
(FULL ARCHIVAL REPRODUCTION). This script is designed to pass using ONLY files
that are actually distributed in a stripped public release
(dist/public_release_preview/, or any checkout built the same way): it never
requires a LICENSE_REVIEW or ARCHIVAL_ONLY input to exist.

It does NOT reproduce the accepted-paper scientific analyses — that requires
the frozen cohorts, prompts, and raw/canonical model outputs, which are
LICENSE_REVIEW and are intentionally excluded from the public release (see
docs/public_dependency_audit.md). What it DOES verify, using only public
files:

  1. public release manifest integrity (docs/public_release_manifest_draft.csv
     is well-formed; every tier is one of the 6 allowed values; no duplicate
     repo_path)
  2. source/copied SHA256 consistency, both within dist/.../MANIFEST.csv (if
     present) and between that manifest and the files actually on disk
  3. expected top-level repo structure
  4. every experiment_manifest.json parses as JSON
  5. public-safe result-provenance validation: docs/result_provenance.csv's
     schema, plus path-existence checks ONLY for columns whose target is
     itself public (per the release manifest); a path that resolves to a
     LICENSE_REVIEW/ARCHIVAL_ONLY file is expected to be absent and is not
     treated as a failure
  6. no LICENSE_REVIEW or ARCHIVAL_ONLY file is present under this checkout
     (i.e. nothing restricted leaked into what should be a stripped release)
  7. the reconstructed Figure 1 script exists and its declared source inputs
     are present and internally consistent; if matplotlib is importable, it
     is actually executed with its output redirected to a scratch temp
     directory (--out-dir), never writing into the checkout being validated
  8. the reconstructed canonical-reference generator exists, uses only the
     standard library, and — because its own inputs (posthoc CSVs, per-cohort
     flip_threshold.csv) are themselves PUBLIC_CORE/PUBLIC_OPTIONAL — is
     actually RE-RUN here (output redirected to a scratch temp file via
     --out, never written into the checkout) and compared byte-for-byte
     against the archived reference file
  9. internal documentation links (relative [text](path) references) resolve
  10. CITATION.cff is present and has the required top-level keys
  11. required README/docs exist
  12. no obvious secret-bearing content (API-key-shaped strings) is present
  13. no unmanifested/unclassified file is present: every ordinary file must
      either be a row in docs/public_release_manifest_draft.csv or belong to
      a narrowly documented allowlist of files generated at preview-build
      time (MANIFEST.csv, PREVIEW_ONLY.txt); .git/ and __pycache__/ etc. are
      never treated as release artifacts in the first place

This script, and everything it depends on, is itself classified PUBLIC_CORE
and ships inside the public release, so this command is always runnable by
anyone who only has the public artifact.

Usage: python scripts/validate_public_release.py
Exit code: 0 = public artifact internally valid, non-zero = a problem.
"""
import csv
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_CSV = ROOT / "docs/public_release_manifest_draft.csv"
PREVIEW_MANIFEST = ROOT / "MANIFEST.csv"  # present only when ROOT *is* a built preview
ALLOWED_TIERS = {"PUBLIC_CORE", "PUBLIC_OPTIONAL", "LICENSE_REVIEW", "ARCHIVAL_ONLY", "SCRATCH_IGNORE", "PUBLIC_RELEASE_PENDING_PERMISSION"}
SECRET_RE = re.compile(r"AIza[0-9A-Za-z_-]{20,}|gsk_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}")
# Local developer home-directory paths (macOS/Linux/Windows). Catches operational logs that leaked
# the machine username, not just API-key-shaped secrets.
LOCAL_PATH_RE = re.compile(r"/Users/[A-Za-z0-9_.-]+/|/home/[A-Za-z0-9_.-]+/|[Cc]:\\\\Users\\\\[A-Za-z0-9_.-]+\\\\")

problems = []
notes = []


def reset_state():
    """Test-only helper: clear accumulated problems/notes between step calls."""
    problems.clear()
    notes.clear()


def fail(msg):
    problems.append(msg)
    print(f"  FAIL: {msg}")


def ok(msg):
    print(f"  ok: {msg}")


def note(msg):
    notes.append(msg)
    print(f"  NOTE: {msg}")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def section(title):
    print(f"\n== {title} ==")


def load_release_manifest():
    if not MANIFEST_CSV.exists():
        return None
    with open(MANIFEST_CSV, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def step1_manifest_integrity(rows):
    section("Step 1: public release manifest integrity")
    if rows is None:
        fail(f"{MANIFEST_CSV.relative_to(ROOT)} not found — cannot validate the release manifest")
        return {}
    seen = set()
    by_path = {}
    for r in rows:
        if r["tier"] not in ALLOWED_TIERS:
            fail(f"invalid tier '{r['tier']}' for {r['repo_path']}")
        if r["repo_path"] in seen:
            fail(f"duplicate repo_path in manifest: {r['repo_path']}")
        seen.add(r["repo_path"])
        by_path[r["repo_path"]] = r
        if (r["tier"] != "SCRATCH_IGNORE" and not r["source_sha256"]
                and r["repo_path"] != "docs/public_release_manifest_draft.csv"):
            # The manifest's own row is the one documented exception: it
            # cannot record its own post-write hash (see
            # scripts/build_public_release_manifest.py).
            fail(f"missing source_sha256 for non-ignored file: {r['repo_path']}")
    if not problems:
        ok(f"{len(rows)} rows, all tiers valid, no duplicates")
    return by_path


# Artifacts this validator itself regenerates in step7/step8 (matplotlib PDFs
# embed a CreationDate, so the figure files are not byte-stable across runs).
# Their *content validity* is checked by those steps (script succeeds, output
# written, and for the canonical reference, byte-identity to the archive);
# excluding them here avoids a false "drift" failure caused by running this
# very validator.
NON_DETERMINISTIC_REGENERATED_PREFIXES = ("validation/reconstructed_figures/",)
# Cannot record its own post-write hash (see build_public_release_manifest.py).
SELF_REFERENTIAL_PATHS = ("docs/public_release_manifest_draft.csv",)


def step2_sha256_consistency(by_path):
    section("Step 2: source/copied SHA256 consistency")
    if PREVIEW_MANIFEST.exists():
        with open(PREVIEW_MANIFEST, newline="", encoding="utf-8") as fh:
            prows = list(csv.DictReader(fh))
        mism = [r for r in prows if r["match"] != "TRUE"]
        if mism:
            for m in mism:
                fail(f"preview MANIFEST.csv records a mismatch: {m['public_path']}")
        else:
            ok(f"{len(prows)} entries in {PREVIEW_MANIFEST.name}, all match=TRUE")
        drift = skipped = 0
        for r in prows:
            if r["public_path"].startswith(NON_DETERMINISTIC_REGENERATED_PREFIXES):
                skipped += 1
                continue
            p = ROOT / r["public_path"]
            if p.exists() and sha(p) != r["copied_sha256"]:
                fail(f"on-disk file no longer matches MANIFEST.csv copied_sha256: {r['public_path']}")
                drift += 1
        if not drift:
            ok(f"no drift between MANIFEST.csv and files on disk ({skipped} non-deterministic regenerated file(s) excluded)")
    else:
        note(f"{PREVIEW_MANIFEST.name} not found at repo root (expected only inside a built "
            "dist/public_release_preview/ checkout) — checking against docs/public_release_manifest_draft.csv instead")
        checked = mismatches = 0
        for rel, r in by_path.items():
            if r["tier"] not in ("PUBLIC_CORE", "PUBLIC_OPTIONAL"):
                continue
            if rel.startswith(NON_DETERMINISTIC_REGENERATED_PREFIXES) or rel in SELF_REFERENTIAL_PATHS:
                continue
            p = ROOT / rel
            if not p.exists():
                continue  # covered by step 6 / informational only here
            checked += 1
            if sha(p) != r["source_sha256"]:
                mismatches += 1
                fail(f"file hash differs from public_release_manifest_draft.csv: {rel}")
        if not mismatches:
            ok(f"{checked} public files checked against the manifest's recorded source_sha256, 0 mismatches")


def step3_repo_structure():
    section("Step 3: expected repo structure")
    expected = ["README.md", "LICENSE", "CITATION.cff", "pyproject.toml", "docs", "scripts",
                "tests", "experiments", "papers", "data", "artifacts"]
    missing = [e for e in expected if not (ROOT / e).exists()]
    if missing:
        fail(f"missing expected top-level entries: {missing}")
    else:
        ok(f"all {len(expected)} expected top-level entries present")


def step4_experiment_manifests():
    section("Step 4: experiment manifests parse correctly")
    manifests = sorted(ROOT.glob("experiments/*/*/experiment_manifest.json"))
    if not manifests:
        fail("no experiment_manifest.json files found under experiments/*/*/")
        return
    bad = 0
    for m in manifests:
        try:
            json.loads(m.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            fail(f"{m.relative_to(ROOT)} does not parse as JSON: {e}")
            bad += 1
    if not bad:
        ok(f"{len(manifests)} experiment_manifest.json files parse")


def step5_public_provenance(by_path):
    section("Step 5: public-safe result-provenance validation")
    csv_path = ROOT / "docs/result_provenance.csv"
    if not csv_path.exists():
        fail(f"{csv_path.relative_to(ROOT)} not found")
        return
    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        header = reader.fieldnames or []
        rows = list(reader)
    required = ["paper", "result_id", "description", "experiment", "source_cohort", "source_raw_file",
                "source_canonical_file", "analysis_script", "analysis_output", "protocol",
                "prespecified_or_posthoc", "reproduced_status", "value", "notes"]
    missing_cols = [c for c in required if c not in header]
    if missing_cols:
        fail(f"result_provenance.csv missing columns: {missing_cols}")
    ids = [r["result_id"] for r in rows]
    if len(ids) != len(set(ids)):
        fail("result_provenance.csv has duplicate result_id values")

    public_target_cols = ["analysis_script", "analysis_output", "protocol"]
    restricted_target_cols = ["source_cohort", "source_raw_file", "source_canonical_file"]
    public_path_problems = 0
    unexpectedly_missing_restricted = 0
    for i, row in enumerate(rows, start=2):
        for col in public_target_cols:
            val = row.get(col, "")
            for part in val.split(";"):
                p = part.strip().split(" (")[0]
                if not p or "/" not in p:
                    continue
                if not (ROOT / p).exists():
                    # Only a problem if the manifest says this file SHOULD be public.
                    tier = by_path.get(p, {}).get("tier")
                    if tier in ("PUBLIC_CORE", "PUBLIC_OPTIONAL") or tier is None:
                        fail(f"result_provenance.csv row {i} ({row['result_id']}): {col} missing public file '{p}'")
                        public_path_problems += 1
        for col in restricted_target_cols:
            val = row.get(col, "")
            for part in val.split(";"):
                p = part.strip().split(" (")[0]
                if not p or "/" not in p:
                    continue
                tier = by_path.get(p, {}).get("tier")
                if tier in ("PUBLIC_CORE", "PUBLIC_OPTIONAL") and not (ROOT / p).exists():
                    # Manifest claims this is public but it's missing: a real problem.
                    fail(f"result_provenance.csv row {i} ({row['result_id']}): {col} ('{p}') is classified public but missing")
                    public_path_problems += 1
                elif tier in ("LICENSE_REVIEW", "ARCHIVAL_ONLY") and not (ROOT / p).exists():
                    pass  # expected: restricted source, correctly excluded from a public checkout
    if not public_path_problems:
        ok(f"{len(rows)} rows; {len(ids)} unique result_id; all public-targeted path references resolve; "
          "restricted source_cohort/source_raw_file/source_canonical_file references are correctly absent")


def step6_no_restricted_files_present(by_path):
    section("Step 6: no LICENSE_REVIEW / ARCHIVAL_ONLY / PUBLIC_RELEASE_PENDING_PERMISSION file is present")
    leaked = []
    for rel, r in by_path.items():
        if r["tier"] in ("LICENSE_REVIEW", "ARCHIVAL_ONLY", "PUBLIC_RELEASE_PENDING_PERMISSION") and (ROOT / rel).exists():
            leaked.append((rel, r["tier"]))
    if leaked:
        for rel, tier in leaked:
            fail(f"{tier} file is present in this checkout: {rel}")
    else:
        ok("no LICENSE_REVIEW, ARCHIVAL_ONLY or PUBLIC_RELEASE_PENDING_PERMISSION file found on disk")
    if not PREVIEW_MANIFEST.exists():
        note("MANIFEST.csv not found at repo root, so this does not look like a built preview checkout — "
            "this step only confirms docs/public_release_manifest_draft.csv and disk agree here; it does "
            "NOT by itself prove a dist/public_release_preview/ build would be clean (run "
            "scripts/build_public_release.py and re-run this script from inside that directory for that)")


def step7_figure1_reconstruction():
    section("Step 7: Figure 1 reconstruction consistency")
    script = ROOT / "scripts/reconstructed/plot_genai4health_figure1.py"
    doc = ROOT / "docs/figure1_reconstruction.md"
    if not script.exists():
        fail(f"{script.relative_to(ROOT)} not found")
        return
    if not doc.exists():
        fail(f"{doc.relative_to(ROOT)} not found")
    else:
        text = doc.read_text(encoding="utf-8")
        if "DATA_EXACT / PLOT_RECONSTRUCTED" not in text:
            fail("docs/figure1_reconstruction.md does not state the expected status DATA_EXACT / PLOT_RECONSTRUCTED")
        if "RECONSTRUCTED" not in script.read_text(encoding="utf-8"):
            fail("plot_genai4health_figure1.py does not self-label as RECONSTRUCTED")
    posthoc_csvs = ["binomial_proportions_exact.csv", "confidence_contrasts_bootstrap.csv", "confidence_direction_counts.csv"]
    posthoc_dir = ROOT / "experiments/static_conflict/historical_package/evidence_not_vote_starter/analysis/posthoc_contrasts"
    missing_inputs = [c for c in posthoc_csvs if not (posthoc_dir / c).exists()]
    if missing_inputs:
        fail(f"Figure 1 reconstruction's declared source inputs are missing: {missing_inputs}")
        return
    ok("script + doc present, self-labeled RECONSTRUCTED, declared source CSVs present")
    if importlib.util.find_spec("matplotlib") is None:
        note("matplotlib not installed — skipping execution check (file/input consistency already verified)")
        return
    # Write into a scratch temp directory, NOT validation/reconstructed_figures/ inside the
    # checkout, so running this validator never modifies the checkout it is validating.
    with tempfile.TemporaryDirectory(prefix="validate_public_release_fig1_") as td:
        out_dir = Path(td)
        proc = subprocess.run([sys.executable, "-B", str(script), "--out-dir", str(out_dir)],
                              cwd=ROOT, capture_output=True, text=True)
        if proc.returncode != 0:
            fail(f"plot_genai4health_figure1.py exited {proc.returncode}: {proc.stderr[-500:]}")
        else:
            out_png = out_dir / "figure1_decision_confidence_dissociation_RECONSTRUCTED.png"
            if out_png.exists():
                ok(f"executed successfully into a scratch temp dir (checkout untouched): {out_png.name}")
            else:
                fail("script exited 0 but did not write the expected output PNG")


def step8_canonical_reference_reconstruction():
    section("Step 8: canonical-reference reconstruction (re-run and compare)")
    script = ROOT / "scripts/reconstructed/build_canonical_results_reference.py"
    archived = ROOT / "experiments/static_conflict/historical_package/evidence_not_vote_starter/analysis/canonical_results_reference.md"
    if not script.exists():
        fail(f"{script.relative_to(ROOT)} not found")
        return
    if "RECONSTRUCTED" not in script.read_text(encoding="utf-8"):
        fail("build_canonical_results_reference.py does not self-label as RECONSTRUCTED")
    if not archived.exists():
        note("archived canonical_results_reference.md not present in this checkout (expected if it was not "
            "classified public) — skipping byte-identity re-check; file/label presence already verified")
        return
    # Write into a scratch temp file, NOT validation/reconstructed_reference/ inside the
    # checkout, so running this validator never modifies the checkout it is validating.
    with tempfile.TemporaryDirectory(prefix="validate_public_release_ref_") as td:
        regenerated = Path(td) / "canonical_results_reference.md"
        proc = subprocess.run([sys.executable, "-B", str(script), "--out", str(regenerated)],
                              cwd=ROOT, capture_output=True, text=True)
        if proc.returncode != 0:
            fail(f"build_canonical_results_reference.py exited {proc.returncode}: {proc.stderr[-500:]}")
            return
        if not regenerated.exists():
            fail("script exited 0 but did not write the expected output file")
            return
        if sha(regenerated) == sha(archived):
            ok("re-ran the reconstructed generator into a scratch temp dir (stdlib only, checkout "
              "untouched) — output is BYTE-IDENTICAL to the archive")
        else:
            fail("reconstructed canonical_results_reference.md output no longer matches the archive")


def step9_doc_links():
    section("Step 9: internal documentation links resolve")
    checked = broken = 0
    for md in ROOT.rglob("*.md"):
        if "historical_package" in md.parts or ".venv" in str(md) or "scratch" in md.parts:
            continue
        text = md.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r"\[([^\]]*)\]\(([^)]+)\)", text):
            link = m.group(2)
            if link.startswith(("http://", "https://", "mailto:")):
                continue
            link_path = link.split("#")[0]
            if not link_path:
                continue
            checked += 1
            resolved = (md.parent / link_path).resolve()
            if not resolved.exists():
                broken += 1
                fail(f"{md.relative_to(ROOT)}: broken link -> {link}")
    if not broken:
        ok(f"{checked} relative links checked, 0 broken")


def step10_citation_cff():
    section("Step 10: CITATION.cff")
    p = ROOT / "CITATION.cff"
    if not p.exists():
        note("CITATION.cff not present (optional per instructions if absent)")
        return
    text = p.read_text(encoding="utf-8")
    required_keys = ["cff-version:", "title:", "authors:"]
    missing = [k for k in required_keys if k not in text]
    if missing:
        fail(f"CITATION.cff missing expected keys: {missing}")
        return
    if importlib.util.find_spec("yaml") is not None:
        import yaml
        try:
            data = yaml.safe_load(text)
            assert isinstance(data, dict) and "cff-version" in data
            ok("CITATION.cff present and parses as valid YAML with required keys")
        except Exception as e:
            fail(f"CITATION.cff present but failed to parse as YAML: {e}")
    else:
        note("pyyaml not installed — did a textual key check only (found cff-version/title/authors)")
        ok("CITATION.cff present with required keys (textual check)")


def step11_required_docs():
    section("Step 11: required README/docs exist")
    required = [
        "README.md", "LICENSE", "docs/reproducibility.md", "docs/reproducibility_levels.md",
        "docs/limitations.md", "docs/public_release_audit.md", "docs/public_artifact_plan.md",
        "docs/reproduction_environment.md", "docs/result_provenance.csv",
        "docs/public_release_manifest_draft.csv", "docs/public_dependency_audit.md",
        "docs/phase4_1_public_validation_report.md",
        "papers/genai4health/README.md", "papers/genai4health/reproduce.md",
        "papers/agenticls/README.md", "papers/agenticls/reproduce.md",
    ]
    missing = [r for r in required if not (ROOT / r).exists()]
    if missing:
        fail(f"missing required docs: {missing}")
    else:
        ok(f"all {len(required)} required docs present")


# Generated at preview-build time by scripts/build_public_release.py itself,
# so these two root-level files legitimately have no row in
# docs/public_release_manifest_draft.csv (which classifies files in the
# FULL repo, before a preview is ever built). Nothing else is allowlisted:
# any other file that is not a manifest row is treated as unexpected.
RUNTIME_GENERATED_ALLOWLIST = {"MANIFEST.csv", "PREVIEW_ONLY.txt"}


def step13_unmanifested_files(by_path):
    section("Step 13: no unmanifested/unclassified file is present")
    import build_public_release_manifest as bprm  # reuse the same ignore rules, not a second definition
    unexpected = []
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        parts = set(p.relative_to(ROOT).parts)
        if parts & bprm.IGNORE_DIR_NAMES:
            continue  # .git, __pycache__, .pytest_cache, dist — never release artifacts
        rel = str(p.relative_to(ROOT))
        if any(rel.startswith(pfx) for pfx in bprm.IGNORE_PATH_PREFIXES):
            continue  # validation/scratch/, .venv*/, _orchestrator_scratch/ — local-only, gitignored
        if rel in RUNTIME_GENERATED_ALLOWLIST and p.parent == ROOT:
            continue
        if rel not in by_path:
            unexpected.append(rel)
    if unexpected:
        for rel in unexpected:
            fail(f"unmanifested file present (not in docs/public_release_manifest_draft.csv, not in "
                f"the documented allowlist {sorted(RUNTIME_GENERATED_ALLOWLIST)}): {rel}")
    else:
        ok(f"every file present is either a release-manifest row or in the documented runtime allowlist "
          f"{sorted(RUNTIME_GENERATED_ALLOWLIST)}")


def step12_secret_scan():
    section("Step 12: no obvious secret-bearing content")
    import build_public_release_manifest as bprm  # same ignore rules as step 13
    secret_hits, path_hits = [], []
    for p in ROOT.rglob("*"):
        if not p.is_file() or p.suffix in (".pyc",) or ".git" in p.parts:
            continue
        if set(p.relative_to(ROOT).parts) & bprm.IGNORE_DIR_NAMES:
            continue  # .venv (CI creates it in the checkout), __pycache__, .pytest_cache, dist: not release artifacts
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if SECRET_RE.search(text):
            secret_hits.append(str(p.relative_to(ROOT)))
        m = LOCAL_PATH_RE.search(text)
        if m:
            path_hits.append((str(p.relative_to(ROOT)), m.group(0)))
    if secret_hits:
        for h in secret_hits:
            fail(f"possible secret-shaped string found in {h}")
    else:
        ok("no API-key-shaped strings found")
    if path_hits:
        for h, frag in path_hits:
            fail(f"local developer home-directory path found in {h} (e.g. '{frag}')")
    else:
        ok("no local developer home-directory paths found")


def main():
    print(f"validate_public_release.py — scope: {ROOT}")
    rows = load_release_manifest()
    by_path = step1_manifest_integrity(rows)
    step2_sha256_consistency(by_path)
    step3_repo_structure()
    step4_experiment_manifests()
    step5_public_provenance(by_path)
    step6_no_restricted_files_present(by_path)
    step7_figure1_reconstruction()
    step8_canonical_reference_reconstruction()
    step9_doc_links()
    step10_citation_cff()
    step11_required_docs()
    step12_secret_scan()
    step13_unmanifested_files(by_path)

    print("\n" + "=" * 60)
    print("VALIDATE PUBLIC RELEASE — SUMMARY")
    print("=" * 60)
    if notes:
        print(f"{len(notes)} note(s) (not failures):")
        for n in notes:
            print(f"  - {n}")
    print(f"OVERALL: {'PASS' if not problems else 'FAIL'} ({len(problems)} problem(s))")
    print("This validates the PUBLIC artifact only. It does NOT reproduce the")
    print("accepted-paper scientific analyses — that requires the full archive")
    print("(python scripts/validate_accepted_papers.py); see docs/public_dependency_audit.md.")
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
