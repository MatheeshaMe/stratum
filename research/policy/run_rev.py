#!/usr/bin/env python3
"""The two actions that came out positive: L_REV and S_REV.
Entry-timing sensitivity, holdout, cross-asset, and long/short as separate policies."""
import sys, os, pickle, numpy as np, itertools
sys.path.insert(0,'research/policy'); sys.path.insert(0,'research/btc3')
import engine as EN, events as E
from run_policy import prep, boot, ms, DISC, VALD, HELD

def sample_rev(b,ctx,lo,hi,entry_mode="close",manage="target",maxb=120):
    n=len(b['c']); C=b['c']; O=b['o']; rows=[]
    for i in range(600,n-maxb-3):
        t=b['t'][i]
        if not (lo<=t<hi): continue
        for a in ("L_REV","S_REV"):
            trig=EN.action_trigger(a,b,ctx,i)
            if trig is None: continue
            side,_,cost=trig
            if entry_mode=="close":
                ei,epx=i,C[i]
            elif entry_mode=="next_open":
                ei,epx=i+1,O[i+1]
            else:                                    # next close
                ei,epx=i+1,C[i+1]
            r=EN.run_trade(b,ctx,ei,side,epx,cost,manage=manage,maxb=maxb)
            if r is None: continue
            rows.append((r['R'],side,t,r['rr'],r['bars'],1.0 if a=="S_REV" else 0.0))
    return np.array(rows) if rows else np.zeros((0,6))

def rep(lbl,R,extra=""):
    if len(R)<25: print(f"  {lbl:<40}{len(R):>6}  too few"); return None
    lo,hi=boot(R); w=R>0
    print(f"  {lbl:<40}{len(R):>6}{w.mean():>7.1%}{R.mean():>+9.3f}"
          f"   [{lo:+.3f},{hi:+.3f}]{R[w].sum()/max(-R[~w].sum(),1e-9):>7.2f}"
          f"{'  <<<' if lo>0 else ''}{extra}")
    return R

b,ctx=prep("data/spot/BTCUSDT-1m-full.pkl")
print("ENTRY-TIMING SENSITIVITY (BTC, discovery window)")
print(f"  {'entry model':<40}{'n':>6}{'win%':>7}{'EV R':>9}{'  95% CI':>22}{'PF':>7}")
for em in ("close","next_open","next_close"):
    M=sample_rev(b,ctx,*DISC,entry_mode=em)
    rep(f"REV entry at {em}",M[:,0])

print("\nSPLIT BY SIDE — long and short as separate policies (entry next_open)")
print(f"  {'policy / window':<40}{'n':>6}{'win%':>7}{'EV R':>9}{'  95% CI':>22}{'PF':>7}")
for wname,W in (("discovery",DISC),("validation",VALD)):
    M=sample_rev(b,ctx,*W,entry_mode="next_open")
    rep(f"S_REV (short, upside sweep at premium) {wname[:4]}",M[M[:,5]==1,0])
    rep(f"L_REV (long, downside sweep at discount) {wname[:4]}",M[M[:,5]==0,0])

print("\n" + "="*100)
print("HOLDOUT 2025-01 .. 2026-07 — one look")
print("="*100)
print(f"  {'policy':<40}{'n':>6}{'win%':>7}{'EV R':>9}{'  95% CI':>22}{'PF':>7}")
MH=sample_rev(b,ctx,*HELD,entry_mode="next_open")
rep("BOTH sides",MH[:,0])
rep("S_REV only",MH[MH[:,5]==1,0])
rep("L_REV only",MH[MH[:,5]==0,0])

print("\n" + "="*100)
print("CROSS-ASSET — full period, no refit (entry next_open)")
print("="*100)
print(f"  {'asset / policy':<40}{'n':>6}{'win%':>7}{'EV R':>9}{'  95% CI':>22}{'PF':>7}")
pool_s=[]; pool_l=[]
for sym,p in (("ETH","data/alt/ETHUSDT-1m.pkl"),("SOL","data/alt/SOLUSDT-1m.pkl"),
              ("XRP","data/alt/XRPUSDT-1m.pkl"),("DOGE","data/alt/DOGEUSDT-1m.pkl")):
    if not os.path.exists(p): continue
    bb,cc=prep(p); MM=sample_rev(bb,cc,0,10**15,entry_mode="next_open")
    s=MM[MM[:,5]==1,0]; l=MM[MM[:,5]==0,0]
    rep(f"{sym} S_REV",s); rep(f"{sym} L_REV",l)
    pool_s.append(s); pool_l.append(l)
if pool_s:
    rep("POOLED alts S_REV",np.concatenate(pool_s))
    rep("POOLED alts L_REV",np.concatenate(pool_l))
pickle.dump((MH,),open("/tmp/pol_rev.pkl","wb"))
