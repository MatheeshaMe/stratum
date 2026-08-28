#!/usr/bin/env python3
"""P2+P3 -- bucket x stop-width x target surface, with REALISED R.

Corrected after C2 (see CORRECTIONS.md): a trade unresolved at the vertical
barrier is marked out at the close, not charged a full stop. Wider barriers
resolve less often, so the old treatment penalised exactly the cells P1 said
were most promising.

Reports for every cell:
    unres%  fraction still open at the vertical barrier (validity check on P1)
    grossR  mean realised R before cost
    costR   round-trip cost in R at that stop width
    netR    grossR - costR                    <- the only number that matters
    CI      circular block bootstrap on netR
"""
import sys, os, pickle, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import situations as S

MAKER, TAKER, HALF = 1.5/1e4, 4.5/1e4, 0.63/1e4
COSTS = {"maker/taker": MAKER+TAKER+HALF, "maker/maker": MAKER+MAKER,
         "taker/taker": (TAKER+HALF)*2}

def realised_R(rows, b, st, k_atr, horizon, side, rr):
    """+rr target-first, -1 stop-first, else markout/stop_distance."""
    H1 = realised_R.H1; L1 = realised_R.L1; C1 = realised_R.C1
    c = b['c']; A = st['A']; i1 = b['i1m']; n = len(c)
    R = np.full(n, np.nan); unres = np.zeros(n, dtype=bool)
    for i in range(60, n - 1):
        a = A[i]
        if not np.isfinite(a): continue
        d = k_atr*a; entry = c[i]
        tgt = entry + side*d*rr; stp = entry - side*d
        j0 = i1[i+1]; j1 = i1[min(i+1+horizon, n-1)]
        if j1 <= j0: continue
        sh = H1[j0:j1]; sl = L1[j0:j1]
        if side > 0: w = sh >= tgt; s = sl <= stp
        else:        w = sl <= tgt; s = sh >= stp
        wi = np.argmax(w) if w.any() else 10**9
        si = np.argmax(s) if s.any() else 10**9
        if wi == 10**9 and si == 10**9:
            R[i] = side*(C1[j1-1] - entry)/d; unres[i] = True
        elif si <= wi: R[i] = -1.0            # ties -> stop
        else:          R[i] = float(rr)
    return R, unres

def block_ci(x, block, iters=1200, seed=0):
    rng = np.random.default_rng(seed); n = len(x)
    if n < block*3: return (np.nan, np.nan)
    nb = int(np.ceil(n/block)); m = np.empty(iters)
    for k in range(iters):
        stt = rng.integers(0, n, nb)
        s = np.concatenate([np.take(x, np.arange(i,i+block), mode='wrap') for i in stt])[:n]
        m[k] = s.mean()
    return np.percentile(m, 2.5), np.percentile(m, 97.5)

def surface(rows, tag, k_list=(4,7,10,14,20), rr_list=(1.0,1.5,2.0,3.0),
            exec_style="maker/taker", sides=(+1,-1), buckets=(1,2,3,4,5,6),
            verbose=True):
    b = S.agg(rows,5); st = S.situations(b); lab = S.buckets(b,st)
    realised_R.H1 = np.array([r[2] for r in rows])
    realised_R.L1 = np.array([r[3] for r in rows])
    realised_R.C1 = np.array([r[4] for r in rows])
    c = b['c']; A = st['A']; cb = COSTS[exec_style]
    hits = []
    for side in sides:
        sname = "LONG" if side>0 else "SHORT"
        if verbose:
            print(f"\n{'='*112}\n{tag}  {sname}  {exec_style} ({cb*1e4:.2f} bps RT)\n{'='*112}")
            print(f"{'bucket':<22}{'kATR':>5}{'stop%':>7}{'rr':>5}{'n':>7}{'unres%':>8}"
                  f"{'grossR':>8}{'costR':>7}{'netR':>8}{'   95% CI netR':>20}")
        for k in k_list:
            hz = int(max(36, 4*k*k))
            stop_pct = k*A/c
            for rr in rr_list:
                R, unres = realised_R(rows, b, st, k, hz, side, rr)
                base_ok = np.isfinite(R) & np.isfinite(stop_pct) \
                          & (stop_pct >= 0.006) & (stop_pct <= 0.05)
                if base_ok.sum() < 500: continue
                med_stop = np.median(stop_pct[base_ok]); costR = cb/med_stop
                for bid in buckets:
                    m = base_ok & (lab==bid)
                    if m.sum() < 150: continue
                    g = R[m].mean(); net = g - costR
                    lo,hi = block_ci(R[m]-costR, block=min(hz,60))
                    flag = "  <<< POSITIVE" if lo > 0 else ""
                    if verbose:
                        print(f"{S.BUCKET_NAMES[bid][:20]:<22}{k:>5}{med_stop*100:>7.2f}{rr:>5.1f}"
                              f"{m.sum():>7}{unres[m].mean():>8.1%}{g:>+8.3f}{costR:>7.3f}"
                              f"{net:>+8.3f}   [{lo:+.3f},{hi:+.3f}]{flag}")
                    if lo > 0: hits.append(dict(bucket=bid,k=k,rr=rr,side=side,
                                 exec=exec_style,n=int(m.sum()),net=net,lo=lo,hi=hi,
                                 stop=med_stop,unres=float(unres[m].mean())))
    return hits

if __name__ == "__main__":
    EX = pickle.load(open("data/is/BTCUSDT-1m.pkl","rb"))
    hits = surface(EX, "EXPLORE 2025-01..2026-07")
    print(f"\n\nCELLS WITH 95% CI ABOVE ZERO: {len(hits)}")
    for h in sorted(hits, key=lambda z:-z['net']):
        print(f"   B{h['bucket']} {'LONG' if h['side']>0 else 'SHORT':<5} "
              f"k={h['k']:<3} rr={h['rr']:<4} stop={h['stop']*100:.2f}% "
              f"n={h['n']:<6} unres={h['unres']:.0%} net={h['net']:+.3f}R "
              f"CI[{h['lo']:+.3f},{h['hi']:+.3f}]")
    pickle.dump(hits, open("/tmp/p2_hits.pkl","wb"))
