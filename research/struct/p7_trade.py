#!/usr/bin/env python3
"""PHASE 7/8/18 -- does the path model's ranking translate into money?

AUC on P(peak >= 3R) is 0.589 and on 5R is 0.625. Trend-following needs only a
few large winners, so if that ranking is real it should show up as positive EV
in the top slices. Tested with the unbounded structural exit, full taker cost,
plus partial-exit and pyramiding variants (Phase 8).
"""
import sys, os, pickle, numpy as np
sys.path.insert(0,'research/struct')
MODELS,MT,TT,SD,SY,Y=pickle.load(open("/tmp/p4_models.pkl","rb"))

def boot(R,it=4000,seed=0):
    rg=np.random.default_rng(seed)
    return tuple(np.percentile([rg.choice(R,len(R)).mean() for _ in range(it)],[2.5,97.5]))
def ms(y): return int(np.datetime64(f'{y}-01-01').astype('datetime64[ms]').astype(np.int64))

print(f"pooled n={len(MT):,}  unconditional EV {MT.mean():+.4f}R  win {(MT>0).mean():.1%}\n")
print(f"{'rank by':<22}{'slice':<10}{'n':>7}{'win%':>7}{'EV R':>9}{'  95% CI':>22}"
      f"{'PF':>7}{'totR':>9}{'p90 R':>8}{'maxR':>8}")
best=None
for k in (1.0,2.0,3.0,5.0):
    P=MODELS[k]; s=np.isfinite(P)
    for qq,lab in ((0.0,"all"),(0.5,"top 50%"),(0.8,"top 20%"),(0.9,"top 10%"),(0.95,"top 5%")):
        thr=np.quantile(P[s],qq) if qq>0 else -np.inf
        m=s&(P>=thr)
        if m.sum()<150: continue
        R=MT[m]; w=R>0
        lo,hi=boot(R); pf=R[w].sum()/max(-R[~w].sum(),1e-9)
        flag="  <<<" if lo>0 else ""
        print(f"P(peak>={k:.0f}R){'':<11}{lab:<10}{int(m.sum()):>7}{w.mean():>7.1%}"
              f"{R.mean():>+9.3f}   [{lo:+.3f},{hi:+.3f}]{pf:>7.2f}{R.sum():>+9.1f}"
              f"{np.percentile(R,90):>8.2f}{R.max():>8.1f}{flag}")
        if lo>0 and (best is None or R.mean()>best[0]): best=(R.mean(),k,qq,m)
    print()

print("PHASE 8 -- trade management variants on the top-10% P(peak>=3R) slice")
P=MODELS[3.0]; s=np.isfinite(P); m=s&(P>=np.quantile(P[s],0.9))
R=MT[m]; peak=Y[m]
print(f"  {'management':<34}{'EV R':>9}{'  95% CI':>22}{'win%':>8}{'PF':>7}")
def rep(lbl,r):
    lo,hi=boot(r); w=r>0
    print(f"  {lbl:<34}{r.mean():>+9.3f}   [{lo:+.3f},{hi:+.3f}]{w.mean():>8.1%}"
          f"{r[w].sum()/max(-r[~w].sum(),1e-9):>7.2f}")
rep("baseline: full trail to stop", R)
# partial at +1R, trail the rest: approximate using realised peak and final R
for frac,at in ((0.5,1.0),(0.5,2.0),(0.33,1.0)):
    r=np.where(peak>=at, frac*at+(1-frac)*R, R)
    rep(f"take {frac:.0%} at +{at:.0f}R, trail rest", r)
# hard cap (deliberately destroys the tail, for contrast)
for cap in (2.0,3.0,5.0):
    r=np.where(peak>=cap, cap, R)
    rep(f"hard cap at +{cap:.0f}R (tail removed)", r)

print("\nTEMPORAL + CROSS-ASSET SPLIT of the top-10% P(peak>=3R) slice")
print(f"  {'split':<18}{'n':>7}{'win%':>8}{'EV R':>9}{'  95% CI':>22}")
for lbl,mm in (("2017-2019",m&(TT<ms(2020))),("2023-2024",m&(TT>=ms(2023))&(TT<ms(2025))),
               ("2025-2026",m&(TT>=ms(2025)))):
    if mm.sum()<80: continue
    r=MT[mm]; lo,hi=boot(r)
    print(f"  {lbl:<18}{int(mm.sum()):>7}{(r>0).mean():>8.1%}{r.mean():>+9.3f}   [{lo:+.3f},{hi:+.3f}]")
for sym in sorted(set(SY)):
    mm=m&(SY==sym)
    if mm.sum()<80: continue
    r=MT[mm]; lo,hi=boot(r)
    print(f"  {sym:<18}{int(mm.sum()):>7}{(r>0).mean():>8.1%}{r.mean():>+9.3f}   [{lo:+.3f},{hi:+.3f}]")
print(f"\n  LONG  n={int((m&(SD>0)).sum()):>5}  EV {MT[m&(SD>0)].mean():+.3f}R")
print(f"  SHORT n={int((m&(SD<0)).sum()):>5}  EV {MT[m&(SD<0)].mean():+.3f}R")
