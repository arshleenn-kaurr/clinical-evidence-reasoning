#!/usr/bin/env python3
"""RELEASE TOOLING (not historical execution code).

Classifies every PUBLIC_CORE / PUBLIC_OPTIONAL file (from
docs/public_release_manifest_draft.csv) into:
  V1_CORE | V1_SUPPORTING | DEFER_FROM_V1

This does NOT touch LICENSE_REVIEW / ARCHIVAL_ONLY / SCRATCH_IGNORE files —
those are already excluded from any public build regardless of V1 scope.
DEFER_FROM_V1 means "not in the first public release," not "never public" —
nothing is deleted from the archival repo either way.

Writes docs/public_v1_scope.csv. The narrative companion
docs/public_v1_scope.md is written separately (not regenerated here) since
it explains the reasoning in prose.

Used by scripts/build_public_release.py --v1-core.
"""
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/public_release_manifest_draft.csv"
OUT = ROOT / "docs/public_v1_scope.csv"

# Ordered (regex on repo_path, scope, reason). First match wins.
RULES = [
    # --- Defer: redundant reproduction-run duplicates (the compact
    # comparison JSONs that summarize these ARE kept; the full per-cohort
    # regenerated CSV dumps are the redundant intermediate).
    (r"^validation/genai4health/prespecified/", "DEFER_FROM_V1",
     "Redundant analysis intermediate: a full regenerated copy of outputs already archived in experiments/.../analysis/; the compact prespecified_comparison.json (kept, V1_SUPPORTING) already reports EXACT_MATCH for all of these."),
    (r"^validation/genai4health/posthoc/", "DEFER_FROM_V1",
     "Redundant analysis intermediate: regenerated copy of archived analysis/posthoc_contrasts/ outputs; posthoc_comparison.json (kept) already reports the result."),
    (r"^validation/genai4health/posthoc_scipy1\.16\.3/", "DEFER_FROM_V1",
     "Redundant sensitivity-check intermediate; the finding (EXACT_MATCH under scipy 1.16.3) is reported in docs/posthoc_hash_investigation.md (kept)."),
    (r"^validation/genai4health/posthoc_py312_scipy1\.16\.3/", "DEFER_FROM_V1",
     "Redundant sensitivity-check intermediate (duplicate of the scipy1.16.3 check under a different interpreter); finding already reported in docs."),
    (r"^validation/logs/", "DEFER_FROM_V1", "Stale operational logs (exact commands/timestamps of past reproduction runs); superseded by the reports that summarize them."),
    (r"^validation/public_preview_validation/logs/", "DEFER_FROM_V1", "Operational logs of validating the preview itself; superseded by this phase's own report."),

    # --- Defer: dev/smoke-only material (operational, not reported results).
    (r"/analysis/dev_gpt_oss_120b(_v2)?/", "DEFER_FROM_V1", "Low-value dev/smoke scoring output, superseded by the real GPT-OSS primary/veto results."),
    (r"/DRY_RUN_PREVIEW\.txt$", "DEFER_FROM_V1", "Pure operational dry-run output (no API calls, no reported result)."),

    # --- Defer: superseded/excluded latent-v1 code (data already ARCHIVAL_ONLY; this covers the remaining public code/manifest fragments).
    (r"/make_latent_ablation\.py$", "DEFER_FROM_V1", "Builder for latent v1, STATUS: SUPERSEDED / EXCLUDED FROM REPORTED ANALYSES (see experiments/static_conflict/latent_v2/README.md)."),
    (r"/data/latent_ablation_lock\.sha256$", "DEFER_FROM_V1", "Lock file for latent v1 (superseded/excluded)."),
    (r"/analysis/latent_gemini/", "DEFER_FROM_V1", "Latent v1 scoring output (superseded/excluded); not reached (latent v1 analysis files are already ARCHIVAL_ONLY, this rule is defensive)."),

    # --- Defer: internal migration/recovery bookkeeping, not needed to understand or reproduce the papers.
    (r"^docs/source_inventory\.(csv|md)$", "DEFER_FROM_V1", "Internal Phase 1/2 recovery bookkeeping (every file originally found, with confidence/notes); large, not needed to use or reproduce the papers."),
    (r"^docs/copied_artifact_hashes\.csv$", "DEFER_FROM_V1", "Internal Phase 1/2 migration-copy hash ledger; superseded by docs/public_release_manifest_draft.csv for release purposes."),
    (r"^docs/migration_plan\.md$", "DEFER_FROM_V1", "Internal Phase 1/2 migration narrative (how files were moved into this repo layout); historical process detail, not science."),

    # --- Defer: not-yet-implemented placeholders.
    (r"^src/clinical_evidence/", "DEFER_FROM_V1", "Placeholder package stubs, explicitly 'not yet implemented'; no functional content to ship yet."),
    (r"^scripts/canonicalize_results\.py$", "DEFER_FROM_V1", "Stub that intentionally refuses to run (no canonicalization rule chosen yet); minor, deferrable."),

    # --- V1_SUPPORTING: secondary provenance detail, real content, not core narrative.
    (r"^docs/(hash_verification_report|canonical_structure_report|genai4health_prespecified_reproduction|environment_validation|phase3_reproduction_report|phase4_release_readiness_report|phase4_1_public_validation_report)\.md$", "V1_SUPPORTING",
     "Phase progress/audit report: real provenance detail, but secondary to the top-level documentation for a first-time public reader."),
    (r"^docs/recovery_status\.md$", "V1_SUPPORTING", "Compact per-experiment status table; useful secondary reference."),
    (r"^validation/(README\.md|hash_verification_report\.json|canonical_structure_report\.json|diffs/|agenticls/|genai4health/(posthoc_comparison|prespecified_comparison|figure1_data_from_reproduced_outputs)\.|reconstructed_figures/|reconstructed_reference/|public_preview_validation/README\.md)", "V1_SUPPORTING",
     "Compact machine-readable reproduction evidence or the reconstructed-artifact outputs themselves."),
    (r"/results/.*_terminal\.log$", "V1_SUPPORTING", "Small execution-order log documenting the reported arm-order balance (e.g. 130/130)."),
    (r"experiments/persistent_context/groq_gpt_oss_120b/(README\.md|PROVENANCE\.md|CONFIG_NOTE\.md|experiment_manifest\.json)$", "V1_SUPPORTING",
     "Navigational labeling for the out-of-scope Groq extension; kept visible so the boundary is clear, but not core science of either paper."),
    (r"^(data|artifacts)/.*(README\.md|_registry\.csv|_index\.csv)$", "V1_SUPPORTING", "Useful cross-package index/registry, small."),
    (r"^artifacts/README\.md$|^papers/README\.md$", "V1_SUPPORTING", "Navigational doc."),

    # --- Everything else that is PUBLIC_CORE/PUBLIC_OPTIONAL and reaches here is V1_CORE.
]
FALLBACK = ("V1_CORE", "Root docs, protocols, frozen runners/analysis code, reported analysis outputs, "
            "experiment manifests, reproduction/release tooling, CI, and public-safe tests: the core of a "
            "professional, reproducible research artifact.")


def classify(rel):
    for pattern, scope, reason in RULES:
        if re.search(pattern, rel):
            return scope, reason
    return FALLBACK


def main():
    with open(MANIFEST, newline="", encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh) if r["tier"] in ("PUBLIC_CORE", "PUBLIC_OPTIONAL")]

    out_rows = []
    for r in rows:
        scope, reason = classify(r["repo_path"])
        out_rows.append({"repo_path": r["repo_path"], "tier": r["tier"], "v1_scope": scope,
                         "reason": reason, "source_sha256": r["source_sha256"]})

    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["repo_path", "tier", "v1_scope", "reason", "source_sha256"])
        w.writeheader()
        w.writerows(out_rows)

    from collections import Counter
    c = Counter(r["v1_scope"] for r in out_rows)
    print(f"{len(out_rows)} public-eligible files classified -> {OUT.relative_to(ROOT)}")
    for k in ("V1_CORE", "V1_SUPPORTING", "DEFER_FROM_V1"):
        print(f"  {k}: {c.get(k, 0)}")


if __name__ == "__main__":
    main()
