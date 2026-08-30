#!/usr/bin/env python3
"""Step 6 -- do the precursors predict UP, or just BIG?

Every condition from step 5 is re-scored against BOTH tails:
    P(+3% within 60m | condition)   and   P(-3% within 60m | condition)
If the two rise together, the condition carries magnitude information and no
directional information -- which is the null this project has established
four times already. Directional edge requires the RATIO to move.
"""
import sys, os, pickle, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import events as E
from numpy.lib.stride_tricks import sliding_window_view

T,O,H,L,C,V,N=E.load("data/spot/BTCUSDT-1m.pkl")
n=len(C); IND=pickle.load(open("/tmp/btc3_ind.pkl","rb"))
STRIDE=5; grid=np.arange(10081,n-1441,STRIDE); W=60
ratio=np.full(n,np.nan); ratio[W:]=C[W:]/C[:-W]-1.0
def future(mask):
    f=np.zeros(n,bool); sw=sliding_window_view(mask,61); f[:len(sw)]=sw[:,1:].any(1); return f
up=future(np.nan_to_num(ratio,nan=0)>=0.03)
dn=future(np.nan_to_num(ratio,nan=0)<=-0.03)
yU=up[grid].astype(float); yD=dn[grid].astype(float)
ref=grid
F={}
F['atr_pct']=IND['atr14'][ref]/C[ref]*100
F['rsi']=IND['rsi14'][ref]; F['mfi']=IND['mfi14'][ref]
F['vol_ratio']=(IND['vsum20'][ref]/20)/(IND['vsum1440'][ref]/1440)
F['ret_1h']=(C[ref]/C[ref-60]-1)*100
F['ret_4h']=(C[ref]/C[ref-240]-1)*100
F['ret_24h']=(C[ref]/C[ref-1440]-1)*100
F['dist_24h_high']=(C[ref]/IND['hh1440'][ref]-1)*100
F['dist_7d_high']=(C[ref]/IND['hh10080'][ref]-1)*100
F['ema200h_dist']=(C[ref]/IND['ema200h'][ref]-1)*100
F['range24']=(IND['hh1440'][ref]-IND['ll1440'][ref])/C[ref]*100
CUT=np.datetime64('2021-01-01').astype('datetime64[ms]').astype(np.int64)
disc=T[ref]<CUT; vald=T[ref]>=CUT

def wilson_ratio(ku,kd):
    """CI on log(P_up/P_dn) via a normal approximation on the log odds."""
    if ku<5 or kd<5: return (np.nan,np.nan)
    se=np.sqrt(1/ku+1/kd); lr=np.log(ku/kd)
    return np.exp(lr-1.96*se), np.exp(lr+1.96*se)

CONDS=[]
for f in F:
    for qq,lab in ((0.95,">= p95"),(0.90,">= p90"),(0.10,"<= p10"),(0.05,"<= p05")):
        q=np.nanquantile(F[f][disc],qq)
        m=(F[f]>=q) if qq>0.5 else (F[f]<=q)
        CONDS.append((f"{f} {lab}",m))
qa=np.nanquantile(F['atr_pct'][disc],0.90); qr=np.nanquantile(F['rsi'][disc],0.10)
qd=np.nanquantile(F['dist_24h_high'][disc],0.10); qv=np.nanquantile(F['vol_ratio'][disc],0.90)
CONDS+=[("high ATR & RSI low",(F['atr_pct']>=qa)&(F['rsi']<=qr)),
        ("high ATR & far below 24h high",(F['atr_pct']>=qa)&(F['dist_24h_high']<=qd)),
        ("high ATR & high vol",(F['atr_pct']>=qa)&(F['vol_ratio']>=qv))]

for era,sel,lab in (("DISCOVERY 2017-2019",disc,"disc"),("VALIDATION 2023-2026",vald,"valid")):
    bU=yU[sel].mean(); bD=yD[sel].mean()
    print(f"\n{'='*104}\n{era}   base P(+3%)={bU:.4%}  P(-3%)={bD:.4%}  "
          f"base ratio up/down = {bU/bD:.2f}\n{'='*104}")
    print(f"{'condition':<34}{'n':>9}{'P(+3%)':>10}{'P(-3%)':>10}{'up/down':>10}"
          f"{'  95% CI on up/down':>24}{'  directional?':>15}")
    rows=[]
    for cl,m in CONDS:
        mm=m&sel
        if mm.sum()<400: continue
        ku=int(yU[mm].sum()); kd=int(yD[mm].sum())
        pu=yU[mm].mean(); pdn=yD[mm].mean()
        if kd<5 or ku<5: continue
        lo,hi=wilson_ratio(ku,kd)
        r=pu/pdn if pdn>0 else np.nan
        direc = "yes" if (lo>1.15 or hi<0.87) else "no"
        rows.append((abs(np.log(r)),cl,int(mm.sum()),pu,pdn,r,lo,hi,direc))
    rows.sort(reverse=True)
    for _,cl,nn,pu,pdn,r,lo,hi,direc in rows[:16]:
        print(f"{cl:<34}{nn:>9,}{pu:>10.3%}{pdn:>10.3%}{r:>10.2f}"
              f"   [{lo:.2f},{hi:.2f}]{direc:>15}")
print("\n  'directional?' = the up/down ratio CI excludes the +/-15% band around 1.0")
