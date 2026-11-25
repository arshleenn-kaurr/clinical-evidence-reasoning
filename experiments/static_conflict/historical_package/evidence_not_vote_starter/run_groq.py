#!/usr/bin/env python3

import argparse
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_MODEL = "openai/gpt-oss-120b"


def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]


def completed_ids(path):
    p = Path(path)
    if not p.exists():
        return set()

    done = set()
    with p.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                r = json.loads(line)
                if r.get("status") == "ok":
                    done.add(r["prompt_id"])
            except Exception:
                pass
    return done


def validate_answer(x):
    if not isinstance(x, dict):
        raise ValueError("Response is not a JSON object")

    required = {
        "decision",
        "confidence",
        "dominant_evidence_ids",
        "rationale",
    }

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


def call_groq(prompt, model, key, retries=6):
    url = "https://api.groq.com/openai/v1/chat/completions"

    schema = {
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
        "additionalProperties": False,
    }

    body = {
        "model": model,

        # Do not add a new system prompt.
        # The frozen benchmark prompt is passed unchanged.
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],

        "temperature": 0,

        # Keep reasoning configuration fixed for every run.
        "reasoning_effort": "medium",

        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "therapeutic_decision",
                "strict": True,
                "schema": schema,
            },
        },
    }

    encoded = json.dumps(body).encode("utf-8")

    for attempt in range(1, retries + 1):
        req = urllib.request.Request(
            url,
            data=encoded,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "User-Agent": "evidence-not-vote/1.0",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(
                req,
                timeout=180,
            ) as resp:
                raw = json.load(resp)

            choices = raw.get("choices", [])
            if not choices:
                raise RuntimeError(
                    f"No choices returned: {raw}"
                )

            text = (
                choices[0]
                .get("message", {})
                .get("content", "")
            )

            if not text:
                raise RuntimeError(
                    f"No response content: {raw}"
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

            if e.code == 429 and attempt < retries:
                retry_after = e.headers.get(
                    "Retry-After"
                )

                try:
                    wait = float(retry_after)
                except Exception:
                    wait = min(60, 2 ** attempt)

                print(
                    f"  HTTP 429; retrying in {wait}s..."
                )
                time.sleep(wait)
                continue

            if e.code in {
                500, 502, 503, 504
            } and attempt < retries:
                wait = min(60, 2 ** attempt)

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
                wait = min(60, 2 ** attempt)

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
        default="results/dev_gpt_oss_120b.jsonl",
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
        default=2.0,
    )

    args = ap.parse_args()

    key = os.environ.get("GROQ_API_KEY")

    if not key:
        raise SystemExit(
            "GROQ_API_KEY is not set."
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
            "reasoning_effort": "medium",
        }

        try:
            parsed, raw_text, provider = call_groq(
                row["prompt"],
                args.model,
                key,
            )

            result.update(parsed)
            result["status"] = "ok"
            result["raw_text"] = raw_text

            choice = provider.get(
                "choices", [{}]
            )[0]

            result["finish_reason"] = (
                choice.get("finish_reason")
            )

            result["usage"] = (
                provider.get("usage", {})
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

            print(
                "  ERROR:",
                e,
            )

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
