#!/usr/bin/env python3
"""Step 6b -- C8 fixed. Forward-only, non-overlapping +3% label."""
import sys, os, pickle, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import events as E
from numpy.lib.stride_tricks import sliding_window_view

T,O,H,L,C,V,N=E.load("data/spot/BTCUSDT-1m.pkl")
n=len(C); IND=pickle.load(open("/tmp/btc3_ind.pkl","rb"))
K=60
fmax=np.full(n,np.nan); fmin=np.full(n,np.nan)
swh=sliding_window_view(H,K); swl=sliding_window_view(L,K)
fmax[:len(swh)-1]=swh[1:].max(1)          # H[i+1..i+K]
fmin[:len(swl)-1]=swl[1:].min(1)
contig=np.zeros(n,bool); contig[:n-K-1]=(T[K+1:]-T[:n-K-1])==(K+1)*60000
STRIDE=5; grid=np.arange(10081,n-K-2,STRIDE); grid=grid[contig[grid]]
yU=((fmax[grid]/C[grid]-1)>=0.03).astype(float)
yD=((fmin[grid]/C[grid]-1)<=-0.03).astype(float)
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
def ci_ratio(ku,kd):
    if ku<5 or kd<5: return (np.nan,np.nan)
    se=np.sqrt(1/ku+1/kd); lr=np.log(ku/kd)
    return np.exp(lr-1.96*se),np.exp(lr+1.96*se)
CONDS=[]
for f in F:
    for qq,lab in ((0.95,">= p95"),(0.90,">= p90"),(0.10,"<= p10"),(0.05,"<= p05")):
        q=np.nanquantile(F[f][disc],qq)
        CONDS.append((f"{f} {lab}",(F[f]>=q) if qq>0.5 else (F[f]<=q)))
qa=np.nanquantile(F['atr_pct'][disc],0.90); qr=np.nanquantile(F['rsi'][disc],0.10)
qd=np.nanquantile(F['dist_24h_high'][disc],0.10); qv=np.nanquantile(F['vol_ratio'][disc],0.90)
CONDS+=[("high ATR & RSI low",(F['atr_pct']>=qa)&(F['rsi']<=qr)),
        ("high ATR & far below 24h high",(F['atr_pct']>=qa)&(F['dist_24h_high']<=qd)),
        ("high ATR & high vol",(F['atr_pct']>=qa)&(F['vol_ratio']>=qv))]
store={}
for era,sel in (("DISCOVERY 2017-2019",disc),("VALIDATION 2023-2026",vald)):
    bU=yU[sel].mean(); bD=yD[sel].mean()
    print(f"\n{'='*106}\n{era}   n={sel.sum():,}  base P(+3% in 60m)={bU:.4%}  "
          f"P(-3%)={bD:.4%}  base up/down={bU/bD:.2f}\n{'='*106}")
    print(f"{'condition':<34}{'n':>9}{'P(+3%)':>10}{'P(-3%)':>10}{'up/dn':>8}"
          f"{'  95% CI up/dn':>20}{'  lift vs base':>15}{'  directional?':>14}")
    rows=[]
    for cl,m in CONDS:
        mm=m&sel
        if mm.sum()<400: continue
        ku=int(yU[mm].sum()); kd=int(yD[mm].sum())
        if ku<5 or kd<5: continue
        pu=yU[mm].mean(); pdn=yD[mm].mean(); r=pu/pdn
        lo,hi=ci_ratio(ku,kd)
        rows.append((abs(np.log(r)),cl,int(mm.sum()),pu,pdn,r,lo,hi,pu/bU))
    rows.sort(reverse=True)
    store[era]={x[1]:x for x in rows}
    for _,cl,nn,pu,pdn,r,lo,hi,lift in rows[:14]:
        d="yes" if (lo>1.15 or hi<0.87) else "no"
        print(f"{cl:<34}{nn:>9,}{pu:>10.3%}{pdn:>10.3%}{r:>8.2f}"
              f"   [{lo:.2f},{hi:.2f}]{lift:>13.2f}x{d:>14}")
print("\n\nREPLICATION: up/down ratio in both eras (directional info only if BOTH differ from 1)")
print(f"{'condition':<34}{'disc up/dn':>12}{'valid up/dn':>13}{'  both directional & same side':>32}")
A=store["DISCOVERY 2017-2019"]; B=store["VALIDATION 2023-2026"]
sur=[]
for cl in A:
    if cl not in B: continue
    ra,la,ha=A[cl][5],A[cl][6],A[cl][7]; rb,lb,hb=B[cl][5],B[cl][6],B[cl][7]
    da=(la>1.15 or ha<0.87); db=(lb>1.15 or hb<0.87)
    same=(ra>1 and rb>1) or (ra<1 and rb<1)
    ok="YES" if (da and db and same) else ""
    if ok: sur.append((abs(np.log(ra*rb)/2),cl,ra,rb))
    print(f"{cl:<34}{ra:>12.2f}{rb:>13.2f}{ok:>32}")
print(f"\n  conditions replicating with a directional up/down skew: {len(sur)}")
