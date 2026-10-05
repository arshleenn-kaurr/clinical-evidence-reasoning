# data

Frozen inputs live inside the historical packages, so each package's manifests verify in place. This folder holds **registries**, not extra copies.

- [`frozen/`](frozen/): `cohort_registry.csv` lists every frozen input by sha256 and every in-repo location.
- [`manifests/`](manifests/): `manifest_registry.csv` lists every historical hash/freeze manifest.
- `samples/`: TODO (small public samples, only if licensing allows).

Frozen inputs contain MEDAL-derived Cochrane and AHA text. See `docs/public_release_audit.md`.
