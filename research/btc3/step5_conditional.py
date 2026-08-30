#!/usr/bin/env python3
"""Step 5 -- the REVERSE question: P(+3% within 1h | state), train/test split.

Step 4 measured P(state | event). That is not the same thing and cannot be used
to forecast. This measures P(event | state) against the base rate, with a strict
temporal split:
    DISCOVERY  2017-08 .. 2019-12
    VALIDATION 2023-01 .. 2026-07     (2020-2022 sealed, excluded)
Conditions are fixed quantile cuts defined on the DISCOVERY set only.
"""
import sys, os, pickle, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import events as E

T,O,H,L,C,V,N=E.load("data/spot/BTCUSDT-1m.pkl")
n=len(C); IND=pickle.load(open("/tmp/btc3_ind.pkl","rb"))

STRIDE=5
grid=np.arange(10081, n-1441, STRIDE)
# label: does close/close[-60] cross +3% at ANY point in the next 60 minutes?
print("labelling ...", flush=True)
fwd_max=np.full(n,np.nan)
from numpy.lib.stride_tricks import sliding_window_view
W=60
ratio=np.full(n,np.nan); ratio[W:]=C[W:]/C[:-W]-1.0
# event at bar j if ratio[j] >= .03 ; we ask: any j in (i, i+60]
ev=np.nan_to_num(ratio,nan=0)>=0.03
fut=np.zeros(n,bool)
sw=sliding_window_view(ev, 61)
fut[:len(sw)]=sw[:,1:].any(1)
y=fut[grid].astype(float)
print(f"grid {len(grid):,} points, base rate P(+3% in next 60m) = {y.mean():.4%}")

ref=grid
F={}
F['ret_1h']=(C[ref]/C[ref-60]-1)*100
F['ret_4h']=(C[ref]/C[ref-240]-1)*100
F['ret_24h']=(C[ref]/C[ref-1440]-1)*100
F['atr_pct']=IND['atr14'][ref]/C[ref]*100
F['rsi']=IND['rsi14'][ref]
F['mfi']=IND['mfi14'][ref]
F['vol_ratio']=(IND['vsum20'][ref]/20)/(IND['vsum1440'][ref]/1440)
F['dist_24h_high']=(C[ref]/IND['hh1440'][ref]-1)*100
F['dist_7d_high']=(C[ref]/IND['hh10080'][ref]-1)*100
F['ema200h_dist']=(C[ref]/IND['ema200h'][ref]-1)*100
F['range24']=(IND['hh1440'][ref]-IND['ll1440'][ref])/C[ref]*100

CUT=np.datetime64('2021-01-01').astype('datetime64[ms]').astype(np.int64)
disc=T[ref]<CUT; vald=T[ref]>=CUT
print(f"discovery {disc.sum():,} pts ({y[disc].mean():.4%} base)   "
      f"validation {vald.sum():,} pts ({y[vald].mean():.4%} base)\n")

def wilson(k,nn):
    if nn==0: return (np.nan,np.nan)
    p=k/nn; z=1.96; d=1+z*z/nn
    c=(p+z*z/(2*nn))/d; h=z*np.sqrt(p*(1-p)/nn+z*z/(4*nn*nn))/d
    return c-h,c+h

CONDS=[]
for f in F:
    q=np.nanquantile(F[f][disc],[0.05,0.10,0.90,0.95])
    CONDS.append((f"{f} <= p05", F[f]<=q[0]))
    CONDS.append((f"{f} <= p10", F[f]<=q[1]))
    CONDS.append((f"{f} >= p90", F[f]>=q[2]))
    CONDS.append((f"{f} >= p95", F[f]>=q[3]))
# a few economically-motivated combinations, defined a priori
qa=np.nanquantile(F['atr_pct'][disc],0.90); qv=np.nanquantile(F['vol_ratio'][disc],0.90)
qr=np.nanquantile(F['rsi'][disc],0.10); qd=np.nanquantile(F['dist_24h_high'][disc],0.10)
CONDS += [
 ("high ATR & high vol",            (F['atr_pct']>=qa)&(F['vol_ratio']>=qv)),
 ("high ATR & RSI low",             (F['atr_pct']>=qa)&(F['rsi']<=qr)),
 ("high ATR & far below 24h high",  (F['atr_pct']>=qa)&(F['dist_24h_high']<=qd)),
 ("RSI low & far below 24h high",   (F['rsi']<=qr)&(F['dist_24h_high']<=qd)),
 ("high ATR & RSI low & far below", (F['atr_pct']>=qa)&(F['rsi']<=qr)&(F['dist_24h_high']<=qd)),
 ("above EMA200h & vol spike",      (F['ema200h_dist']>0)&(F['vol_ratio']>=qv)),
]
print(f"{'condition':<36}{'DISCOVERY 2017-19':>30}{'VALIDATION 2023-26':>32}")
print(f"{'':<36}{'n':>9}{'P(+3%)':>10}{'lift':>11}{'n':>10}{'P(+3%)':>10}"
      f"{'lift':>11}{'  95% CI (valid)':>20}")
b_d=y[disc].mean(); b_v=y[vald].mean()
res=[]
for lbl,m in CONDS:
    md=m&disc&np.isfinite(m.astype(float)); mv=m&vald
    nd=int(md.sum()); nv=int(mv.sum())
    if nd<300 or nv<300: continue
    pd_=y[md].mean(); pv=y[mv].mean()
    lo,hi=wilson(y[mv].sum(),nv)
    sig="*" if lo>b_v else " "
    res.append((pv/b_v if b_v>0 else np.nan, lbl, nd,pd_,pd_/b_d, nv,pv,pv/b_v, lo,hi, sig))
res.sort(reverse=True)
for r in res:
    _,lbl,nd,pd_,ld,nv,pv,lv,lo,hi,sig=r
    print(f"{lbl:<36}{nd:>9,}{pd_:>10.3%}{ld:>10.2f}x{nv:>10,}{pv:>10.3%}"
          f"{lv:>10.2f}x{sig} [{lo:.3%},{hi:.3%}]")
print(f"\n  base rate: discovery {b_d:.4%}  validation {b_v:.4%}")
print(f"  conditions tested {len(res)}, expected false positives at a=0.05 ~{0.05*len(res):.1f}")
surv=[r for r in res if r[10]=='*' and r[4]>1.2 and r[7]>1.2]
print(f"  lift > 1.2x in BOTH eras and CI above base: {len(surv)}")
for r in surv[:12]:
    print(f"     {r[1]:<36}disc {r[4]:.2f}x  valid {r[7]:.2f}x")
