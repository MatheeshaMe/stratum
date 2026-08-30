#!/usr/bin/env python3
"""R-3 core experiment -- do observable states move P(target first) enough?

Baseline is the UNCONDITIONAL value of the same cell, never the martingale.
That removes the vertical-barrier selection effect, which dominates the raw
deviation surface and is not an edge.

Only the reachable corner is searched: spans where the required deviation
(cost/(S+T)) is under ~4pp. Searching cells needing 20-40pp would be theatre.

States are built from information already in Stratum -- no new indicators.
Every state is a fixed quantile cut, so there is no threshold search.
"""
import sys, os, pickle, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import situations as S, ml_model as M, r3_paths as P
from sklearn.ensemble import HistGradientBoostingRegressor

COST = {"maker/maker":0.030/100, "maker/taker":0.0663/100, "taker/taker":0.1026/100}
CELLS = [(0.40,0.50),(0.50,0.50),(0.50,0.75),(0.75,0.75),
         (0.75,1.00),(1.00,1.00),(1.00,1.50)]          # (stop%, target%)
HZ = 120

def block_ci(x, block, iters=1200, seed=0):
    rng = np.random.default_rng(seed); n = len(x)
    if n < block*3: return (np.nan, np.nan)
    nb = int(np.ceil(n/block)); m = np.empty(iters)
    for k in range(iters):
        st = rng.integers(0, n, nb)
        s = np.concatenate([np.take(x, np.arange(i,i+block), mode='wrap') for i in st])[:n]
        m[k] = s.mean()
    return np.percentile(m,2.5), np.percentile(m,97.5)

