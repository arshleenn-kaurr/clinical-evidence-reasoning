# GitHub Actions pre-flight (local, 2026-10-04)

Workflow: `.github/workflows/reproducibility.yml` (jobs `public-integrity`, `full-archive-reproduction`). **Nothing was pushed; the workflow has not run on a GitHub runner.** This records the exact commands run locally. No secrets are needed and no model API is called (the scripts contain no `os.environ`/key reads; the workflow declares `permissions: contents: read` and no `secrets.*`).

## Job 1 — `public-integrity` (run on an isolated copy of `dist/public_v1_preview/`, with its own `.venv` **inside** the checkout, as CI does)

```bash
uv venv --python 3.12 .venv          # uv 0.12.23, the version the workflow pins
VIRTUAL_ENV=.venv uv pip install -r requirements-reproduction.lock.txt
.venv/bin/python scripts/validate_public_release.py     # -> OVERALL: PASS (0 problem(s)), exit 0
.venv/bin/python -m pytest -m public -v                 # -> 17 passed, exit 0
```

## Job 2 — `full-archive-reproduction`

- **On the stripped public tree:** the marker-file check (`experiments/static_conflict/historical_package/evidence_not_vote_starter/data/replication_cases.jsonl`) reports `present=false`, so every subsequent step is skipped (job succeeds, not fails). Verified by running the workflow's own bash snippet in the isolated copy.
- **On the full archive (steps run locally):** `python scripts/verify_hashes.py` → `ALL HASHES OK`; `python scripts/validate_accepted_papers.py` → `OVERALL: PASS`; `python -m pytest -m archive` → 36 passed. (The "no `historical_package/` change" step uses `git status`, which cannot run: no git repository exists; equivalent local check: no `historical_package` file modified during Phase 5B.)

## Two real problems found by this pre-flight, and fixed

1. **`.venv` inside the checkout broke `public-integrity`.** CI creates `.venv/` in the workspace, but `validate_public_release.py` step 13 (unmanifested files) and step 12 (secret/path scan) did not ignore it: 6,332 spurious failures (site-packages files, plus example home-directory strings inside third-party packages). Fixed: `.venv` added to the shared `IGNORE_DIR_NAMES` (`scripts/build_public_release_manifest.py`) and step 12 now applies the same ignore set as step 13. Re-run: PASS.
2. **The archive job's `pytest tests/` would fail on a full-archive checkout.** The `@public` tests legitimately fail there (restricted files and a local-path-bearing `nohup.out` are present; `validate_accepted_papers.py` regenerates `validation/*.json`, so manifest hashes drift). Fixed: the archive job now runs `pytest -m archive`; the `@public` tests remain the `public-integrity` job's responsibility.

## Not verified here

Behavior of `astral-sh/setup-uv@v3`, `actions/checkout@v4`, Ubuntu runner specifics, and wall-clock time on a GitHub runner. These can only be confirmed by an actual run, which requires a repository (separate authorization).
