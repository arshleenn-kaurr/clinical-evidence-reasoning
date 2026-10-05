#!/usr/bin/env python3
"""RELEASE TOOLING (not historical execution code). Dry-run by default.

Future workflow for ingesting a finished camera-ready PDF once one exists
(at Phase 5A none existed; AgenticLS was ingested in Phase 5B, GenAI4Health is still CAMERA-READY PENDING). This script does
NOT read, parse, or extract anything from the PDF's content: title, authors,
affiliations, workshop, and year must be given explicitly on the command
line (or via --metadata-json), never auto-extracted from current draft
files or from the PDF itself. That is a deliberate guard against silently
baking in draft/incorrect bibliographic metadata.

Usage (dry-run; prints the plan, touches nothing):
    python scripts/ingest_camera_ready.py --paper genai4health \\
        --pdf /path/to/final.pdf --title "..." --authors "A. One; B. Two" \\
        --affiliations "University X; Lab Y" --workshop "GenAI4Health, NeurIPS 2026" \\
        --year 2026 [--url ...] [--doi ...]

Usage (actually copy the PDF and write metadata):
    python scripts/ingest_camera_ready.py ... --apply

Will refuse to overwrite an existing final PDF unless --force is also given.

Writes (only with --apply):
    papers/<paper>/paper/<paper>-camera-ready.pdf
    papers/<paper>/paper/metadata.json
"""
import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALID_PAPERS = {"genai4health", "agenticls"}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def looks_like_pdf(path):
    try:
        with open(path, "rb") as fh:
            return fh.read(5) == b"%PDF-"
    except OSError:
        return False


def split_list(s):
    return [x.strip() for x in s.split(";") if x.strip()] if s else []


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--paper", required=True, choices=sorted(VALID_PAPERS))
    ap.add_argument("--pdf", required=True, type=Path, help="Path to the final camera-ready PDF.")
    ap.add_argument("--title", help="Final camera-ready title. Required with --apply.")
    ap.add_argument("--authors", help="Semicolon-separated author list, e.g. 'A. One; B. Two'. Required with --apply.")
    ap.add_argument("--affiliations", help="Semicolon-separated affiliation list, in author order or as a flat list.")
    ap.add_argument("--workshop", help="e.g. 'GenAI4Health, NeurIPS 2026 Workshop'. Required with --apply.")
    ap.add_argument("--year", type=int, help="Publication year. Required with --apply.")
    ap.add_argument("--url", default=None, help="Optional paper URL (OpenReview, proceedings page, etc.).")
    ap.add_argument("--doi", default=None, help="Optional DOI, only if one actually exists — never invented.")
    ap.add_argument("--apply", action="store_true", help="Actually copy the PDF and write metadata.json. Without this flag, nothing is written (dry run).")
    ap.add_argument("--force", action="store_true", help="Allow overwriting an already-ingested final PDF/metadata.")
    args = ap.parse_args()

    paper_dir = ROOT / "papers" / args.paper / "paper"
    dest_pdf = paper_dir / f"{args.paper}-camera-ready.pdf"
    dest_meta = paper_dir / "metadata.json"

    print(f"Paper: {args.paper}")
    print(f"Source PDF: {args.pdf}")

    if not args.pdf.exists():
        print(f"FAIL: source PDF does not exist: {args.pdf}")
        return 1
    if not looks_like_pdf(args.pdf):
        print(f"FAIL: {args.pdf} does not look like a PDF (missing %PDF- header)")
        return 1
    digest = sha256(args.pdf)
    print(f"SHA256: {digest}")
    print(f"Size: {args.pdf.stat().st_size} bytes")

    if dest_pdf.exists() and not args.force:
        print(f"FAIL: {dest_pdf.relative_to(ROOT)} already exists. Pass --force to overwrite an already-ingested PDF.")
        return 1

    metadata = {
        "paper": args.paper,
        "title": args.title,
        "authors": split_list(args.authors),
        "affiliations": split_list(args.affiliations),
        "workshop": args.workshop,
        "year": args.year,
        "url": args.url,
        "doi": args.doi,
        "pdf_filename": dest_pdf.name,
        "pdf_sha256": digest,
        "pdf_size_bytes": args.pdf.stat().st_size,
        "ingested_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }

    if not args.apply:
        print("\nDRY RUN — nothing written. Plan:")
        print(f"  would copy -> {dest_pdf.relative_to(ROOT)}")
        print(f"  would write -> {dest_meta.relative_to(ROOT)}:")
        print(json.dumps(metadata, indent=2))
        missing_required = [f for f in ("title", "authors", "workshop", "year") if not metadata[f]]
        if missing_required:
            print(f"\nNOTE: these required fields are not yet set: {missing_required} "
                  "(required when actually running with --apply).")
        return 0

    missing_required = [f for f in ("title", "authors", "workshop", "year") if not metadata[f]]
    if missing_required:
        print(f"FAIL: --apply requires these fields to be set: {missing_required}")
        return 1

    paper_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(args.pdf, dest_pdf)
    with open(dest_meta, "w", encoding="utf-8") as fh:
        json.dump(metadata, fh, indent=2)
        fh.write("\n")
    print(f"\nWrote {dest_pdf.relative_to(ROOT)}")
    print(f"Wrote {dest_meta.relative_to(ROOT)}")
    print("\nReminder: this does not update CITATION.cff, docs/result_provenance.csv's camera-ready "
          "columns, or tag the repository. Those remain separate, deliberate steps (see "
          "docs/release_strategy.md, docs/camera_ready_provenance_mapping_template.csv).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
