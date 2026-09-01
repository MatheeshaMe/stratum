#!/usr/bin/env python3
"""Funding on a multi-day trailing hold — the last unmodelled cost."""
import sys, os, pickle, numpy as np, itertools
sys.path.insert(0,'research/trader'); sys.path.insert(0,'research/btc3')
import setups as SU
from run_discovery import prep, boot
ASSETS=[("BTC","data/spot/BTCUSDT-1m-full.pkl"),("ETH","data/alt/ETHUSDT-1m.pkl"),
        ("SOL","data/alt/SOLUSDT-1m.pkl"),("XRP","data/alt/XRPUSDT-1m.pkl"),
        ("DOGE","data/alt/DOGEUSDT-1m.pkl")]
rows=[]
for sym,p in ASSETS:
    if not os.path.exists(p): continue
    b,ctx,Z,TE=prep(p); A=ctx['A']; C=b['c']; H=b['h']; L=b['l']; n=len(C)
    for e in TE:
        i=e['i']
        if i<600 or i>=n-130 or e['touch']!=0: continue
        if ctx['htf'][i]!=e['side']: continue
        prox=e['prox']
        if (e['side']>0 and L[i]>prox) or (e['side']<0 and H[i]<prox): continue
        stop=e['dist']-0.25*A[i] if e['side']>0 else e['dist']+0.25*A[i]
        r=SU.manage(b,ctx,i,e['side'],prox,stop,mode="trail_struct",rr=None,
                    maxb=120,cost=SU.COST_LIMIT_IN)
        if r: rows.append((r['R'],r['bars'],r['risk_pct'],e['side'],b['t'][i]))
M=np.array(rows)
R,BARS,RISK=M[:,0],M[:,1],M[:,2]
print(f"n={len(R):,}  EV {R.mean():+.3f}R  median hold {np.median(BARS):.0f} bars "
      f"({np.median(BARS):.0f}h)  median risk {np.median(RISK):.2f}% of price")
print(f"  hold distribution: p25 {np.percentile(BARS,25):.0f}h  p75 {np.percentile(BARS,75):.0f}h  "
      f"p95 {np.percentile(BARS,95):.0f}h\n")
print(f"  {'funding rate':<28}{'cost in R (median)':>20}{'EV after':>10}{'  95% CI':>22}")
for rate,lbl in ((0.00125,"typical 0.00125%/h"),(0.005,"moderate 0.005%/h"),
                 (0.01,"elevated 0.01%/h"),(0.03,"stressed 0.03%/h")):
    fund_pct=rate*BARS                      # % of notional
    fund_R=fund_pct/RISK                    # in R
    Rn=R-fund_R
    lo,hi=boot(Rn)
    print(f"  {lbl:<28}{np.median(fund_R):>20.3f}{Rn.mean():>+10.3f}"
          f"   [{lo:+.3f},{hi:+.3f}]{'  <<<' if lo>0 else ''}")
Rn=R-(0.005*BARS)/RISK
S=np.sort(Rn)[::-1]
print(f"\n  at moderate funding, tail dependence:")
for k in (0,3,10,25):
    X=S[k:]; lo,hi=boot(X)
    print(f"    excluding top {k:<4}{len(X):>7}  EV {X.mean():>+7.3f}  CI [{lo:+.3f},{hi:+.3f}]")
ls=[len(list(g)) for k,g in itertools.groupby(Rn>0) if not k]
print(f"\n  win {(Rn>0).mean():.1%}  median {np.median(Rn):+.2f}R  "
      f"longest losing streak {max(ls) if ls else 0}")
eq=np.cumsum(Rn); pk=np.maximum.accumulate(eq)
print(f"  total {Rn.sum():+.0f}R  max drawdown {(pk-eq).max():.0f}R")
def ms(s): return int(np.datetime64(s).astype('datetime64[ms]').astype(np.int64))
print(f"\n  {'era':<16}{'n':>7}{'EV R':>9}{'  95% CI':>22}")
for lbl,a,z in (("2017-2019",ms('2017-01-01'),ms('2020-01-01')),
                ("2020-2022",ms('2020-01-01'),ms('2023-01-01')),
                ("2023-2024",ms('2023-01-01'),ms('2025-01-01')),
                ("2025-2026",ms('2025-01-01'),ms('2027-01-01'))):
    m=(M[:,4]>=a)&(M[:,4]<z)
    if m.sum()<80: continue
    X=Rn[m]; lo,hi=boot(X)
    print(f"  {lbl:<16}{int(m.sum()):>7}{X.mean():>+9.3f}   [{lo:+.3f},{hi:+.3f}]"
          f"{'  <<<' if lo>0 else ''}")
pickle.dump(M,open("/tmp/trader_final.pkl","wb"))
