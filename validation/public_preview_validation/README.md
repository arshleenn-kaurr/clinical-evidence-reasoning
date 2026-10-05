# Public preview validation (Phase 5, step 6)

Evidence that `dist/public_release_preview/` is self-sufficient: both the
public-only CLI validator and the public-marked pytest suite were run from
a copy of the preview placed OUTSIDE this repository entirely (so there is
no possibility of accidentally resolving a file from the private archive),
using the exact sequence:

```
rm -rf <isolated>
cp -R dist/public_release_preview <isolated>
cd <isolated>
python scripts/validate_public_release.py   # -> PASS, 0 problems
python -m pytest -m public -v                 # -> 15 passed
```

See `logs/validate_public_release_isolated.log` and `logs/pytest_public_isolated.log`.

This does not (and is not meant to) reproduce the accepted-paper scientific
analyses — that requires the full archive (`scripts/validate_accepted_papers.py`),
which needs `LICENSE_REVIEW` inputs intentionally excluded from the preview.
See `docs/public_dependency_audit.md`.
