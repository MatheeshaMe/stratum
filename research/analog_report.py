"""Does the situation actually move the odds? Base-rate lift with honest n."""
import sys, os, pickle, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import situations as S

def block_bootstrap_ci(x, block, iters=2000, seed=0):
    """Overlapping forward windows are autocorrelated. A naive binomial CI is a
    lie. Circular block bootstrap gives an honest interval."""
    rng = np.random.default_rng(seed); n = len(x)
    if n < block*3: return (np.nan, np.nan)
    nb = int(np.ceil(n/block)); means = np.empty(iters)
    for k in range(iters):
        st = rng.integers(0, n, nb)
        s = np.concatenate([np.take(x, np.arange(i, i+block), mode='wrap') for i in st])[:n]
        means[k] = s.mean()
    return np.percentile(means, 2.5), np.percentile(means, 97.5)

def analyse(rows, label, k_atr=2.0, horizon=12, sides=(+1,-1)):
    b = S.agg(rows, 5); st = S.situations(b); lab = S.buckets(b, st)
    out = {}
    for side in sides:
        res, bars = S.triple_barrier(rows, b, st, k_atr=k_atr, horizon=horizon, side=side)
        valid = res >= 0
        base = res[valid]
        pw = (base == 1).mean(); pl = (base == 0).mean(); pi = (base == 2).mean()
        sname = "LONG" if side > 0 else "SHORT"
        print(f"\n{label}  {sname}  barrier=±{k_atr} ATR  horizon={horizon}x5m "
              f"({horizon*5}min)")
        print(f"  BASE RATE (all {valid.sum():,} bars): "
              f"win-first {pw:.1%}  loss-first {pl:.1%}  still-inside {pi:.1%}")
        print(f"  {'bucket':<24}{'n':>7}{'win1st':>8}{'loss1st':>8}{'inside':>8}"
              f"{'LIFT':>8}{'95% CI on lift':>22}")
        for bid in (1,2,3,4,5,6):
            m = valid & (lab == bid)
            if m.sum() < 30: 
                print(f"  {S.BUCKET_NAMES[bid]:<24}{m.sum():>7}   -- too few --"); continue
            w = (res[m] == 1).astype(float)
            lift = w.mean() - pw
            lo, hi = block_bootstrap_ci(w - pw, block=horizon)
            flag = "" if (lo < 0 < hi) else "  <-- signal"
            print(f"  {S.BUCKET_NAMES[bid]:<24}{m.sum():>7}{w.mean():>8.1%}"
                  f"{(res[m]==0).mean():>8.1%}{(res[m]==2).mean():>8.1%}"
                  f"{lift:>+8.1%}   [{lo:+.1%}, {hi:+.1%}]{flag}")
            out[(sname,bid)] = (m.sum(), w.mean(), lift, lo, hi)
    return out

if __name__ == "__main__":
    IS  = pickle.load(open("data/is/BTCUSDT-1m.pkl","rb"))
    OOS = pickle.load(open("data/oos/BTCUSDT-1m.pkl","rb"))
    for k, hz in ((2.0, 12), (5.0, 36)):
        a = analyse(IS,  f"IS  2025-01..2026-07", k_atr=k, horizon=hz)
        c = analyse(OOS, f"OOS 2023-01..2024-12", k_atr=k, horizon=hz)
        print("\n  --- sign stability of lift, IS vs OOS ---")
        for key in sorted(set(a) & set(c)):
            la, lc = a[key][2], c[key][2]
            ok = "STABLE" if la*lc > 0 else "FLIPS"
            print(f"    {key[0]:<6}{S.BUCKET_NAMES[key[1]]:<24} IS {la:+.1%}  OOS {lc:+.1%}   {ok}")
        print("\n" + "="*100)
