#!/usr/bin/env python3
"""RELEASE TOOLING (not historical execution code).

Groups the 64 `LICENSE_REVIEW` rows in docs/public_release_manifest_draft.csv
into artifact-type families and writes a licensing decision matrix. Makes NO
legal conclusions — every "contains X-derived material?" flag is a factual
observation about file provenance (as already documented in
docs/public_release_audit.md and docs/data_provenance.md), not a licensing
determination. "Redistribution concern" and "recommended disposition" use
"requires redistribution-rights review" language, never "illegal to publish"
or similar.

Writes docs/licensing_decision_matrix.csv and (from the same rows)
docs/licensing_decision_matrix.md is written separately by hand as a
narrative companion (not regenerated here) since it also records qualitative
reasoning that doesn't belong in a CSV.

Disposition options: PUBLIC_IF_CLEARED, RELEASE_DERIVED_ONLY,
RELEASE_HASH_ONLY, RELEASE_RECONSTRUCTION_SCRIPT_ONLY, ARCHIVE_ONLY, UNKNOWN.
"""
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/public_release_manifest_draft.csv"
OUT = ROOT / "docs/licensing_decision_matrix.csv"

# (regex on repo_path, group fields). First match wins. Patterns target the
# basename / path shape, not a specific package, so static + persistent-
# context copies of the same artifact family collapse into one row.
GROUPS = [
    (r"data/QA-systematic-review\.jsonl$", dict(
        artifact_type="raw_source_dataset", upstream_source="MEDAL (Cochrane systematic-review QA extract)",
        medal=True, cochrane=True, aha=False, provider_output=False, synthetic_only=False,
        redistribution_concern="Raw third-party dataset export; MEDAL's own redistribution terms, and Cochrane's underlying terms, are not recorded in the recovered package and require redistribution-rights review.",
        public_value="High: this is the ultimate source of the main cohort; without it, provenance cannot be independently re-verified.",
        min_substitute="SHA256 (already public, matches freeze manifests) + row/field schema + manifest entry.",
        disposition="UNKNOWN", confidence="medium",
        action="Locate and review the MEDAL dataset's own license/terms of use (not found in the recovered package); confirm whether Cochrane permits this derived-QA redistribution.")),
    (r"data/recommendation-aha-guideline-clean\.jsonl$", dict(
        artifact_type="raw_source_dataset", upstream_source="MEDAL (AHA/Red Cross first-aid guideline recommendations)",
        medal=True, cochrane=False, aha=True, provider_output=False, synthetic_only=False,
        redistribution_concern="Verbatim guideline recommendation text and source PDF filenames; AHA copyright and MEDAL's redistribution terms require review.",
        public_value="Medium: supports the veto/boundary cohort's provenance.",
        min_substitute="SHA256 + row/field schema + per-record COR/LOE/id without recommendation text.",
        disposition="UNKNOWN", confidence="medium",
        action="Review AHA copyright terms for guideline recommendation text and MEDAL's redistribution terms.")),
    (r"data/(cochrane_candidates|replication_candidates)(_audited|\.pre_audit)?\.csv$", dict(
        artifact_type="candidate_audit_csv", upstream_source="MEDAL/Cochrane, filtered + author audit fields added",
        medal=True, cochrane=True, aha=False, provider_output=False, synthetic_only=False,
        redistribution_concern="Contains Cochrane source notes (effect estimates, certainty) plus author-written audit fields; same Cochrane/MEDAL review as the raw source applies.",
        public_value="Medium: shows the audit/selection process (prepare_cases.py, freeze_cases.py) but duplicates data/QA-systematic-review.jsonl content.",
        min_substitute="SHA256 + row counts per audit decision (eligible/excluded) + the audit_note taxonomy (already in audit_protocol.md, which IS public) without the Cochrane notes column.",
        disposition="UNKNOWN", confidence="medium",
        action="Same MEDAL/Cochrane review as the raw source; if cleared, the audit-only derived columns (eligible, audit_note) without the Cochrane notes text could be a lower-risk release-derived substitute.")),
    (r"data/aha_veto_candidates\.csv$", dict(
        artifact_type="candidate_audit_csv", upstream_source="MEDAL/AHA, filtered + author audit fields added",
        medal=True, cochrane=False, aha=True, provider_output=False, synthetic_only=False,
        redistribution_concern="Embeds AHA guideline text plus audit fields.",
        public_value="Medium.", min_substitute="SHA256 + audit-decision counts + veto_subtype taxonomy without the recommendation text.",
        disposition="UNKNOWN", confidence="medium",
        action="Same AHA/MEDAL review as the raw source.")),
    (r"data/latent_v2_anchor_audit\.csv$", dict(
        artifact_type="candidate_audit_csv", upstream_source="MEDAL/Cochrane, audit fields for latent-anchor sensitivity construction",
        medal=True, cochrane=True, aha=False, provider_output=False, synthetic_only=False,
        redistribution_concern="Embeds Cochrane-derived anchor/source text.",
        public_value="Low-medium: sensitivity-analysis input only.",
        min_substitute="SHA256 + row count + construction method description (already in make_latent_v2.py, which IS public).",
        disposition="UNKNOWN", confidence="medium", action="Same Cochrane/MEDAL review as the raw source.")),
    (r"example_audited_case\.jsonl$", dict(
        artifact_type="illustrative_example", upstream_source="MEDAL/Cochrane, one illustrative record",
        medal=True, cochrane=True, aha=False, provider_output=False, synthetic_only=False,
        redistribution_concern="Single Cochrane-derived example record; same review as the raw source applies even at n=1.",
        public_value="Low: illustrative only, not used by any pipeline.",
        min_substitute="A NEW project-authored synthetic example with the same field shape (not a transformed real record) — see docs/restricted_artifact_substitutes.md.",
        disposition="RELEASE_RECONSTRUCTION_SCRIPT_ONLY", confidence="high",
        action="If a worked example is wanted for documentation, author a new synthetic one; do not transform this real record.")),
    (r"(data/(dev|final_main|final_veto|replication)_cases\.jsonl|dev_cases\.jsonl|replication_cases_verified\.jsonl|aligned_control_cases_40\.jsonl)$", dict(
        artifact_type="frozen_cohort", upstream_source="MEDAL/Cochrane + MEDAL/AHA, anonymized, audited, frozen",
        medal=True, cochrane=True, aha=True, provider_output=False, synthetic_only=False,
        redistribution_concern="Questions are anonymized (\"Intervention A/B\") but anchor text paraphrases Cochrane/AHA findings, including reported effect estimates in some rows; downstream of the same MEDAL/Cochrane/AHA review.",
        public_value="High: these are the actual experimental units referenced by every result in docs/result_provenance.csv.",
        min_substitute="SHA256 (already public and matches every freeze manifest) + per-stratum counts + case_id list without anchor/question text.",
        disposition="UNKNOWN", confidence="medium",
        action="Core redistribution-rights question for this whole program: whether an anonymized, paraphrased derivative of Cochrane/AHA findings may be redistributed as a benchmark. Likely the single highest-value item to clear.")),
    (r"(data/.*prompts.*\.jsonl|dev_prompts\.jsonl)$", dict(
        artifact_type="generated_prompt", upstream_source="Project-authored template (prompt_template.md, PUBLIC) + frozen cohort text",
        medal=True, cochrane=True, aha=True, provider_output=False, synthetic_only=False,
        redistribution_concern="The template and synthetic lower-tier cards are project-authored and already effectively public (prompt_template.md, the runner source), but each prompt also embeds the cohort's anchor/question text, so the same cohort review applies.",
        public_value="Medium: the template structure is already public; the embedded cohort text is the restricted part.",
        min_substitute="prompt_template.md (already public) + response_schema.json (already public) + condition/prompt_id list without cohort text.",
        disposition="UNKNOWN", confidence="medium", action="Resolves automatically once the frozen-cohort question above is resolved.")),
    (r"results/.*\.jsonl$", dict(
        artifact_type="model_output", upstream_source="Gemini / GPT-OSS-120B (via Groq) provider responses to the above prompts",
        medal=True, cochrane=True, aha=True, provider_output=True, synthetic_only=False,
        redistribution_concern="Model rationale text may restate or summarize cohort content; separately, Google's and Groq's own terms on redistributing model outputs are not reviewed.",
        public_value="High for the canonical/clean accepted-paper files (these ARE the scientific record); lower for dev/smoke/checkpoint/backup variants.",
        min_substitute="Already public: decision/confidence/dominant_evidence_ids-only derived tables (merged_scored_results.csv minus rationale/raw_text) and docs/result_provenance.csv's aggregate values.",
        disposition="UNKNOWN", confidence="medium",
        action="Two separate reviews: (1) provider terms of service for Gemini and Groq outputs, (2) whether rationale text restates restricted cohort content closely enough to inherit its status.")),
    (r"analysis/.*/merged_scored_results\.csv$", dict(
        artifact_type="derived_analysis_table", upstream_source="score_results.py output: cohort + model-output join",
        medal=True, cochrane=True, aha=True, provider_output=True, synthetic_only=False,
        redistribution_concern="Full per-row join of case text, prompt, decision, confidence and rationale; inherits both the cohort and the model-output review above.",
        public_value="Medium: useful for independent per-case auditing, but the binomial/bootstrap summary CSVs already public cover the reported statistics.",
        min_substitute="Already public: accuracy_by_condition.csv, evidence_dilution_rate.csv, order_sensitivity.csv, veto_failure_rate.csv, aligned_control.csv, confidence_shift.csv, flip_threshold.csv (all PUBLIC_OPTIONAL) carry the aggregate numbers without per-row case text.",
        disposition="RELEASE_DERIVED_ONLY", confidence="high",
        action="Keep archive-only; the per-cohort aggregate CSVs already shipped are the public substitute.")),
]
FALLBACK = dict(artifact_type="unclassified", upstream_source="unknown", medal=False, cochrane=False, aha=False,
                provider_output=False, synthetic_only=False, redistribution_concern="Not matched by any pattern; needs manual review.",
                public_value="unknown", min_substitute="TODO", disposition="UNKNOWN", confidence="low", action="Manual classification needed.")


