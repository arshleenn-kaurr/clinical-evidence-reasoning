#!/usr/bin/env python3

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


SEED = 2026090903
PER_STRATUM = 65

SRC = Path("data/replication_candidates_audited.csv")
OUT = Path("data/replication_cases.jsonl")
MANIFEST = Path("data/replication_freeze_manifest.json")

TRUTHY = {"1", "true", "yes", "y"}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


df = pd.read_csv(
    SRC,
    dtype=str,
    keep_default_na=False
)

df = df[
    df["eligible"].str.strip().str.lower().isin(TRUTHY)
].copy()

required = [
    "case_id",
    "source_type",
    "source_id",
    "reference_decision",
    "evidence-quality",
    "anonymized_question",
    "anonymized_anchor",
]

for col in required:
    bad = df[df[col].str.strip() == ""]
    if len(bad):
        raise ValueError(
            f"{len(bad)} eligible rows missing {col}"
        )

cells = [
    ("High", "support"),
    ("High", "do_not_support"),
    ("Moderate", "support"),
    ("Moderate", "do_not_support"),
]

selected = []

for i, (quality, decision) in enumerate(cells):
    g = df[
        (df["evidence-quality"] == quality)
        & (df["reference_decision"] == decision)
    ].copy()

    print(f"{quality}/{decision}: {len(g)} eligible")

    if len(g) < PER_STRATUM:
        raise RuntimeError(
            f"Need {PER_STRATUM}, only {len(g)} eligible "
            f"for {quality}/{decision}"
        )

    g = g.sample(
        n=PER_STRATUM,
        random_state=SEED + i,
        replace=False,
    )

    selected.append(g)

sel = pd.concat(
    selected,
    ignore_index=True
)

# Deterministically mix row order.
sel = sel.sample(
    frac=1,
    random_state=SEED + 100
).reset_index(drop=True)

records = []

for _, r in sel.iterrows():
    records.append({
        "case_id": r["case_id"],
        "source_type": r["source_type"],
        "source_id": r["source_id"],
        "question": r["anonymized_question"],
        "reference_decision": r["reference_decision"],
        "anchor": {
            "text": r["anonymized_anchor"],
            "evidence_quality": r["evidence-quality"],
        },
        "veto": False,
        "veto_subtype": "",
    })

with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    for r in records:
        f.write(
            json.dumps(
                r,
                ensure_ascii=False,
                sort_keys=True
            ) + "\n"
        )

digest = sha256_file(OUT)

with open(str(OUT) + ".sha256", "w") as f:
    f.write(digest + "\n")

counts = (
    sel.groupby(
        ["evidence-quality", "reference_decision"]
    )
    .size()
    .to_dict()
)

manifest = {
    "freeze_timestamp_utc": datetime.now(
        timezone.utc
    ).isoformat(),
    "purpose": "supplementary replication extension",
    "seed": SEED,
    "cases_per_stratum": PER_STRATUM,
    "total_cases": len(sel),
    "selection_uses_model_outputs": False,
    "primary_cohort_modified": False,
    "source_audited_csv": str(SRC),
    "source_audited_csv_sha256": sha256_file(SRC),
    "output": str(OUT),
    "output_sha256": digest,
    "strata": {
        f"{k[0]}__{k[1]}": int(v)
        for k, v in counts.items()
    },
}

with open(
    MANIFEST,
    "w",
    encoding="utf-8"
) as f:
    json.dump(
        manifest,
        f,
        indent=2,
        sort_keys=True
    )
    f.write("\n")

print("\nREPLICATION FREEZE COMPLETE")
print("Cases:", len(sel))
print("SHA256:", digest)

print("\nSTRATA:")
for k, v in sorted(counts.items()):
    print(k, v)

print("\nOutputs:")
print(OUT)
print(str(OUT) + ".sha256")
print(MANIFEST)
