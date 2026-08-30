#!/usr/bin/env python3
"""R-3 -- sequential, non-overlapping simulation. What the system would actually do.

The candidate fires 5.8x/day with a 120-minute horizon, so raw per-trade EV
double-counts overlapping exposure. A one-position-at-a-time system takes the
first signal and IGNORES every signal until that position closes. This measures
the real opportunity rate, the real equity path, and the real drawdown.
"""
import sys, os, pickle, itertools, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import situations as S
from r3_causal import trail_q, block_ci, BPS, MAKER, TAKER, HALF, HMAX

def main(K=6, Q=0.01, STOP=0.005, TGT=0.0075, LEV=2.67):
    rows=pickle.load(open("data/explore_r1.pkl","rb"))
    b=S.agg(rows,5); st=S.situations(b)
    O=np.array([r[1] for r in rows]); H=np.array([r[2] for r in rows])
    L=np.array([r[3] for r in rows]); C=np.array([r[4] for r in rows])
    # C7: signal is the CLOSE of 5m bar k -> last 1m bar of that 5m bar
    _end=b['i1m'][1:]-1
    _ok=(_end>60)&(_end<len(rows)-HMAX-5)
    ent5=_end[_ok]
    idx5=np.arange(len(b['c'])-1)[_ok]
    c=b['c']; atrp=st['A']/c
    r=np.concatenate([[np.nan]*K,(c[K:]-c[:-K])/c[:-K]])/np.where(atrp==0,np.nan,atrp)
    rs=r[idx5]; thi=trail_q(rs,1-Q); tlo=trail_q(rs,Q)
    sigL=np.isfinite(rs)&np.isfinite(thi)&(rs>=thi)
    sigS=np.isfinite(rs)&np.isfinite(tlo)&(rs<=tlo)

    trades=[]; busy_until=-1
    for j in range(len(ent5)):
        if not (sigL[j] or sigS[j]): continue
        e=ent5[j]
        if e <= busy_until: continue
        side=+1 if sigL[j] else -1
        fill=O[e+1]
        tgt = fill*(1+side*TGT); stp = fill*(1-side*STOP)
        exit_i=None; out=None
        for k in range(e+1, min(e+1+HMAX, len(C))):
            if side>0:
                if L[k]<=stp: out=-STOP; exit_i=k; break
                if H[k]>=tgt: out=+TGT;  exit_i=k; break
            else:
                if H[k]>=stp: out=-STOP; exit_i=k; break
                if L[k]<=tgt: out=+TGT;  exit_i=k; break
        if out is None:
            exit_i=min(e+HMAX, len(C)-1); out=side*(C[exit_i]/fill-1)
            win=False
        else:
            win = out>0
        cost=(TAKER+HALF)*BPS + (MAKER*BPS if win else (TAKER+HALF)*BPS)
        trades.append((b['t'][idx5[j]], out-cost, win, exit_i-e, side))
        busy_until=exit_i

    R=np.array([t[1] for t in trades]); W=np.array([t[2] for t in trades])
    HOLD=np.array([t[3] for t in trades]); SIDE=np.array([t[4] for t in trades])
    days=(ent5[-1]-ent5[0])/1440
    lo,hi=block_ci(R, block=60)
    print(f"SEQUENTIAL SYSTEM  (lookback {K*5}m, tail {Q*100:g}%, stop {STOP*100:g}%, "
          f"target {TGT*100:g}%, horizon {HMAX}m)\n")
    print(f"  trades taken           {len(R):,}  ({len(R)/days:.2f}/day over {days:.0f} days)")
    print(f"  signals ignored (busy) {int(sigL.sum()+sigS.sum())-len(R):,} "
          f"of {int(sigL.sum()+sigS.sum()):,}")
    print(f"  long / short           {int((SIDE>0).sum()):,} / {int((SIDE<0).sum()):,}")
    print(f"  P(target first)        {W.mean():.1%}")
    print(f"  median hold            {np.median(HOLD):.0f} min")
    print(f"  EV/trade (notional)    {R.mean()*100:+.4f}%   CI [{lo*100:+.4f},{hi*100:+.4f}]")
    print(f"  sd/trade               {R.std()*100:.4f}%")

    print(f"\n  COMPOUNDED at {LEV}x leverage, full-size each trade:")
    eq=np.cumprod(1+R*LEV); pk=np.maximum.accumulate(eq); dd=(pk-eq)/pk
    yrs=days/365.25
    cagr=eq[-1]**(1/yrs)-1
    ls=[len(list(g)) for k,g in itertools.groupby(R>0) if not k]
    print(f"    final equity multiple {eq[-1]:.2f}x over {yrs:.2f}y   CAGR {cagr:+.1%}")
    print(f"    max drawdown          {dd.max():.1%}")
    print(f"    longest losing streak {max(ls) if ls else 0}")
    print(f"    worst trade           {R.min()*LEV*100:+.2f}%   best {R.max()*LEV*100:+.2f}%")

    # yearly stability
    print(f"\n  BY YEAR (notional EV, no leverage):")
    yr=np.array([int(np.datetime64(int(t[0]),'ms').astype('datetime64[Y]').astype(int))+1970
                 for t in trades])
    for y in sorted(set(yr)):
        m=yr==y
        if m.sum()<50: continue
        l2,h2=block_ci(R[m], block=60)
        print(f"    {y}  n={m.sum():>4}  EV {R[m].mean()*100:>+8.4f}%  "
              f"CI [{l2*100:+.4f},{h2*100:+.4f}]  win {W[m].mean():.1%}")

    # bootstrap the equity path -- historical order is one sample
    print(f"\n  MONTE CARLO on the empirical trade distribution (10k resamples, {LEV}x):")
    rng=np.random.default_rng(0); N=len(R)
    finals=[]; dds=[]
    for _ in range(10000):
        s=rng.choice(R, N, replace=True)
        e=np.cumprod(1+s*LEV); p=np.maximum.accumulate(e)
        finals.append(e[-1]); dds.append(((p-e)/p).max())
    finals=np.array(finals); dds=np.array(dds)
    print(f"    final multiple  p5 {np.percentile(finals,5):.2f}x  "
          f"median {np.median(finals):.2f}x  p95 {np.percentile(finals,95):.2f}x")
    print(f"    max drawdown    median {np.median(dds):.1%}  "
          f"p95 {np.percentile(dds,95):.1%}  worst {dds.max():.1%}")
    print(f"    P(ruin, -80%)   {(finals<0.2).mean():.2%}")

if __name__=="__main__":
    main()
