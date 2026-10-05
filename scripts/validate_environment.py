#!/usr/bin/env python3
"""Report whether the local environment can run the frozen code.

Requirements are taken from the historical packages: runners use the
standard library (Python 3.10+); static scoring needs numpy/pandas
(requirements.txt also lists datasets for case preparation); persistent
analyses need numpy/scipy. API keys are only needed for live runs, which
are not part of reproducing archived results. Never prints keys.
"""
import importlib.util
import os
import sys

ok = sys.version_info >= (3, 10)
print(f"python {sys.version.split()[0]}: {'OK' if ok else 'NEED >=3.10'}")
for mod in ("numpy", "scipy", "pandas", "datasets"):
    present = importlib.util.find_spec(mod) is not None
    print(f"{mod} (analysis): {'OK' if present else 'missing'}")
for var in ("GEMINI_API_KEY", "GROQ_API_KEY"):
    print(f"{var} set (live runs only): {'yes' if os.environ.get(var) else 'no'}")
sys.exit(0 if ok else 1)