def build_states(rows, b, st):
    """Fixed-quantile states from existing Stratum information."""
    c=b['c']; h=b['h']; l=b['l']; v=b['v']; A=st['A']; n=len(c)
    atrp = A/c
    def pct(x, w=2016):
        o=np.full(n,np.nan)
        for i in range(w,n):
            o[i]=(x[i-w:i] < x[i]).mean()
        return o
    vol_pct = pct(atrp)
    ret6  = np.concatenate([[np.nan]*6,(c[6:]-c[:-6])/c[:-6]])/np.where(atrp==0,np.nan,atrp)
    ret36 = np.concatenate([[np.nan]*36,(c[36:]-c[:-36])/c[:-36]])/np.where(atrp==0,np.nan,atrp)
    rng12 = np.full(n,np.nan)
    for i in range(12,n): rng12[i]=(h[i-12:i].max()-l[i-12:i].min())/c[i]
    compress = pct(rng12/np.where(atrp==0,np.nan,atrp))
    vma = np.convolve(v,np.ones(20)/20,'full')[:n]
    vshock = v/np.where(vma==0,np.nan,vma)
    hi24 = np.full(n,np.nan); lo24=np.full(n,np.nan)
    for i in range(288,n):
        hi24[i]=(h[i-288:i].max()-c[i])/c[i]/np.where(atrp[i]==0,np.nan,atrp[i])
        lo24[i]=(c[i]-l[i-288:i].min())/c[i]/np.where(atrp[i]==0,np.nan,atrp[i])
    hour = ((b['t']//3600000)%24)
    return dict(vol_pct=vol_pct, ret6=ret6, ret36=ret36, compress=compress,
                vshock=vshock, hi24=hi24, lo24=lo24, hour=hour, atrp=atrp)

def main():
    rows = pickle.load(open("data/explore_r1.pkl","rb"))
    b = S.agg(rows,5); st = S.situations(b)
    n5 = len(b['c'])
    _end = b['i1m'][1:]-1
    _ok = (_end > 60) & (_end < len(rows)-P.HMAX-2)
    entry = _end[_ok]
    idx5 = np.arange(len(b['c'])-1)[_ok]
    print(f"R-3 conditional test: {len(entry):,} aligned 5m entries, horizon {HZ}m")

    STA = build_states(rows, b, st)
    # expected-magnitude model (OHLCV only -- the strongest thing we have)
    Xo,_,_,_,_,_ = M.build_matrix(rows, k_atr=7.0, rr=1.5, horizon=96)
    fwd_rng = np.full(n5, np.nan)
    H1=np.array([r[2] for r in rows]); L1=np.array([r[3] for r in rows]); i1=b['i1m']
    for i in range(60, n5-1):
        a=st['A'][i]
        if not np.isfinite(a): continue
        j0=i1[i+1]; j1=i1[min(i+1+24,n5-1)]
        if j1<=j0: continue
        fwd_rng[i]=(H1[j0:j1].max()-L1[j0:j1].min())/a
    okm = np.isfinite(Xo).all(1)&np.isfinite(fwd_rng)
    ii = np.where(okm)[0]; mag=np.full(n5,np.nan)
    for tr,te in M.purged_folds(n5, ii, 24):
        w=M.uniqueness_weights(tr,24,n5)
        m=HistGradientBoostingRegressor(max_depth=4,max_iter=200,learning_rate=0.05,
              min_samples_leaf=200,random_state=0)
        m.fit(Xo[tr],fwd_rng[tr],sample_weight=w); mag[te]=m.predict(Xo[te])

    def q(x, lo, hi):
        v = x[idx5]; f=np.isfinite(v)
        if f.sum()<5000: return None
        a,bq = np.nanquantile(v[f],lo), np.nanquantile(v[f],hi)
        return (v>=a)&(v<=bq)&f

    STATES = [
      ("ALL (baseline)",              lambda: np.ones(len(idx5),bool)),
      ("expected magnitude top 20%",  lambda: q(mag,0.80,1.0)),
      ("expected magnitude bot 20%",  lambda: q(mag,0.0,0.20)),
      ("volatility pct top 20%",      lambda: q(STA['vol_pct'],0.80,1.0)),
      ("volatility pct bot 20%",      lambda: q(STA['vol_pct'],0.0,0.20)),
      ("range compressed (bot 20%)",  lambda: q(STA['compress'],0.0,0.20)),
      ("range expanded (top 20%)",    lambda: q(STA['compress'],0.80,1.0)),
      ("momentum up (ret36 top 10%)", lambda: q(STA['ret36'],0.90,1.0)),
      ("momentum dn (ret36 bot 10%)", lambda: q(STA['ret36'],0.0,0.10)),
      ("short-term up (ret6 top 10%)",lambda: q(STA['ret6'],0.90,1.0)),
      ("short-term dn (ret6 bot 10%)",lambda: q(STA['ret6'],0.0,0.10)),
      ("volume shock (top 10%)",      lambda: q(STA['vshock'],0.90,1.0)),
      ("near 24h high (bot 10% dist)",lambda: q(STA['hi24'],0.0,0.10)),
      ("near 24h low (bot 10% dist)", lambda: q(STA['lo24'],0.0,0.10)),
      ("US session 13-21z",           lambda: np.isin(STA['hour'][idx5], range(13,21))),
      ("Asia session 0-8z",           lambda: np.isin(STA['hour'][idx5], range(0,8))),
    ]

    results=[]; tested=0
    for side, sname in ((+1,"LONG"), (-1,"SHORT")):
        tp, sl = P.first_passage(rows, entry, side=side)
        mo = P.markout(rows, entry, HZ)
        print(f"\n{'='*118}\n{sname}  net EV per trade (% of notional), maker/taker, "
              f"horizon {HZ}m. Baseline row is unconditional.\n{'='*118}")
        hdr = "state"
        print(f"  {hdr:<32}{'n':>8}" + "".join(f"{f'{s}/{t}':>11}" for s,t in CELLS))
        base_ev = {}
        for lbl, fn in STATES:
            m = fn()
            if m is None or m.sum() < 1000: continue
            row = f"  {lbl:<32}{m.sum():>8,}"
            for s,t in CELLS:
                si = list(P.STOPS).index(s/100); ti = list(P.TARGETS).index(t/100)
                w,l,u,r = P.score_cell(tp, sl, mo, si, ti, HZ, side,
                                        s/100, t/100, COST["maker/taker"])
                ev = r[m].mean()*100
                if lbl.startswith("ALL"): base_ev[(s,t)] = ev
                row += f"{ev:>+11.4f}"
                if not lbl.startswith("ALL"):
                    tested += 1
                    lo,hi = block_ci(r[m]-COST["maker/taker"]*0, block=288)
                    results.append((sname,lbl,s,t,ev,ev-base_ev[(s,t)],
                                    lo*100,hi*100,int(m.sum())))
            print(row)
    print(f"\n\n{'='*118}\nCELLS WITH POSITIVE NET EV AND 95% CI ABOVE ZERO\n{'='*118}")
    hits=[r for r in results if r[4]>0 and r[6]>0]
    print(f"  tested {tested} state x cell combinations, "
          f"expected false positives at a=0.05 ~{0.05*tested:.0f}")
    print(f"  found {len(hits)}")
    for h in sorted(hits, key=lambda z:-z[4])[:20]:
        print(f"   {h[0]:<6}{h[1]:<32}stop{h[2]:.2f}/tgt{h[3]:.2f} "
              f"EV{h[4]:+.4f}% lift{h[5]:+.4f} CI[{h[6]:+.4f},{h[7]:+.4f}] n={h[8]:,}")
    pickle.dump(results, open("/tmp/r3_results.pkl","wb"))

if __name__ == "__main__":
    main()
