# Manifests (registry)

[`manifest_registry.csv`](manifest_registry.csv) lists every historical `.sha256`, `SHA256SUMS.txt` and JSON freeze manifest recovered, at its in-package path. `scripts/verify_hashes.py` verifies all of them in place (95 entries). One known discrepancy: the `posthoc_contrasts.py` script hash.
