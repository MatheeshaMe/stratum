#!/usr/bin/env python3
"""E4 -- the user's central question, tested with a strict chronological split.

'If I see THIS state now, how likely is BTC to give me the move before the stop?'

Target 0.30% BTC (= +3% account at 10x), stop 0.15% (1:2), 4h limit.
Conditions are quantile cuts fixed on the TRAIN period only.
  TRAIN 2017-08..2018-12   VALIDATE 2019-01..2019-12   TEST 2023-01..2026-07
Sealed 2020-2022 untouched.
"""
import sys, os, pickle, numpy as np
sys.path.insert(0,"research/btc3")
import events as E
T,O,H,L,C,V,N=E.load("data/spot/BTCUSDT-1m.pkl")
n=len(C); IND=pickle.load(open("/tmp/btc3_ind.pkl","rb"))
COSTB=0.0663; LEVR=10; TGT=0.30; STP=0.15; LIM=240; HMAX=1440
STRIDE=15
ent=np.arange(20161,n-HMAX-2,STRIDE)
ent=ent[(T[np.minimum(ent+HMAX,n-1)]-T[ent])==HMAX*60000]

def fp(e,t,s,side,chunk=4000):
    BIG=np.int32(10**6); tp=np.full(len(e),BIG,np.int32); sl=np.full(len(e),BIG,np.int32)
    off=np.arange(1,HMAX+1)
    for a in range(0,len(e),chunk):
        ee=e[a:a+chunk]; idx=ee[:,None]+off[None,:]; px=C[ee][:,None]
        rh=np.maximum.accumulate(H[idx],1)/px; rl=np.minimum.accumulate(L[idx],1)/px
        mt=(rh>=1+t/100) if side>0 else (rl<=1-t/100)
        ms=(rl<=1-s/100) if side>0 else (rh>=1+s/100)
        tp[a:a+len(ee)]=np.where(mt.any(1),mt.argmax(1)+1,BIG)
        sl[a:a+len(ee)]=np.where(ms.any(1),ms.argmax(1)+1,BIG)
    return tp,sl

R={}
for side,sn in ((+1,"LONG"),(-1,"SHORT")):
    tp,sl=fp(ent,TGT,STP,side)
    win=(tp<=LIM)&(tp<sl); los=(sl<=LIM)&~win
    j=np.minimum(ent+LIM,n-1); mo=(C[j]/C[ent]-1)*100*side
    gross=np.where(win,TGT,np.where(los,-STP,mo))
    R[sn]=((gross-COSTB)*LEVR, win)

ref=ent
F={}
F['atr_pct']=IND['atr14'][ref]/C[ref]*100
F['rsi']=IND['rsi14'][ref]; F['mfi']=IND['mfi14'][ref]
F['vol_ratio']=(IND['vsum20'][ref]/20)/(IND['vsum1440'][ref]/1440)
F['ret_1h']=(C[ref]/C[ref-60]-1)*100
F['ret_4h']=(C[ref]/C[ref-240]-1)*100
F['ret_24h']=(C[ref]/C[ref-1440]-1)*100
F['dist_24h_high']=(C[ref]/IND['hh1440'][ref]-1)*100
F['dist_24h_low']=(C[ref]/IND['ll1440'][ref]-1)*100
F['ema200h_dist']=(C[ref]/IND['ema200h'][ref]-1)*100
F['range24']=(IND['hh1440'][ref]-IND['ll1440'][ref])/C[ref]*100

def ms(y,m): return int(np.datetime64(f'{y}-{m:02d}-01').astype('datetime64[ms]').astype(np.int64))
tt=T[ent]
TR=tt<ms(2019,1); VA=(tt>=ms(2019,1))&(tt<ms(2020,1)); TE=tt>=ms(2023,1)
print(f"TRAIN {TR.sum():,}   VALIDATE {VA.sum():,}   TEST {TE.sum():,}   "
      f"(sealed 2020-2022 excluded)\n")
CONDS=[]
for f in F:
    for qq,lab in ((0.90,">=p90"),(0.95,">=p95"),(0.10,"<=p10"),(0.05,"<=p05")):
        q=np.nanquantile(F[f][TR],qq)
        CONDS.append((f"{f} {lab}",(F[f]>=q) if qq>0.5 else (F[f]<=q)))
qa=np.nanquantile(F['atr_pct'][TR],0.90); qv=np.nanquantile(F['vol_ratio'][TR],0.90)
qr=np.nanquantile(F['rsi'][TR],0.10); qd=np.nanquantile(F['dist_24h_low'][TR],0.10)
CONDS+=[("high ATR & high volume",(F['atr_pct']>=qa)&(F['vol_ratio']>=qv)),
        ("high ATR & RSI low",(F['atr_pct']>=qa)&(F['rsi']<=qr)),
        ("near 24h low & high vol",(F['dist_24h_low']<=qd)&(F['vol_ratio']>=qv))]
print(f"{'condition':<28}{'side':<6}" +
      "".join(f"{p:>26}" for p in ("TRAIN  n / win% / net","VALID  n / win% / net","TEST   n / win% / net")))
best=[]
for lbl,m in CONDS:
    for sn in ("LONG","SHORT"):
        net,win=R[sn]
        cells=[]
        ok=True
        for sel in (TR,VA,TE):
            mm=m&sel
            if mm.sum()<300: ok=False; cells.append("     too few          "); continue
            cells.append(f"{mm.sum():>7,} {win[mm].mean():>6.1%} {net[mm].mean():>+8.3f}")
        if not ok: continue
        print(f"{lbl:<28}{sn:<6}" + "".join(f"{c:>26}" for c in cells))
        nets=[net[m&s].mean() for s in (TR,VA,TE)]
        if all(x>0 for x in nets): best.append((lbl,sn,nets))
print(f"\n  conditions x sides tested: {len(CONDS)*2}")
print(f"  positive net EV in ALL THREE periods: {len(best)}")
for b in best: print("    ",b)
