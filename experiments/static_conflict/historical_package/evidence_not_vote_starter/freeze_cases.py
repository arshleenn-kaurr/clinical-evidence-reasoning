#!/usr/bin/env python3
"""
Freeze the audited MEDAL candidate cohorts into immutable dev/final splits.

Protocol source: audit_protocol.md (split sizes / balance requirements) and
analysis_contract.md (cohort definitions, and the seeds for OTHER pipeline
stages). This script makes no scientific judgment of its own -- the manual
audit (the `eligible`, `anonymized_question`, `anonymized_anchor`, and
`veto_subtype` columns) is the only input that determines which cases are
eligible. Given that audit, this script only:

  1. validates every eligible row has the fields the benchmark needs;
  2. deterministically partitions the eligible pool into dev / final-main /
     final-veto under a fixed seed, preserving 2x2 stratum balance for the
     main cohort (evidence-quality x reference_decision) and proportional
     harm/no_benefit representation for the veto cohort;
  3. writes three immutable JSONL files, SHA256 sidecars for each, and a
     provenance manifest.

It never reads model outputs and performs no case-text-based selection.
"""
import argparse
import hashlib
import json
import random
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

# --- Fixed constants ---------------------------------------------------------

# audit_protocol.md / analysis_contract.md do not declare a seed for THIS
# step (the contract's seeds cover candidate sampling, condition ordering,
# and bootstrapping -- earlier/later pipeline stages). We reuse the project's
# single already-declared constant (also SEED in prepare_cases.py) for
# consistency rather than introducing a new arbitrary value. Override with
# --seed only for testing; a real freeze should use the default.
DEFAULT_SEED = 20260909

FINAL_MAIN_N = 40
DEV_MAIN_N = 10
VETO_FINAL_TARGET = 15
VETO_FINAL_MIN = 10

