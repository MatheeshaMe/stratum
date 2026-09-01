#!/usr/bin/env python3
"""The decisive control for the trailing-structural result.

A trailing structural stop with no profit cap is a TREND-FOLLOWING exit. In a
market that trends, it makes money from almost any entry. So the question is not
'is trailS profitable' but 'does the ZONE entry beat a random entry using the
same exit?'
"""
import sys, os, pickle, numpy as np, itertools
sys.path.insert(0,'research/trader'); sys.path.insert(0,'research/btc3')
import setups as SU, events as E
from run_discovery import prep, boot

def trail_from(b,ctx,i,side,entry,stop,cost,maxb=120):
    return SU.manage(b,ctx,i,side,entry,stop,mode="trail_struct",rr=None,
                     maxb=maxb,cost=cost)

ASSETS=[("BTC","data/spot/BTCUSDT-1m-full.pkl"),("ETH","data/alt/ETHUSDT-1m.pkl"),
        ("SOL","data/alt/SOLUSDT-1m.pkl"),("XRP","data/alt/XRPUSDT-1m.pkl"),
        ("DOGE","data/alt/DOGEUSDT-1m.pkl")]
REAL=[]; CTRL=[]; CTRL_AL=[]
rng=np.random.default_rng(0)
for sym,p in ASSETS:
    if not os.path.exists(p): continue
    b,ctx,Z,TE=prep(p)
    A=ctx['A']; C=b['c']; H=b['h']; L=b['l']; n=len(C)
    risks=[]
    for e in TE:
        i=e['i']
        if i<600 or i>=n-130 or e['touch']!=0: continue
        if ctx['htf'][i]!=e['side']: continue
        prox=e['prox']
        if (e['side']>0 and L[i]>prox) or (e['side']<0 and H[i]<prox): continue
        stop=e['dist']-0.25*A[i] if e['side']>0 else e['dist']+0.25*A[i]
        r=trail_from(b,ctx,i,e['side'],prox,stop,SU.COST_LIMIT_IN)
        if r: REAL.append(r['R']); risks.append(abs(prox-stop)/prox)
    if len(risks)<50: continue
    risks=np.array(risks)
    # CONTROL 1: random bar, random side, same risk distribution, same exit
    for _ in range(len(risks)*3):
        i=int(rng.integers(600,n-130)); a=A[i]
        if not np.isfinite(a) or a<=0: continue
        side=1 if rng.random()<0.5 else -1
        rk=risks[rng.integers(0,len(risks))]*C[i]
        r=trail_from(b,ctx,i,side,C[i],C[i]-side*rk,SU.COST_LIMIT_IN)
        if r: CTRL.append(r['R'])
    # CONTROL 2: random bar, HTF-ALIGNED side, same risk, same exit
    for _ in range(len(risks)*3):
        i=int(rng.integers(600,n-130)); a=A[i]
        if not np.isfinite(a) or a<=0: continue
        side=int(ctx['htf'][i])
        if side==0: continue
        rk=risks[rng.integers(0,len(risks))]*C[i]
        r=trail_from(b,ctx,i,side,C[i],C[i]-side*rk,SU.COST_LIMIT_IN)
        if r: CTRL_AL.append(r['R'])

R=np.array(REAL); C1=np.array(CTRL); C2=np.array(CTRL_AL)
print(f"{'population':<46}{'n':>7}{'win%':>7}{'EV R':>9}{'  95% CI':>22}{'medR':>8}{'maxR':>8}")
for lbl,X in (("REAL: zone + HTF aligned, trailing structural",R),
              ("CONTROL 1: random entry, random side",C1),
              ("CONTROL 2: random entry, HTF-ALIGNED side",C2)):
    lo,hi=boot(X)
    print(f"{lbl:<46}{len(X):>7}{(X>0).mean():>7.1%}{X.mean():>+9.3f}"
          f"   [{lo:+.3f},{hi:+.3f}]{np.median(X):>+8.2f}{X.max():>8.1f}")
d=np.array([np.random.default_rng(s).choice(R,len(R)).mean()-
            np.random.default_rng(s+9999).choice(C2,len(C2)).mean() for s in range(3000)])
print(f"\n  REAL minus CONTROL 2: {R.mean()-C2.mean():+.3f} R   "
      f"95% CI [{np.percentile(d,2.5):+.3f},{np.percentile(d,97.5):+.3f}]")
print(f"  -> {'the ZONE adds value over an aligned random entry' if np.percentile(d,2.5)>0 else 'the zone adds NOTHING beyond HTF alignment + a trailing exit'}")

print(f"\nTAIL DEPENDENCE of the REAL series")
S=np.sort(R)[::-1]
print(f"  {'excluding':<18}{'n':>7}{'EV R':>9}{'  95% CI':>22}")
for k in (0,1,3,5,10,25):
    X=S[k:]; lo,hi=boot(X)
    print(f"  top {k:<14}{len(X):>7}{X.mean():>+9.3f}   [{lo:+.3f},{hi:+.3f}]")
print(f"\n  median trade {np.median(R):+.2f} R   "
      f"share of total profit from top 3 trades: {S[:3].sum()/max(S.sum(),1e-9):.0%}")
ls=[len(list(g)) for k,g in itertools.groupby(R>0) if not k]
print(f"  win rate {(R>0).mean():.1%}   longest losing streak {max(ls) if ls else 0}")
rg=np.random.default_rng(7)
for N in (50,100,200):
    p=np.mean([rg.choice(R,N).sum()>0 for _ in range(20000)])
    print(f"  P(profitable after {N:>3} trades) = {p:.1%}")
