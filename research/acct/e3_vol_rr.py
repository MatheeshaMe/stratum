#!/usr/bin/env python3
"""E3/E5/E7 -- volatility buckets, risk:reward structures, opportunity frequency."""
import sys, os, pickle, numpy as np
sys.path.insert(0,"research/btc3")
import events as E
T,O,H,L,C,V,N=E.load("data/spot/BTCUSDT-1m.pkl")
n=len(C); IND=pickle.load(open("/tmp/btc3_ind.pkl","rb"))
D=pickle.load(open("/tmp/acct_fp.pkl","rb")); ent=D['ent']
COSTB=0.0663   # % of notional, maker-in/taker-out

# trailing ATR percentile -- causal, 30d window
atrp=IND['atr14']/C
W=43200
pct=np.full(n,np.nan)
step=1440
for a in range(W,n,step):
    w=atrp[a-W:a]; w=w[np.isfinite(w)]
    if len(w)<1000: continue
    hi=min(a+step,n)
    pct[a:hi]=np.searchsorted(np.sort(w), atrp[a:hi])/len(w)
vp=pct[ent]

def first_passage(e, t_pct, s_pct, side, chunk=4000, HMAX=1440):
    BIG=np.int32(10**6); tp=np.full(len(e),BIG,np.int32); sl=np.full(len(e),BIG,np.int32)
    off=np.arange(1,HMAX+1)
    for a in range(0,len(e),chunk):
        ee=e[a:a+chunk]; idx=ee[:,None]+off[None,:]; px=C[ee][:,None]
        rh=np.maximum.accumulate(H[idx],1)/px; rl=np.minimum.accumulate(L[idx],1)/px
        mt=(rh>=1+t_pct/100) if side>0 else (rl<=1-t_pct/100)
        ms=(rl<=1-s_pct/100) if side>0 else (rh>=1+s_pct/100)
        tp[a:a+len(ee)]=np.where(mt.any(1),mt.argmax(1)+1,BIG)
        sl[a:a+len(ee)]=np.where(ms.any(1),ms.argmax(1)+1,BIG)
    return tp,sl

BUCK=[("bottom 10%",0.0,0.10),("10-25%",0.10,0.25),("25-50%",0.25,0.50),
      ("50-75%",0.50,0.75),("75-90%",0.75,0.90),("90-95%",0.90,0.95),
      ("95-99%",0.95,0.99),("top 1%",0.99,1.01)]
LEV_T=[(10,0.30),(20,0.15),(5,0.60)]
print(f"{'='*118}\nVOLATILITY BUCKETS -- 1:1 trade, LONG, 4h limit\n{'='*118}")
for Lv,t in LEV_T:
    tp,sl=first_passage(ent,t,t,+1)
    lim=240
    win=(tp<=lim)&(tp<sl); los=(sl<=lim)&~win
    j=np.minimum(ent+lim,n-1); mo=(C[j]/C[ent]-1)*100
    gross=np.where(win,t,np.where(los,-t,mo))
    ttt=np.where(win,tp,np.nan).astype(float)
    print(f"\n  leverage {Lv}x  (BTC target {t}%, stop {t}%)")
    print(f"  {'vol bucket':<14}{'n':>8}{'P(hit tgt)':>12}{'P(tgt 1st)':>12}"
          f"{'med MFE%':>10}{'med MAE%':>10}{'med min to tgt':>16}{'net %acct':>11}")
    for lbl,lo,hi in BUCK:
        m=np.isfinite(vp)&(vp>=lo)&(vp<hi)
        if m.sum()<500: continue
        # MFE/MAE over the limit
        e2=ent[m]
        off=np.arange(1,lim+1); idx=e2[:,None]+off[None,:]; px=C[e2][:,None]
        mfe=(H[idx].max(1)/px[:,0]-1)*100; mae=(L[idx].min(1)/px[:,0]-1)*100
        net=(gross[m]-COSTB)*Lv
        tt=ttt[m][np.isfinite(ttt[m])]
        print(f"  {lbl:<14}{m.sum():>8,}{(tp[m]<=lim).mean():>12.1%}"
              f"{win[m].mean():>12.1%}{np.median(mfe):>10.3f}{np.median(mae):>10.3f}"
              f"{np.median(tt) if len(tt) else np.nan:>16.0f}{net.mean():>+11.4f}")

print(f"\n\n{'='*118}\nRISK:REWARD STRUCTURES -- 10x leverage (+3% acct needs a 0.30% BTC move)")
print(f"{'='*118}")
print(f"  {'r:r':<8}{'target%':>9}{'stop%':>8}{'side':<7}{'n':>8}{'P(win)':>9}"
      f"{'martingale':>12}{'gross %acct':>13}{'cost':>8}{'NET %acct':>11}{'  profit factor':>16}")
for rr in (1.0,1.5,2.0,3.0):
    t=0.30; s=t/rr
    for side,sn in ((+1,"LONG"),(-1,"SHORT")):
        tp,sl=first_passage(ent,t,s,side)
        lim=240
        win=(tp<=lim)&(tp<sl); los=(sl<=lim)&~win
        j=np.minimum(ent+lim,n-1); mo=(C[j]/C[ent]-1)*100*side
        gross=np.where(win,t,np.where(los,-s,mo))
        net=(gross-COSTB)*10
        mart=s/(s+t)
        pf=(gross[gross>0].sum()/abs(gross[gross<0].sum())) if (gross<0).any() else np.nan
        print(f"  1:{rr:<6.1f}{t:>9.3f}{s:>8.3f}{sn:<7}{len(ent):>8,}{win.mean():>9.1%}"
              f"{mart:>12.1%}{gross.mean()*10:>+13.4f}{COSTB*10:>8.3f}"
              f"{net.mean():>+11.4f}{pf:>16.3f}")

print(f"\n\n{'='*118}\nOPPORTUNITY FREQUENCY -- how often is a 0.30% BTC move (=+3% at 10x) available")
print(f"{'='*118}")
tp,sl=first_passage(ent,0.30,0.30,+1)
days=(T[ent[-1]]-T[ent[0]])/86400000
for lim,lab in ((60,"1h"),(240,"4h"),(1440,"24h")):
    hit=(tp<=lim); first=hit&(tp<sl)
    print(f"  within {lab:<4}: target touched {hit.mean():>6.1%} of entries "
          f"({hit.sum()/days*96/96:>6.1f} per day of 15m entries) | "
          f"reached BEFORE the stop {first.mean():>6.1%}")
hr=((T[ent]//3600000)%24)
print(f"\n  P(target before stop, 4h limit) by UTC hour, 10x/1:1:")
lim=240; win=(tp<=lim)&(tp<sl)
row=""
for h in range(24):
    m=hr==h
    if m.sum()<200: continue
    row+=f"{h:02d}h {win[m].mean():.1%}  "
    if (h+1)%6==0: print("   "+row); row=""
if row: print("   "+row)
