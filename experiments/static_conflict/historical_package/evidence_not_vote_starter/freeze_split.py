import argparse
import hashlib
import json
import random
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


SEED = 20260909

TRUTHY = {"1", "true", "yes", "y"}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def is_eligible(x):
    return str(x).strip().lower() in TRUTHY


def norm_quality(x):
    x = str(x).strip().lower()
    if x == "high":
        return "High"
    if x == "moderate":
        return "Moderate"
    return str(x).strip()


def validate_required(df, fields, cohort):
    for _, row in df.iterrows():
        for field in fields:
            if not str(row.get(field, "")).strip():
                raise ValueError(
                    f"{cohort}: eligible case {row.get('case_id')} "
                    f"is missing required field '{field}'"
                )


def row_to_case(row, veto=False):
    return {
        "case_id": row["case_id"],
        "source_type": row["source_type"],
        "source_id": row["source_id"],
        "question": row["anonymized_question"],
        "reference_decision": row["reference_decision"],
        "anchor": {
            "text": row["anonymized_anchor"],
            "evidence_quality": row.get("evidence-quality", ""),
        },
        "veto": bool(veto),
        "veto_subtype": row.get("veto_subtype", "") if veto else "",
    }


def write_jsonl(rows, path):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def stratified_main_split(df, seed):
    rng = random.Random(seed)

    cells = [
        ("High", "support"),
        ("High", "do_not_support"),
        ("Moderate", "support"),
        ("Moderate", "do_not_support"),
    ]

    pools = {}

    for quality, decision in cells:
        pool = df[
            (df["evidence-quality"].map(norm_quality) == quality)
            & (df["reference_decision"].str.strip() == decision)
        ].copy()

        ids = list(pool.index)
        rng.shuffle(ids)
        pools[(quality, decision)] = ids

        # Need 10 final per cell, plus enough total for dev allocation.
        if len(ids) < 10:
            raise ValueError(
                f"Insufficient eligible cases in {quality}/{decision}: "
                f"{len(ids)} available, need at least 10."
            )

    # Exactly 40 final: 10 from each 2x2 cell.
    final_indices = []

    remaining = {}

    for cell in cells:
        final_indices.extend(pools[cell][:10])
        remaining[cell] = pools[cell][10:]

    # Exactly 10 dev, distributed 3/3/2/2.
    # Rotate which cells get 3 according to seeded shuffle to avoid arbitrary preference.
    cell_order = cells.copy()
    rng.shuffle(cell_order)

    dev_quota = {cell: 2 for cell in cells}
    dev_quota[cell_order[0]] += 1
    dev_quota[cell_order[1]] += 1

    dev_indices = []

    for cell in cells:
        need = dev_quota[cell]
        if len(remaining[cell]) < need:
            raise ValueError(
                f"Insufficient eligible cases in {cell[0]}/{cell[1]} "
                f"for dev allocation: {len(remaining[cell])} remain, need {need}."
            )
        dev_indices.extend(remaining[cell][:need])

    final_df = df.loc[final_indices].copy()
    dev_df = df.loc[dev_indices].copy()

    return final_df, dev_df, dev_quota


