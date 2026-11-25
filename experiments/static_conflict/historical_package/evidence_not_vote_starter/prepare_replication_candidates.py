#!/usr/bin/env python3

import hashlib
import json
from pathlib import Path

import pandas as pd


SEED = 2026090902
PER_STRATUM_CANDIDATES = 85

RAW = Path("data/QA-systematic-review.jsonl")
OLD = Path("data/cochrane_candidates.csv")
OUT = Path("data/replication_candidates.csv")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


raw = pd.read_json(RAW, lines=True).reset_index(names="_raw_index")
old = pd.read_csv(OLD, dtype=str, keep_default_na=False)

# ---------------------------------------------------------
# Restrict to SAME evidence contract as original main cohort
# ---------------------------------------------------------
raw["answer"] = raw["answer"].astype(str).str.strip()
raw["evidence-quality"] = (
    raw["evidence-quality"].astype(str).str.strip()
)

pool = raw[
    raw["answer"].isin(["Yes", "No"])
    & raw["evidence-quality"].isin(["High", "Moderate"])
].copy()

pool["question"] = pool["question"].fillna("").astype(str).str.strip()
pool["doi"] = pool["doi"].fillna("").astype(str).str.strip()

# Stable source ID.
pool["source_id"] = pool.apply(
    lambda r: r["doi"]
    if r["doi"]
    else f"medal_row_{int(r['_raw_index']):05d}",
    axis=1,
)

# ---------------------------------------------------------
# Exclude ALL 120 original candidate-pool cases,
# not merely the 40 selected final cases.
# This prevents reuse of previously audited/exposed cases.
# ---------------------------------------------------------
old_source_ids = set(
    old["source_id"].astype(str).str.strip()
)
old_questions = set(
    old["question"].astype(str).str.strip()
)

pool = pool[
    ~pool["source_id"].isin(old_source_ids)
    & ~pool["question"].isin(old_questions)
].copy()

# Remove exact duplicate sources/questions before sampling.
pool = pool.drop_duplicates(subset=["source_id"])
pool = pool.drop_duplicates(subset=["question"])

pool["reference_decision"] = pool["answer"].map({
    "Yes": "support",
    "No": "do_not_support",
})

cells = [
    ("High", "support"),
    ("High", "do_not_support"),
    ("Moderate", "support"),
    ("Moderate", "do_not_support"),
]

selected = []

for i, (quality, decision) in enumerate(cells):
    g = pool[
        (pool["evidence-quality"] == quality)
        & (pool["reference_decision"] == decision)
    ].copy()

    print(
        f"AVAILABLE {quality}/{decision}: {len(g)}"
    )

    if len(g) < PER_STRATUM_CANDIDATES:
        raise RuntimeError(
            f"Not enough candidates for {quality}/{decision}: "
            f"{len(g)} available."
        )

    # Deterministic sampling. No model results are used.
    g = g.sample(
        n=PER_STRATUM_CANDIDATES,
        random_state=SEED + i,
        replace=False,
    )

    selected.append(g)

out = pd.concat(selected, ignore_index=True)

# Shuffle final row order deterministically so strata are not blocked.
out = out.sample(
    frac=1,
    random_state=SEED + 100,
).reset_index(drop=True)

out["case_id"] = [
    f"R{i:04d}"
    for i in range(1, len(out) + 1)
]

final = pd.DataFrame({
    "case_id": out["case_id"],
    "source_type": "cochrane",
    "source_id": out["source_id"],
    "publication_year": out["publication_year"],
    "question": out["question"],
    "reference_decision": out["reference_decision"],
    "evidence-quality": out["evidence-quality"],
    "discrepancy": out["discrepancy"],
    "notes": out["notes"],
    "anonymized_question": "",
    "anonymized_anchor": "",
    "eligible": "",
    "audit_note": "",
})

OUT.parent.mkdir(parents=True, exist_ok=True)
final.to_csv(OUT, index=False)

digest = sha256(OUT)

with open(str(OUT) + ".sha256", "w") as f:
    f.write(digest + "\n")

manifest = {
    "purpose": "supplementary replication extension",
    "selection_time_relative_to_results":
        "defined before aggregate primary results were inspected",
    "seed": SEED,
    "candidate_count_per_stratum": PER_STRATUM_CANDIDATES,
    "total_candidates": len(final),
    "raw_medal_sha256": sha256(RAW),
    "original_candidate_pool_sha256": sha256(OLD),
    "replication_candidates_sha256": digest,
    "selection_uses_model_outputs": False,
    "original_candidate_pool_excluded_entirely": True,
}

with open(
    "data/replication_candidate_manifest.json",
    "w",
    encoding="utf-8",
) as f:
    json.dump(manifest, f, indent=2)
    f.write("\n")

print("\nCREATED:", OUT)
print("TOTAL:", len(final))

print("\nSELECTED STRATA:")
print(
    final.groupby(
        ["evidence-quality", "reference_decision"]
    ).size()
)

print("\nSHA256:", digest)
