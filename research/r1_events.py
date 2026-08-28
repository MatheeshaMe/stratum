#!/usr/bin/env python3
"""R-1 SIXTH + SEVENTH QUESTIONS -- event-conditioned distributions and decay.

Simple, non-ML, univariate. Per the mission: establish whether a plain
statistical relationship exists BEFORE escalating model complexity.

Events are defined on lagged microstructure only (see r1_features.py), each as
an extreme quantile of a single variable, so there is no parameter search:
the threshold is a quantile, fixed in advance at 5%/95%.

For each event, the full forward distribution at 5/15/30/60/180 min, plus the
UNCONDITIONAL baseline on the same rows. The reported quantity is the EXCESS
mean forward return in ATR units, with a circular block-bootstrap CI.
"""
import sys, os, pickle, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import situations as S, r1_features as R1

HZ = [(1,"5m"),(3,"15m"),(6,"30m"),(12,"60m"),(36,"180m")]

def block_ci(x, block, iters=1000, seed=0):
    rng = np.random.default_rng(seed); n = len(x)
    if n < block*3: return (np.nan, np.nan)
    nb = int(np.ceil(n/block)); m = np.empty(iters)
    for k in range(iters):
        st = rng.integers(0, n, nb)
        s = np.concatenate([np.take(x, np.arange(i,i+block), mode='wrap') for i in st])[:n]
        m[k] = s.mean()
    return np.percentile(m,2.5), np.percentile(m,97.5)

def fwd_returns(b, rows, st):
    c = b['c']; A = st['A']; i1 = b['i1m']; n = len(c)
    C1 = np.array([r[4] for r in rows])
    out = {}
    for hz,_ in HZ:
        r = np.full(n, np.nan)
        for i in range(60, n-1):
            a = A[i]
            if not np.isfinite(a): continue
            j1 = i1[min(i+1+hz, n-1)]
            if j1 <= i1[i+1]: continue
            r[i] = (C1[j1-1]-c[i])/a
        out[hz] = r
    return out

def main(path, tag):
    rows = pickle.load(open(path,"rb"))
    b = S.agg(rows,5); st = S.situations(b)
    Xm, names = R1.build(b)
    FR = fwd_returns(b, rows, st)
    ix = {nm:i for i,nm in enumerate(names)}
    print(f"\n{'='*104}\n{tag}   event-conditioned forward return (ATR units), "
          f"excess over same-row baseline\n{'='*104}")

    EVENTS = [
        ("OI surge (top 5% oi_d6)",            "oi_d6_pct",        "hi"),
        ("OI collapse (bottom 5%)",            "oi_d6_pct",        "lo"),
        ("aggressive BUY flow (top 5%)",       "taker_ls_z",       "hi"),
        ("aggressive SELL flow (bottom 5%)",   "taker_ls_z",       "lo"),
        ("book bid-heavy (top 5% imb 1%)",     "book_imb_1pct",    "hi"),
        ("book ask-heavy (bottom 5%)",         "book_imb_1pct",    "lo"),
        ("book imbalance SHOCK up (top 5% d6)","book_imb_1pct_d6", "hi"),
        ("book imbalance SHOCK dn (bot 5%)",   "book_imb_1pct_d6", "lo"),
        ("funding extreme high (top 5%)",      "funding_z",        "hi"),
        ("funding extreme low (bottom 5%)",    "funding_z",        "lo"),
        ("top traders max long (top 5%)",      "toptrader_sum_ls_z","hi"),
        ("top traders max short (bottom 5%)",  "toptrader_sum_ls_z","lo"),
        ("crowd long, pros not (spread top5%)","smart_dumb_spread","lo"),
    ]
    hdr = f"{'event':<38}{'n':>7}" + "".join(f"{lbl:>11}" for _,lbl in HZ)
    print(hdr); print("-"*len(hdr))
    hits = 0; tested = 0
    for lbl, feat, side in EVENTS:
        if feat not in ix: continue
        v = Xm[:, ix[feat]]
        fin = np.isfinite(v)
        if fin.sum() < 20000: continue
        thr = np.nanquantile(v[fin], 0.95 if side=="hi" else 0.05)
        ev = fin & (v >= thr if side=="hi" else v <= thr)
        row = f"{lbl:<38}{ev.sum():>7,}"
        for hz,_ in HZ:
            r = FR[hz]; m = ev & np.isfinite(r); base = np.isfinite(r) & fin
            if m.sum() < 500: row += f"{'-':>11}"; continue
            ex = r[m].mean() - r[base].mean()
            lo,hi = block_ci(r[m]-r[base].mean(), block=max(hz,6))
            tested += 1
            sig = "*" if (lo>0 or hi<0) else " "
            if lo>0 or hi<0: hits += 1
            row += f"{ex:>+10.3f}{sig}"
        print(row)
    print(f"\n  * = 95% block-bootstrap CI excludes zero")
    print(f"  cells tested {tested}, significant {hits}, "
          f"expected by chance at a=0.05 ~{0.05*tested:.1f}")

if __name__ == "__main__":
    main("data/explore_r1.pkl", "R1-EXPLORE 2023-01..2026-07 (non-sealed)")
