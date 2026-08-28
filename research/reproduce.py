#!/usr/bin/env python3
"""Regenerate the headline table in STRATUM.md section 0.

Usage:
    python3 scripts/fetch_binance.py --from 2023-01 --to 2024-12 --out data/oos
    python3 scripts/fetch_binance.py --from 2025-01 --to 2026-08 --out data/is
    python3 research/reproduce.py

Every number printed here is what section 0 of STRATUM.md claims. If these
do not reproduce, the document is wrong and should be corrected.
"""
import os, pickle, sys, statistics as st, math
sys.path.insert(0, os.path.dirname(__file__))
import engine

def load(p):
    if not os.path.exists(p):
        sys.exit(f"missing {p} -- run scripts/fetch_binance.py first")
    return pickle.load(open(p, "rb"))

def row(label, period, r):
    if not r or r["n"] < 20:
        print(f"{label:<44}{period:<6}  insufficient trades"); return
    print(f"{label:<44}{period:<6}{r['n']:>6}{r['win']*100:>7.1f}"
          f"{r['net']:>+9.3f}{r['cost']:>8.3f}{r['gross']:>+9.3f}{r['t']:>+8.2f}")

def main():
    IS  = load("data/is/BTCUSDT-1m.pkl")
    OOS = load("data/oos/BTCUSDT-1m.pkl")

    print("STRATUM.md section 0 -- reproduction")
    print("1h decision TF, 2.0 ATR stop, 1.5R target, maker in / taker out\n")
    print(f"{'configuration':<44}{'period':<6}{'n':>6}{'win%':>7}"
          f"{'net R':>9}{'cost':>8}{'gross':>9}{'t':>8}")
    print("-" * 97)

    cfgs = [
        ("unconditional level touch",            dict()),
        ("v1 T1: reject wick + weak second push", dict(need_wick=1, vol_weak=0.8)),
        ("reject wick only",                      dict(need_wick=1)),
        ("wick + climax volume (the IS mirage)",  dict(need_wick=1, need_climax=1)),
    ]
    for label, kw in cfgs:
        for period, rows in (("IS", IS), ("OOS", OOS)):
            row(label, period, engine.run(rows, TF=60, stop_atr=2.0, rr=1.5, **kw))
        print()

    print("Expected (STRATUM.md section 0):")
    print("  unconditional touch          IS net -0.033  OOS net -0.126")
    print("  v1 T1 wick+weak              IS net -0.160  OOS net -0.191   <- falsified")
    print("  wick+climax                  IS net +0.186  OOS net +0.007   <- did not replicate")

if __name__ == "__main__":
    main()
