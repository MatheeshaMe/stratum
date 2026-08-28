#!/usr/bin/env python3
"""Regenerate every measurement in Stratum_Product_Specification-v3.md section 0.

    python3 scripts/fetch_binance.py --from 2023-01 --to 2024-12 --out data/oos
    python3 scripts/fetch_binance.py --from 2025-01 --to 2026-08 --out data/is
    python3 research/run_all.py
"""
import subprocess, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
STEPS = [
    ("0.1-0.2  bucket lift vs base rate, block-bootstrap CI", "analog_report.py"),
    ("0.3      wait clock / survival / memorylessness",       "wait_clock.py"),
    ("0.4      calibrated ML with purged CV",                 "ml_model.py"),
    ("0.5      wait vs click, EV per opportunity",            "wait_vs_click.py"),
]
for title, script in STEPS:
    print("\n" + "="*100); print(f"  {title}"); print("="*100, flush=True)
    r = subprocess.run([sys.executable, os.path.join(HERE, script)])
    if r.returncode: sys.exit(f"FAILED: {script}")
print("\nAll section-0 measurements reproduced.")
