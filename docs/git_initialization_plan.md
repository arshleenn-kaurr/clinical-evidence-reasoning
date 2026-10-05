# Git initialization plan (NOT executed)

**Audit result (2026-10-04, re-audited in the pre-GitHub phase):** The archive checkout (`clinical-evidence-reasoning/`, wherever it lives locally) is **not a git repository** (`git rev-parse` → "not a git repository"); no commit, branch, tag or remote exists anywhere. Nothing in this document has been run.

## Principle

The working tree is the **archive**: it contains files intentionally withheld from the public release (64 `LICENSE_REVIEW`, 55 `ARCHIVAL_ONLY`, the camera-ready PDF pending permission, scratch venvs/logs). **Never** run `git init` inside it followed by `git add .`/`git add -A`. Initialize instead from the clean, validated public tree `dist/public_v1_preview/` (or an equivalent copy), staging only files listed in its `MANIFEST.csv`.

## Commands for later (require explicit authorization; do not run now)

Preconditions:

1. Code license: MIT, applied (`LICENSE`). Done.
2. Author emails removed from the public tree. Done (`docs/public_identity_review.md`).
3. Commit identity: **still to be supplied by the authors** (placeholders below; public in history forever). Recommended: a GitHub no-reply address (GitHub shows one under Settings → Emails, of the form `<id>+<username>@users.noreply.github.com`). Use only the value GitHub displays; do not construct one by hand.
4. Versioning policy (author decision): the first commit is "Initial reproducibility release". **No `v1.0.0`, no paper-specific tags, no GitHub Release, no Zenodo upload** until the GenAI4Health camera-ready is complete, unless the authors decide otherwise.

Use a variable so every path is explicit and nothing runs from the wrong directory:

```bash
export ARCHIVE_CHECKOUT=<ARCHIVE_CHECKOUT>                    # the archival checkout (not a git repo)
export PUBLIC_DIR="$HOME/clinical-evidence-reasoning-public"   # NEW directory, outside the archive
```

```bash
# 1. Rebuild and validate the public tree inside the archive checkout (minimum deterministic order).
#    The manifest and scope builders reference each other, so the scope file's own row can never be a fixpoint;
#    manifest -> scope -> manifest is sufficient because every other hash is current after that pass.
cd "$ARCHIVE_CHECKOUT"
source validation/.venv312/bin/activate
python scripts/validate_accepted_papers.py                   # regenerates validation/*.json first; must print OVERALL: PASS
python scripts/build_tag_freeze_manifest.py
python scripts/build_public_release_manifest.py              # 1. classify + hash every file
python scripts/build_public_v1_scope.py                      # 2. derive v1 scope from that manifest
python scripts/build_public_release_manifest.py              # 3. re-record the scope file's final hash
python scripts/build_public_release.py --v1-core             # -> dist/public_v1_preview/
python scripts/build_tag_freeze_manifest.py --check
```

```bash
# 2. Make a clean working copy OUTSIDE the archive (refuses to overwrite)
test ! -e "$PUBLIC_DIR" || { echo "$PUBLIC_DIR already exists; choose another path"; exit 1; }
cp -R "$ARCHIVE_CHECKOUT/dist/public_v1_preview" "$PUBLIC_DIR"
cd "$PUBLIC_DIR"
rm -f PREVIEW_ONLY.txt                                       # preview marker; must not be committed
```

```bash
# 3. Validate the clean copy in isolation (fresh venv inside it; .venv is git-ignored)
uv venv --python 3.12 .venv
VIRTUAL_ENV=.venv uv pip install -r requirements-reproduction.lock.txt
source .venv/bin/activate
python scripts/validate_public_release.py                    # must print OVERALL: PASS (0 problems)
python -m pytest -m public                                   # must pass
deactivate
```

```bash
# 4. git init, branch main
git init -b main
git config user.name  "<AUTHOR NAME>"                        # author-supplied
git config user.email "<PUBLISHABLE AUTHOR EMAIL>"           # author-supplied; see docs/public_identity_review.md
```

```bash
# 5. Stage ONLY the validated public contents: every path listed in MANIFEST.csv, plus MANIFEST.csv.
#    (Never `git add .` / `git add -A`; .venv, caches, etc. are not in the manifest.)
python - <<'PY' | git add --pathspec-from-file=- --pathspec-file-nul
import csv, sys
for r in csv.DictReader(open("MANIFEST.csv", newline="")):
    sys.stdout.write(r["public_path"] + "\0")
PY
git add -- MANIFEST.csv
```

```bash
# 6. Review before committing
git status --short | head -40
git status --short | grep -v '^A ' || echo "only additions staged"
git ls-files | wc -l                                         # expect (number of MANIFEST.csv rows) + 1
git ls-files | grep -Ei '\.jsonl$|nohup|\.venv|camera-ready\.pdf|LICENSE_REVIEW' || echo "no restricted-looking paths staged"   # cohorts/raw outputs are .jsonl; none belong here
git ls-files --others --exclude-standard | head              # untracked leftovers (expect only ignored/none)
```

(Only the two reconstructed/archived Figure 1 PDFs are PDFs in this tree; the camera-ready PDF is not.)

```bash
# 7. First commit (authors approve the message)
git commit -m "Initial reproducibility release"
```

Tags and remote are separate, later steps (`docs/tag_freeze_manifest.json`, `docs/release_strategy.md`, `docs/private_github_setup.md`): `git tag` for `v1.0.0` / `agenticls-2026-camera-ready` / `genai4health-2026-camera-ready`, `git remote add origin <GITHUB_REPO_URL>`, `git push`, each requiring its own explicit authorization. No remote URL is invented here.

## Why not initialize the archive itself

- A single `git add .` there would commit restricted data, provider outputs and local logs into history, which cannot be reliably scrubbed afterwards.
- `.gitignore` is a safety net, not an allow-list; the manifest-driven staging above is the allow-list.
- Keeping the archive outside git (or in a separate private repository the authors control) preserves `historical_package/` byte-for-byte without publication risk.
