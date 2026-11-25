# Reproduction environment

**RELEASE TOOLING.** This document and the files it describes (`.python-version`, `requirements-reproduction.txt`, `requirements-reproduction.lock.txt`) are newly authored for Phase 4. They pin a verified reproduction environment; they are not historical execution artifacts.

## Why Python 3.12 and scipy 1.16.3

- **Python 3.12** was chosen as a conservative, widely supported version. No recovered package pins a specific Python; `pyproject.toml`'s `requires-python = ">=3.10"` comes from the frozen Groq runner's own README. Historical `.pyc` files in the static package are `cpython-314` (and one `cpython-310`), and the AgenticLS packages are `cpython-313` (see `docs/environment_validation.md`) — none of that is 3.12. **3.12 is not a claim about the historical execution environment.** It is simply a current, stable version this reproduction environment is pinned to.
- **scipy==1.16.3** is pinned because Phase 3 showed that `posthoc_contrasts.py`'s archived outputs reproduce **byte-for-byte** under scipy 1.16.x, while scipy ≥1.17 changes `scipy.stats.beta.ppf` by about 1 ULP in one cell of `binomial_proportions_exact.csv` (a `NUMERIC_MATCH`, not `EXACT_MATCH`; see `docs/posthoc_hash_investigation.md`). numpy and pandas versions were not found to be output-sensitive for the archived inputs (tested at numpy 2.5.3 / pandas 3.0.6 under both Python 3.14 and 3.12).

## Two environments, not confused

| | HISTORICAL EXECUTION ENVIRONMENT | CURRENT VERIFIED REPRODUCTION ENVIRONMENT |
|---|---|---|
| Python | partially unknown: `.pyc` evidence suggests 3.14 (static) and 3.13 (AgenticLS); not independently confirmed | **3.12.15** (pinned; see `.python-version`) |
| numpy / pandas | unknown, not recorded anywhere in the recovered packages | 2.5.3 / 3.0.6 |
| scipy | unknown; inferred ≤1.16.x from output reproduction | **1.16.3** (pinned) |
| OS / hardware | unknown | macOS (validated); Linux via CI (`.github/workflows/reproducibility.yml`) |

Never state or imply that the pinned environment *was* the historical one — only that it reproduces the archived outputs exactly.

## Package-version sensitivity (known)

| Package | Sensitivity |
|---|---|
| scipy | `scipy.stats.beta.ppf` (used for exact Clopper-Pearson CIs in `posthoc_contrasts.py`) changed between 1.16.x and 1.17.0, by ~4×10⁻¹⁷ in the one case tested (replication EDR1 lower CI bound). Pin to 1.16.3. |
| numpy, pandas | No sensitivity found across numpy 2.5.3 / pandas 3.0.6 on Python 3.14.8 and 3.12.15. Not exhaustively tested against other versions. |
| Python | No sensitivity found between 3.14.8 and 3.12.15 for any archived accepted-paper output. |

## Dependencies actually required (and why)

| File | Imports |
|---|---|
| `score_results.py` (prespecified) | numpy, pandas |
| `posthoc_contrasts.py` (post-hoc) | numpy, pandas, scipy |
| `analyze_sequential_gemini.py`, `analyze_aligned_control.py` (AgenticLS) | standard library only |
| `prepare_cases.py` (case preparation; not re-run) | `datasets` (per archived `requirements.txt`) |
| `scripts/phase3_*.py`, `scripts/validate_accepted_papers.py` | numpy, pandas, scipy |
| `tests/` | pytest |

`requirements-reproduction.txt` pins exactly these five top-level packages. `requirements-reproduction.lock.txt` is the full resolved, hashed dependency closure (generated with `uv pip compile --generate-hashes`), so installs are deterministic and verifiable.

## Setup

```bash
# Install uv (or use any tool that can create a 3.12 venv and install from the lockfile)
curl -LsSf https://astral.sh/uv/install.sh | sh   # or: pipx install uv / brew install uv

uv venv --python 3.12 .venv
VIRTUAL_ENV=.venv uv pip install -r requirements-reproduction.lock.txt
source .venv/bin/activate
python scripts/validate_accepted_papers.py
```

Equivalently, without `uv`:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-reproduction.txt   # or the .lock.txt for pinned transitive deps
python scripts/validate_accepted_papers.py
```

This installs only the reproduction toolchain; it never calls an external API and never writes into any `historical_package/`.
