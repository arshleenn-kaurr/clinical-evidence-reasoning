#!/usr/bin/env python3

import argparse
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_MODEL = "gemini-2.5-flash"


def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]


def completed_ids(path):
    p = Path(path)
    if not p.exists():
        return set()

    ids = set()
    with p.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                r = json.loads(line)
                if r.get("status") == "ok":
                    ids.add(r["prompt_id"])
            except Exception:
                pass
    return ids


def validate_answer(x):
    required = {
        "decision",
        "confidence",
        "dominant_evidence_ids",
        "rationale",
    }

    if not isinstance(x, dict):
        raise ValueError("Response is not a JSON object")

    missing = required - set(x)
    if missing:
        raise ValueError(f"Missing keys: {sorted(missing)}")

    if x["decision"] not in {
        "support",
        "do_not_support",
        "insufficient",
    }:
        raise ValueError(
            f"Invalid decision: {x['decision']}"
        )

    conf = float(x["confidence"])
    if not 0 <= conf <= 100:
        raise ValueError(
            f"Confidence outside 0-100: {conf}"
        )

    if not isinstance(x["dominant_evidence_ids"], list):
        raise ValueError(
            "dominant_evidence_ids must be a list"
        )

    x["confidence"] = conf
    x["dominant_evidence_ids"] = [
        str(v) for v in x["dominant_evidence_ids"]
    ]

    return x


def call_gemini(prompt, model, key, retries=5):
    url = (
        "https://generativelanguage.googleapis.com/"
        f"v1beta/models/{model}:generateContent?key={key}"
    )

    body = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}],
            }
        ],
        "generationConfig": {
            "temperature": 0,
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "object",
                "properties": {
                    "decision": {
                        "type": "string",
                        "enum": [
                            "support",
                            "do_not_support",
                            "insufficient",
                        ],
                    },
                    "confidence": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 100,
                    },
                    "dominant_evidence_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "rationale": {
                        "type": "string",
                    },
                },
                "required": [
                    "decision",
                    "confidence",
                    "dominant_evidence_ids",
                    "rationale",
                ],
            },
        },
    }

    data = json.dumps(body).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(
                req,
                timeout=120
            ) as resp:
                raw = json.load(resp)

            candidates = raw.get("candidates", [])
            if not candidates:
                raise RuntimeError(
                    f"No candidate returned: {raw}"
                )

            parts = (
                candidates[0]
                .get("content", {})
                .get("parts", [])
            )

            text = "".join(
                p.get("text", "")
                for p in parts
                if "text" in p
            ).strip()

            if not text:
                raise RuntimeError(
                    f"No text returned: {raw}"
                )

            parsed = validate_answer(
                json.loads(text)
            )

            return parsed, text, raw

        except urllib.error.HTTPError as e:
            msg = e.read().decode(
                "utf-8",
                errors="replace",
            )

            if e.code in {
                429, 500, 502, 503, 504
            } and attempt < retries:
                wait = 2 ** attempt
                print(
                    f"  HTTP {e.code}; "
                    f"retrying in {wait}s..."
                )
                time.sleep(wait)
                continue

            raise RuntimeError(
                f"HTTP {e.code}: {msg}"
            )

        except (
            urllib.error.URLError,
            TimeoutError,
        ) as e:
            if attempt < retries:
                wait = 2 ** attempt
                print(
                    f"  Network error; "
                    f"retrying in {wait}s..."
                )
                time.sleep(wait)
                continue
            raise

    raise RuntimeError("Retry limit exhausted")


def main():
    ap = argparse.ArgumentParser()

    ap.add_argument(
        "--input",
        default="data/dev_prompts.jsonl",
    )

    ap.add_argument(
        "--output",
        default="results/dev_gemini_2_5_flash.jsonl",
    )

    ap.add_argument(
        "--model",
        default=DEFAULT_MODEL,
    )

    ap.add_argument(
        "--limit",
        type=int,
        default=None,
    )

    ap.add_argument(
        "--sleep",
        type=float,
        default=7.0,
    )

    args = ap.parse_args()

    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise SystemExit(
            "GEMINI_API_KEY is not set."
        )

    rows = load_jsonl(args.input)

    done = completed_ids(args.output)

    todo = [
        r for r in rows
        if r["prompt_id"] not in done
    ]

    if args.limit is not None:
        todo = todo[:args.limit]

    out = Path(args.output)
    out.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("Model:", args.model)
    print("Input:", args.input)
    print("Already completed:", len(done))
    print("Running now:", len(todo))
    print()

    for i, row in enumerate(todo, start=1):
        pid = row["prompt_id"]

        print(
            f"[{i}/{len(todo)}] {pid}",
            flush=True,
        )

        result = {
            "prompt_id": pid,
            "case_id": row["case_id"],
            "condition": row["condition"],
            "reference_decision":
                row["reference_decision"],
            "veto": row.get("veto", False),
            "veto_subtype":
                row.get("veto_subtype"),
            "model": args.model,
            "temperature": 0,
        }

        try:
            parsed, raw_text, provider = call_gemini(
                row["prompt"],
                args.model,
                key,
            )

            result.update(parsed)

            result["status"] = "ok"
            result["raw_text"] = raw_text

            result["finish_reason"] = (
                provider.get("candidates", [{}])[0]
                .get("finishReason")
            )

            result["usage_metadata"] = (
                provider.get("usageMetadata", {})
            )

            print(
                "  ->",
                parsed["decision"],
                f"({parsed['confidence']})",
                parsed["dominant_evidence_ids"],
            )

        except Exception as e:
            result["status"] = "error"
            result["error"] = repr(e)
            print("  ERROR:", e)

        with out.open(
            "a",
            encoding="utf-8",
        ) as f:
            f.write(
                json.dumps(
                    result,
                    ensure_ascii=False,
                )
                + "\n"
            )

        if i < len(todo):
            time.sleep(args.sleep)

    print()
    print("DONE ->", out)


if __name__ == "__main__":
    main()