def veto_split(df, seed):
    n = len(df)

    if n < 10:
        raise ValueError(
            f"Only {n} eligible veto cases. Protocol requires at least 10."
        )

    rng = random.Random(seed + 1)

    indices = list(df.index)
    rng.shuffle(indices)

    if n <= 14:
        chosen = indices
    else:
        chosen = indices[:15]

        # Ensure both harm and no_benefit appear when both exist in eligible pool.
        subtypes = {
            str(df.loc[i, "veto_subtype"]).strip().lower()
            for i in chosen
        }

        full_subtypes = {
            str(x).strip().lower()
            for x in df["veto_subtype"]
        }

        for needed in ("harm", "no_benefit"):
            if needed in full_subtypes and needed not in subtypes:
                replacement = next(
                    i for i in indices[15:]
                    if str(df.loc[i, "veto_subtype"]).strip().lower() == needed
                )
                chosen[-1] = replacement
                subtypes.add(needed)

    return df.loc[chosen].copy()


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--main",
        default="data/cochrane_candidates.csv"
    )
    parser.add_argument(
        "--veto",
        default="data/aha_veto_candidates.csv"
    )
    parser.add_argument(
        "--out-dir",
        default="data"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=SEED
    )

    args = parser.parse_args()

    main_path = Path(args.main)
    veto_path = Path(args.veto)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    main_df = pd.read_csv(
        main_path,
        dtype=str,
        keep_default_na=False
    )

    veto_df = pd.read_csv(
        veto_path,
        dtype=str,
        keep_default_na=False
    )

    main_eligible = main_df[
        main_df["eligible"].map(is_eligible)
    ].copy()

    veto_eligible = veto_df[
        veto_df["eligible"].map(is_eligible)
    ].copy()

    validate_required(
        main_eligible,
        ["case_id", "anonymized_question", "anonymized_anchor"],
        "main",
    )

    validate_required(
        veto_eligible,
        [
            "case_id",
            "anonymized_question",
            "anonymized_anchor",
            "veto_subtype",
        ],
        "veto",
    )

    invalid_veto = veto_eligible[
        ~veto_eligible["veto_subtype"]
        .str.strip()
        .str.lower()
        .isin({"harm", "no_benefit"})
    ]

    if len(invalid_veto):
        raise ValueError(
            "Invalid veto_subtype values for eligible cases: "
            + ", ".join(invalid_veto["case_id"].tolist())
        )

    final_main, dev_main, dev_quota = stratified_main_split(
        main_eligible,
        args.seed
    )

    final_veto = veto_split(
        veto_eligible,
        args.seed
    )

    final_main_rows = [
        row_to_case(row, veto=False)
        for _, row in final_main.iterrows()
    ]

    dev_rows = [
        row_to_case(row, veto=False)
        for _, row in dev_main.iterrows()
    ]

    final_veto_rows = [
        row_to_case(row, veto=True)
        for _, row in final_veto.iterrows()
    ]

    outputs = {
        "dev_cases.jsonl": dev_rows,
        "final_main_cases.jsonl": final_main_rows,
        "final_veto_cases.jsonl": final_veto_rows,
    }

    output_hashes = {}

    for filename, rows in outputs.items():
        path = out_dir / filename

        write_jsonl(rows, path)

        digest = sha256_file(path)
        output_hashes[filename] = digest

        with open(
            str(path) + ".sha256",
            "w",
            encoding="utf-8"
        ) as f:
            f.write(digest + "\n")

    main_counts = (
        final_main.assign(
            quality=final_main["evidence-quality"].map(norm_quality)
        )
        .groupby(["quality", "reference_decision"])
        .size()
        .to_dict()
    )

    veto_counts = (
        final_veto["veto_subtype"]
        .str.strip()
        .str.lower()
        .value_counts()
        .to_dict()
    )

    manifest = {
        "freeze_timestamp_utc": datetime.now(
            timezone.utc
        ).isoformat(),

        "seed": args.seed,

        "source_files": {
            "main": str(main_path),
            "veto": str(veto_path),
        },

        "source_sha256": {
            "main": sha256_file(main_path),
            "veto": sha256_file(veto_path),
        },

        "eligible_counts": {
            "main": len(main_eligible),
            "veto": len(veto_eligible),
        },

        "frozen_counts": {
            "dev": len(dev_main),
            "final_main": len(final_main),
            "final_veto": len(final_veto),
        },

        "final_main_strata": {
            f"{k[0]}__{k[1]}": int(v)
            for k, v in main_counts.items()
        },

        "dev_quota": {
            f"{k[0]}__{k[1]}": int(v)
            for k, v in dev_quota.items()
        },

        "final_veto_subtypes": {
            str(k): int(v)
            for k, v in veto_counts.items()
        },

        "output_sha256": output_hashes,
    }

    manifest_path = out_dir / "freeze_manifest.json"

    with open(
        manifest_path,
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

    print("\nFREEZE COMPLETE")
    print("----------------")
    print("Seed:", args.seed)
    print("Eligible main:", len(main_eligible))
    print("Eligible veto:", len(veto_eligible))
    print("Dev:", len(dev_main))
    print("Final main:", len(final_main))
    print("Final veto:", len(final_veto))

    print("\nFinal-main strata:")
    for k, v in sorted(main_counts.items()):
        print(f"  {k}: {v}")

    print("\nVeto subtypes:")
    for k, v in veto_counts.items():
        print(f"  {k}: {v}")

    print("\nOutputs:")
    for filename in outputs:
        print(" ", out_dir / filename)
        print(" ", out_dir / (filename + ".sha256"))

    print(" ", manifest_path)


if __name__ == "__main__":
    main()
