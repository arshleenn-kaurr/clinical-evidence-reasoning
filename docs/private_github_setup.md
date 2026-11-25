# Private GitHub setup (future sequence — NOT executed)

No repository, remote, branch, commit, tag, release or Actions run exists. Every step below needs the authors' explicit go-ahead. No URL is invented: `<GITHUB_REPO_URL>` is a placeholder for the URL GitHub shows after the repository is created.

## Preconditions

- Code license: MIT, applied (`LICENSE`); manifests regenerated and public validation re-run from an isolated copy.
- Author emails removed from the public tree (`docs/public_identity_review.md`, resolved).
- A clean working copy created and committed locally per `docs/git_initialization_plan.md` steps 1–7 (the archive checkout is never the repository).

## Sequence

1. **Create the repository** (authors, in GitHub UI or `gh`), name `clinical-evidence-reasoning`, **visibility PRIVATE**, no README/.gitignore/license added by GitHub (the first push supplies them), default branch `main`.
   ```bash
   gh repo create clinical-evidence-reasoning --private --description "<ABOUT TEXT from docs/github_release_metadata.md>"   # only after authorization; no --source/--push
   ```
   (or create in the web UI and skip this command). Disable Discussions; enable Issues (`docs/github_release_metadata.md`).
2. **Add the remote** from the clean working copy:
   ```bash
   git remote add origin <GITHUB_REPO_URL>
   git remote -v
   ```
3. **Push `main` only** (no tags yet):
   ```bash
   git push -u origin main
   ```
4. **Watch the real GitHub Actions run** (`.github/workflows/reproducibility.yml`). Expected:
   - `public-integrity` job: PASS (manifest/hash integrity, link check, leak scans, `pytest -m public`).
   - `full-archive-reproduction` job: detects the missing restricted inputs and **skips cleanly** (success, not failure). If it instead fails or tries to run archive tests, that is a workflow bug to fix before going further.
   - First run on a real runner is the first time `docs/github_actions_preflight.md` is tested outside the author's machine; fix forward with a new commit, not a force-push of history, unless nothing else has been shared.
5. **Confirm the Actions result** in the UI/`gh run list` and record it in `docs/final_release_checklist.md` ("Actual CI run passes").
6. **Apply metadata** from `docs/github_release_metadata.md` (About description, the 7 topics). Keep social preview optional.
7. **Review the private repository** as an outsider would: README first screen, `LICENSE` and rights notices, no restricted files (`git ls-files` vs `docs/v1_withheld_artifacts.md`), no author emails unless intended, no local paths, file count equals `MANIFEST.csv` + 1. Invite any co-author/reviewer as collaborator rather than making it public.
8. **Stop.** Versioning policy (author decision): **no `v1.0.0`, no paper-specific tags, no GitHub Release, no Zenodo upload** until the GenAI4Health camera-ready is complete, unless the authors decide otherwise. Making the repository public is also a separate later authorization (`docs/release_strategy.md`, `docs/archival_plan.md`).

## Rollback

Before anything is public, a mistaken private repository can be deleted and recreated; history rewriting is only a last resort. This is why the clean-tree-first procedure matters: restricted content must never enter any commit.