# Canonical, alphabetically-fixed stratum order. Fixed so "as evenly as
# possible" dev-count remainders are assigned deterministically -- never
# based on case content, pool size, or expected difficulty.
MAIN_STRATA = [
    ("High", "do_not_support"),
    ("High", "support"),
    ("Moderate", "do_not_support"),
    ("Moderate", "support"),
]
FINAL_PER_STRATUM = {s: FINAL_MAIN_N // len(MAIN_STRATA) for s in MAIN_STRATA}  # 10 each

VALID_VETO_SUBTYPES = {"harm", "no_benefit"}

SCRIPT_VERSION = "2.0.0-dev-final-split"


def clean(x):
    if x is None:
        return ""
    s = str(x).strip()
    return "" if s.lower() == "nan" else s


def truthy(x):
    return clean(x).lower() in {"1", "true", "yes", "y"}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_jsonl(path: Path, records) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for x in records:
            f.write(json.dumps(x, ensure_ascii=False) + "\n")
    digest = sha256_file(path)
    (path.parent / (path.name + ".sha256")).write_text(digest + "\n")
    return digest


def dev_counts_per_stratum(dev_n, strata):
    """Split dev_n as evenly as possible across strata, in canonical order.

    Remainder goes to the first `dev_n % len(strata)` strata in the fixed
    MAIN_STRATA order -- a rule fixed in code, independent of the data.
    """
    base, rem = divmod(dev_n, len(strata))
    return {s: base + (1 if i < rem else 0) for i, s in enumerate(strata)}


def to_main_record(r):
    return {
        "case_id": clean(r["case_id"]),
        "source_type": "cochrane",
        "source_id": clean(r.get("source_id")),
        "question": clean(r.get("anonymized_question")),
        "reference_decision": clean(r["reference_decision"]),
        "anchor": {
            "id": "E0",
            "tier": "high",
            "source_kind": "systematic_review",
            "declared_quality": clean(r.get("evidence-quality")),
            "text": clean(r.get("anonymized_anchor")),
        },
        "veto": False,
        "veto_subtype": None,
    }


def to_veto_record(r):
    return {
        "case_id": clean(r["case_id"]),
        "source_type": "aha_veto",
        "source_id": clean(r.get("source_id")),
        "question": clean(r.get("anonymized_question")),
        "reference_decision": "do_not_support",
        "anchor": {
            "id": "E0",
            "tier": "constraint",
            "source_kind": "clinical_guideline",
            "class_of_recommendation": clean(r.get("COR")),
            "level_of_evidence": clean(r.get("LOE")),
            "text": clean(r.get("anonymized_anchor")),
        },
        "veto": True,
        "veto_subtype": clean(r.get("veto_subtype")) or None,
    }


# --- Validation (hard-fail before any selection happens) --------------------

def validate_eligible_main(rows):
    problems = []
    for r in rows:
        q = clean(r.get("anonymized_question"))
        a = clean(r.get("anonymized_anchor"))
        if not q or not a:
            problems.append(f"  {r.get('case_id')}: missing anonymized_question/anonymized_anchor")
    if problems:
        raise ValueError(
            "Eligible Cochrane rows are missing required audited fields "
            "(fix the CSV, do not relax this check):\n" + "\n".join(problems)
        )


def validate_eligible_veto(rows):
    problems = []
    for r in rows:
        q = clean(r.get("anonymized_question"))
        a = clean(r.get("anonymized_anchor"))
        st = clean(r.get("veto_subtype")).lower()
        if not q or not a:
            problems.append(f"  {r.get('case_id')}: missing anonymized_question/anonymized_anchor")
        if st not in VALID_VETO_SUBTYPES:
            problems.append(
                f"  {r.get('case_id')}: veto_subtype must be one of "
                f"{sorted(VALID_VETO_SUBTYPES)}, got {r.get('veto_subtype')!r}"
            )
    if problems:
        raise ValueError(
            "Eligible AHA veto rows are missing required audited fields "
            "(fix the CSV, do not relax this check):\n" + "\n".join(problems)
        )


# --- Deterministic selection -------------------------------------------------

def select_main_split(eligible_rows, seed):
    groups = defaultdict(list)
    for r in eligible_rows:
        key = (clean(r.get("evidence-quality")), clean(r.get("reference_decision")))
        groups[key].append(r)

    unknown = set(groups) - set(MAIN_STRATA)
    if unknown:
        raise ValueError(
            "Eligible Cochrane rows have evidence-quality/reference_decision "
            f"combinations outside the frozen 2x2 stratum set {MAIN_STRATA}: "
            f"{sorted(unknown)}. This means the audited CSV contains a value "
            "the protocol does not define -- fix the CSV, not the split logic."
        )

    dev_counts = dev_counts_per_stratum(DEV_MAIN_N, MAIN_STRATA)

    shortfalls = []
    for s in MAIN_STRATA:
        need = FINAL_PER_STRATUM[s] + dev_counts[s]
        have = len(groups.get(s, []))
        if have < need:
            shortfalls.append(
                f"  {s[0]}/{s[1]}: need {need} (final {FINAL_PER_STRATUM[s]} + "
                f"dev {dev_counts[s]}), have {have} eligible"
            )
    if shortfalls:
        raise SystemExit(
            "Cannot build the deterministic main split: insufficient eligible "
            "cases in one or more strata. The protocol forbids substituting "
            "other cells or forcing ineligible cases to hit balance -- audit "
            "more cases in the short strata, or STOP.\n" + "\n".join(shortfalls)
        )

    rng = random.Random(seed)
    final_main, dev_main = [], []
    for s in MAIN_STRATA:
        # Sort by case_id first so the result depends only on (seed, eligible
        # set) -- never on incidental CSV row order.
        pool = sorted(groups[s], key=lambda r: r["case_id"])
        rng.shuffle(pool)
        final_main.extend(pool[: FINAL_PER_STRATUM[s]])
        dev_main.extend(pool[FINAL_PER_STRATUM[s]: FINAL_PER_STRATUM[s] + dev_counts[s]])

    return final_main, dev_main, dev_counts


def select_veto_final(eligible_rows, seed):
    n = len(eligible_rows)
    if n < VETO_FINAL_MIN:
        raise SystemExit(
            f"Only {n} eligible AHA veto cases; the protocol's target range is "
            f"{VETO_FINAL_MIN}-{VETO_FINAL_TARGET}. Cannot proceed -- audit more "
            "veto cases, or STOP (do not lower the range)."
        )
    target = min(VETO_FINAL_TARGET, n)

    by_subtype = defaultdict(list)
    for r in eligible_rows:
        by_subtype[clean(r.get("veto_subtype")).lower()].append(r)
    for k in by_subtype:
        by_subtype[k].sort(key=lambda r: r["case_id"])

    if target == n:
        # Take every eligible case -- no trimming, so no allocation decision.
        selected = sorted(eligible_rows, key=lambda r: r["case_id"])
        alloc = {k: len(v) for k, v in by_subtype.items()}
    else:
        # n > 15: proportionally preserve harm/no_benefit representation
        # (largest-remainder rounding on each subtype's share of the eligible
        # pool) rather than inventing a fixed quota. Deterministic tie-break
        # is alphabetical subtype name ("harm" < "no_benefit").
        subtypes = sorted(by_subtype)
        raw = {k: target * len(by_subtype[k]) / n for k in subtypes}
        alloc = {k: int(raw[k]) for k in subtypes}
        remaining = target - sum(alloc.values())
        order = sorted(subtypes, key=lambda k: (-(raw[k] - alloc[k]), k))
        for k in order[:remaining]:
            alloc[k] += 1

        rng = random.Random(seed)
        selected = []
        for k in subtypes:
            pool = list(by_subtype[k])
            rng.shuffle(pool)
            selected.extend(pool[: alloc[k]])
        selected.sort(key=lambda r: r["case_id"])

    return selected, alloc


# --- Provenance manifest -----------------------------------------------------

def stratum_counts(rows):
    c = defaultdict(int)
    for r in rows:
        c[f"{clean(r.get('evidence-quality'))}/{clean(r.get('reference_decision'))}"] += 1
    return dict(c)


def subtype_counts(rows):
    c = defaultdict(int)
    for r in rows:
        c[clean(r.get("veto_subtype")).lower() or "<missing>"] += 1
    return dict(c)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--main", required=True, help="Audited Cochrane candidates CSV")
    ap.add_argument("--veto", required=True, help="Audited AHA veto candidates CSV")
    ap.add_argument("--out-dir", default="data", help="Directory for frozen outputs (default: data)")
    ap.add_argument(
        "--seed", type=int, default=DEFAULT_SEED,
        help=f"Deterministic split seed (default: project seed {DEFAULT_SEED}). "
             "Override only for testing -- a real freeze should use the default.",
    )
    args = ap.parse_args()

    main_path = Path(args.main)
    veto_path = Path(args.veto)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # dtype=str + keep_default_na=False: prevents pandas from inferring a
    # numeric dtype for columns like `eligible` (e.g. "1"/blank -> float64,
    # which silently turns "1" into 1.0 and breaks truthy()'s exact string
    # match). Every field is read as literal text, blanks stay "".
    m = pd.read_csv(main_path, dtype=str, keep_default_na=False)
    v = pd.read_csv(veto_path, dtype=str, keep_default_na=False)

    eligible_main = [r for _, r in m.iterrows() if truthy(r.get("eligible"))]
    eligible_veto = [r for _, r in v.iterrows() if truthy(r.get("eligible"))]

    # Hard-fail on incomplete audit BEFORE any selection happens (fail atomic:
    # nothing is written if any eligible row is incomplete).
    validate_eligible_main(eligible_main)
    validate_eligible_veto(eligible_veto)

    final_main, dev_main, dev_counts = select_main_split(eligible_main, args.seed)
    final_veto, veto_alloc = select_veto_final(eligible_veto, args.seed)

    dev_out = out_dir / "dev_cases.jsonl"
    final_main_out = out_dir / "final_main_cases.jsonl"
    final_veto_out = out_dir / "final_veto_cases.jsonl"

    dev_sha = write_jsonl(dev_out, [to_main_record(r) for r in sorted(dev_main, key=lambda r: r["case_id"])])
    final_main_sha = write_jsonl(final_main_out, [to_main_record(r) for r in sorted(final_main, key=lambda r: r["case_id"])])
    final_veto_sha = write_jsonl(final_veto_out, [to_veto_record(r) for r in final_veto])

    manifest = {
        "freeze_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "script": {
            "file": "freeze_cases.py",
            "version": SCRIPT_VERSION,
            "sha256": sha256_file(Path(__file__).resolve()),
        },
        "seed": args.seed,
        "seed_source": (
            "Not specified in analysis_contract.md or audit_protocol.md for the "
            "dev/final split step; reused the project's single declared seed "
            f"({DEFAULT_SEED}, also used for candidate sampling in "
            "prepare_cases.py) for consistency."
            if args.seed == DEFAULT_SEED else
            "Overridden from the project default via --seed (non-default run -- "
            "do not use for a real freeze)."
        ),
        "source_files": {
            "main_candidates": str(main_path),
            "main_candidates_sha256": sha256_file(main_path),
            "veto_candidates": str(veto_path),
            "veto_candidates_sha256": sha256_file(veto_path),
        },
        "eligible_counts": {
            "main_eligible": len(eligible_main),
            "veto_eligible": len(eligible_veto),
        },
        "assigned_counts": {
            "dev_main": len(dev_main),
            "final_main": len(final_main),
            "final_veto": len(final_veto),
        },
        "main_stratum_counts": {
            "eligible_pool": stratum_counts(eligible_main),
            "dev": stratum_counts(dev_main),
            "final": stratum_counts(final_main),
            "targets": {
                "final_per_stratum": {f"{k[0]}/{k[1]}": val for k, val in FINAL_PER_STRATUM.items()},
                "dev_per_stratum": {f"{k[0]}/{k[1]}": val for k, val in dev_counts.items()},
            },
        },
        "veto_subtype_counts": {
            "eligible_pool": subtype_counts(eligible_veto),
            "final": subtype_counts(final_veto),
            "allocation_used": veto_alloc,
        },
        "output_files": {
            "dev_cases.jsonl": {"path": str(dev_out), "sha256": dev_sha},
            "final_main_cases.jsonl": {"path": str(final_main_out), "sha256": final_main_sha},
            "final_veto_cases.jsonl": {"path": str(final_veto_out), "sha256": final_veto_sha},
        },
    }

    manifest_path = out_dir / "freeze_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Froze {len(dev_main)} dev + {len(final_main)} final-main + {len(final_veto)} final-veto cases.")
    print(f"  {dev_out}  sha256={dev_sha}")
    print(f"  {final_main_out}  sha256={final_main_sha}")
    print(f"  {final_veto_out}  sha256={final_veto_sha}")
    print(f"  manifest: {manifest_path}")


if __name__ == "__main__":
    main()