def classify(rel):
    for pattern, fields in GROUPS:
        if re.search(pattern, rel):
            return fields
    return FALLBACK


def main():
    with open(MANIFEST, newline="", encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh) if r["tier"] == "LICENSE_REVIEW"]

    out_rows = []
    for r in rows:
        g = classify(r["repo_path"])
        out_rows.append({
            "path": r["repo_path"],
            "artifact_type": g["artifact_type"],
            "upstream_source": g["upstream_source"],
            "contains_medal_derived": g["medal"],
            "contains_cochrane_derived": g["cochrane"],
            "contains_aha_derived": g["aha"],
            "contains_provider_model_output": g["provider_output"],
            "synthetic_or_project_authored_only": g["synthetic_only"],
            "redistribution_concern": g["redistribution_concern"],
            "public_release_value": g["public_value"],
            "minimum_public_substitute": g["min_substitute"],
            "recommended_disposition": g["disposition"],
            "confidence": g["confidence"],
            "action_required": g["action"],
            "source_sha256": r["source_sha256"],
        })

    fields = list(out_rows[0].keys())
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(out_rows)

    from collections import Counter
    print(f"{len(out_rows)} LICENSE_REVIEW rows -> {OUT.relative_to(ROOT)}")
    print("by artifact_type:", dict(Counter(r["artifact_type"] for r in out_rows)))
    print("by disposition:", dict(Counter(r["recommended_disposition"] for r in out_rows)))


if __name__ == "__main__":
    main()
