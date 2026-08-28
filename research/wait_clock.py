"""How long does a situation take to resolve? Survival analysis on bars-to-touch.

This is the measurement that ends an open-ended wait. If 70% of the resolution
happens in the first 8 bars, then a situation still unresolved at bar 12 is not
"about to go" -- it is dead, and the correct action is to stand down.
"""
import sys, os, pickle, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import situations as S

def clock(rows, tag, k_atr=2.0, horizon=36):
    b = S.agg(rows,5); st = S.situations(b); lab = S.buckets(b,st)
    res, bars = S.triple_barrier(rows, b, st, k_atr=k_atr, horizon=horizon,
                                 side=+1, rr=1.0)
    ok = res >= 0
    print(f"\n{tag}   symmetric ±{k_atr} ATR, {horizon} bars ({horizon*5}min) max")
    print(f"  {'bucket':<24}{'n':>7}{'resolved':>10}{'median':>8}"
          f"{'  survival: still unresolved after k bars'}")
    print(f"  {'':<24}{'':>7}{'by end':>10}{'bars':>8}"
          f"{'   b3':>7}{'b6':>7}{'b12':>7}{'b18':>7}{'b24':>7}")
    for bid in (0,1,2,3,4,5,6):
        m = ok & (lab == bid)
        if m.sum() < 200: continue
        resolved = res[m] != 2
        bt = bars[m][resolved]
        if len(bt) < 100: continue
        surv = [ (bars[m] > k).mean() if True else 0 for k in (3,6,12,18,24) ]
        # survival must count unresolved-at-vertical as still alive
        alive = lambda k: ((res[m]==2) | (bars[m] > k)).mean()
        print(f"  {S.BUCKET_NAMES[bid]:<24}{m.sum():>7}{resolved.mean():>10.1%}"
              f"{np.median(bt):>8.0f}"
              + "".join(f"{alive(k):>7.0%}" for k in (3,6,12,18,24)))

    # the decisive number: given still unresolved at bar k, what happens next?
    print(f"\n  Conditional on STILL unresolved at bar k -- does waiting longer help?")
    print(f"  {'k':>4}{'n still open':>14}{'eventually up':>15}{'eventually dn':>15}"
          f"{'never resolves':>16}")
    for k in (0, 3, 6, 12, 18):
        m = ok & (bars > k)
        if m.sum() < 200: continue
        r = res[m]
        print(f"  {k:>4}{m.sum():>14,}{(r==1).mean():>15.1%}"
              f"{(r==0).mean():>15.1%}{(r==2).mean():>16.1%}")

if __name__ == "__main__":
    for tag, p in (("IS  2025-26","data/is/BTCUSDT-1m.pkl"),
                   ("OOS 2023-24","data/oos/BTCUSDT-1m.pkl")):
        clock(pickle.load(open(p,"rb")), tag)
