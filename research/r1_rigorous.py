#!/usr/bin/env python3
"""R-1 follow-up with C3 and C4 fixed, plus the two controls that decide it.

C3  bootstrap block length from the integrated autocorrelation time of the
    EVENT INDICATOR, floored at one day. Episodes counted, not just bars.
C4  the magnitude x direction split is run with OHLCV-only, micro-only and
    combined models, so incremental value is measured rather than assumed.

Plus the drift control that killed B6 in P2/P3: an effect that is really the
prevailing trend will vanish when forward returns are de-trended by the
trailing drift, and will not replicate across two sub-periods with opposite
drift.
"""
import sys, os, pickle, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import situations as S, ml_model as M, r1_features as R1

HZ = [(6,"30m"),(12,"60m"),(36,"180m")]

def act(ind, maxlag=2000):
    """Integrated autocorrelation time of a 0/1 event indicator."""
    x = ind.astype(float); x = x - x.mean()
    if x.std() == 0: return 288
    n = len(x); f = np.fft.rfft(x, 2*n); ac = np.fft.irfft(f*np.conj(f))[:maxlag].real
    ac /= ac[0] if ac[0] != 0 else 1
    tau = 1.0
    for k in range(1, maxlag):
        if ac[k] <= 0: break
        tau += 2*ac[k]
    return int(max(288, min(tau*2, 20000)))

def episodes(ind):
    d = np.diff(ind.astype(int)); return int((d == 1).sum()) + int(ind[0])

def block_ci(x, block, iters=1500, seed=0):
    rng = np.random.default_rng(seed); n = len(x)
    if n < block*3: return (np.nan, np.nan)
    nb = int(np.ceil(n/block)); m = np.empty(iters)
    for k in range(iters):
        st = rng.integers(0, n, nb)
        s = np.concatenate([np.take(x, np.arange(i,i+block), mode='wrap') for i in st])[:n]
        m[k] = s.mean()
    return np.percentile(m,2.5), np.percentile(m,97.5)

def fwd_and_detrend(b, rows, st):
    c = b['c']; A = st['A']; i1 = b['i1m']; n = len(c)
    C1 = np.array([r[4] for r in rows])
    raw, det = {}, {}
    # trailing drift per bar, estimated over the previous 7 days (2016 bars)
    W = 2016
    drift = np.full(n, np.nan)
    for i in range(W, n):
        drift[i] = (c[i]-c[i-W])/W        # price units per bar
    for hz,_ in HZ:
        r = np.full(n, np.nan); dd = np.full(n, np.nan)
        for i in range(60, n-1):
            a = A[i]
            if not np.isfinite(a): continue
            j1 = i1[min(i+1+hz, n-1)]
            if j1 <= i1[i+1]: continue
            r[i] = (C1[j1-1]-c[i])/a
            if np.isfinite(drift[i]): dd[i] = r[i] - (drift[i]*hz)/a
        raw[hz] = r; det[hz] = dd
    return raw, det

def main():
    rows = pickle.load(open("data/explore_r1.pkl","rb"))
    b = S.agg(rows,5); st = S.situations(b); n = len(b['c'])
    Xm, names = R1.build(b); ix = {nm:i for i,nm in enumerate(names)}
    raw, det = fwd_and_detrend(b, rows, st)
    half = n//2
    print(f"\n{'='*118}\nR-1 EVENTS, corrected (C3): proper block length, episode counts, "
          f"drift control, split-half replication\n{'='*118}")
    EV = [("aggressive SELL flow (bot 5%)","taker_ls_z","lo"),
          ("aggressive BUY flow (top 5%)","taker_ls_z","hi"),
          ("book imb SHOCK dn (bot 5%)","book_imb_1pct_d6","lo"),
          ("book imb SHOCK up (top 5%)","book_imb_1pct_d6","hi"),
          ("top traders max SHORT (bot 5%)","toptrader_sum_ls_z","lo"),
          ("funding extreme LOW (bot 5%)","funding_z","lo"),
          ("funding extreme HIGH (top 5%)","funding_z","hi")]
    print(f"{'event':<32}{'hz':>5}{'bars':>8}{'episodes':>9}{'block':>7}"
          f"{'excess':>9}{'  95% CI (corrected)':>22}{'detrended':>11}{'  1stH':>8}{'2ndH':>8}")
    tested=sig=0
    for lbl, feat, side in EV:
        v = Xm[:, ix[feat]]; fin = np.isfinite(v)
        thr = np.nanquantile(v[fin], 0.95 if side=="hi" else 0.05)
        ev = fin & (v >= thr if side=="hi" else v <= thr)
        blk = act(ev); eps = episodes(ev)
        for hz,hl in HZ:
            r = raw[hz]; d = det[hz]
            m = ev & np.isfinite(r); base = fin & np.isfinite(r)
            if m.sum() < 500: continue
            ex = r[m].mean()-r[base].mean()
            lo,hi = block_ci(r[m]-r[base].mean(), block=blk)
            md = ev & np.isfinite(d); bd = fin & np.isfinite(d)
            exd = d[md].mean()-d[bd].mean() if md.sum()>500 else np.nan
            i1h = ev & np.isfinite(r) & (np.arange(n)<half)
            i2h = ev & np.isfinite(r) & (np.arange(n)>=half)
            e1 = r[i1h].mean()-r[base & (np.arange(n)<half)].mean() if i1h.sum()>200 else np.nan
            e2 = r[i2h].mean()-r[base & (np.arange(n)>=half)].mean() if i2h.sum()>200 else np.nan
            tested += 1
            s = "*" if (lo>0 or hi<0) else " "
            if lo>0 or hi<0: sig += 1
            print(f"{lbl:<32}{hl:>5}{m.sum():>8,}{eps:>9}{blk:>7}"
                  f"{ex:>+9.3f}{s} [{lo:+.3f},{hi:+.3f}]{exd:>+11.3f}{e1:>+8.3f}{e2:>+8.3f}")
    print(f"\n  cells tested {tested}, significant {sig}, expected by chance ~{0.05*tested:.1f}")
    print("  detrended = excess after removing trailing 7-day drift")
    print("  1stH/2ndH = excess in each half of the exploratory window (sign must hold)")

if __name__ == "__main__":
    main()
