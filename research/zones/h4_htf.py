#!/usr/bin/env python3
"""Validation of the one live candidate: 1h zones, first touch, trend-aligned, 3R.

The sealed 2020-2022 window was SPENT in the prior phase, so there is no clean
holdout left. Validation here is: cross-asset, cross-era, and parameter
perturbation. A candidate that needs one exact parameter set is rejected.
"""
import sys, os, pickle, numpy as np
sys.path.insert(0,'research/zones'); sys.path.insert(0,'research/btc3')
import zoneengine as ZE, events as E
MAKER=1.5/1e4; TAKER=4.5/1e4; HALF=0.63/1e4; COST=MAKER+TAKER+HALF

def prep(path,tf):
    T,O,H,L,C,V,N=E.load(path)
    ms=tf*60000; key=T-(T%ms)
    _,st=np.unique(key,return_index=True); st=np.sort(st); en=np.append(st[1:],len(T))
    b=dict(t=key[st],o=O[st],h=np.maximum.reduceat(H,st),l=np.minimum.reduceat(L,st),
           c=C[en-1],v=np.add.reduceat(V,st))
    A=ZE.atr(b['h'],b['l'],b['c'])
    return b,A
def zones(b,A,**kw): return ZE.find_zones(b['o'],b['h'],b['l'],b['c'],b['v'],A,**kw)
def trades(b,A,Z,rr=3.0,buf=0.25,maxb=120,trend_lb=200,aligned=True,cost=COST):
    O,H,L,C=b['o'],b['h'],b['l'],b['c']; n=len(C)
    out=[]
    for e in ZE.touch_events(Z,H,L,C,A):
        if e['touch_idx']!=0: continue
        i=e['i']
        if i<trend_lb+50 or i>=n-maxb-2: continue
        side=e['side']
        if aligned and np.sign(C[i]-C[i-trend_lb])!=side: continue
        entry=e['proximal']
        stop=e['distal']-buf*A[i] if side>0 else e['distal']+buf*A[i]
        risk=abs(entry-stop)
        if risk<=0 or risk/entry<0.0010 or risk/entry>0.10: continue
        if (side>0 and L[i]>entry) or (side<0 and H[i]<entry): continue
        tgt=entry+side*rr*risk; ex=None
        for j in range(i+1,min(i+1+maxb,n)):
            hs=(L[j]<=stop) if side>0 else (H[j]>=stop)
            ht=(H[j]>=tgt) if side>0 else (L[j]<=tgt)
            if hs: ex=stop; break
            if ht: ex=tgt; break
        if ex is None: ex=C[min(i+maxb,n-1)]
        out.append((side*(ex-entry)/risk-cost*entry/risk, side, b['t'][i]))
    return np.array(out) if out else np.zeros((0,3))
def boot(R,it=4000,seed=0):
    rg=np.random.default_rng(seed)
    return tuple(np.percentile([rg.choice(R,len(R)).mean() for _ in range(it)],[2.5,97.5]))
def rep(lbl,M):
    if len(M)<60: print(f"  {lbl:<38}{len(M):>6}  too few"); return
    R=M[:,0]; w=R>0; lo,hi=boot(R)
    print(f"  {lbl:<38}{len(R):>6}{w.mean():>7.1%}{R.mean():>+9.3f}   [{lo:+.3f},{hi:+.3f}]"
          f"{R[w].sum()/max(-R[~w].sum(),1e-9):>7.2f}{'  <<<' if lo>0 else ''}")

b,A=prep("data/spot/BTCUSDT-1m.pkl",60); Z=zones(b,A)
print(f"BTC 1h: {len(b['c']):,} bars, {len(Z):,} zones")
print(f"\n{'='*100}\nPARAMETER PERTURBATION — a plateau, or one lucky cell?\n{'='*100}")
print(f"  {'config':<38}{'n':>6}{'win%':>7}{'EV R':>9}{'  95% CI':>22}{'PF':>7}")
for rr in (2.0,2.5,3.0,4.0,5.0): rep(f"target {rr}R (buf 0.25, hold 120)", trades(b,A,Z,rr=rr))
print()
for buf in (0.0,0.25,0.5,1.0): rep(f"stop buffer {buf} ATR (3R)", trades(b,A,Z,buf=buf))
print()
for mb in (48,120,240,480): rep(f"max hold {mb} bars ({mb}h) (3R)", trades(b,A,Z,maxb=mb))
print()
for lb in (100,200,400): rep(f"trend lookback {lb} bars (3R)", trades(b,A,Z,trend_lb=lb))
print()
for imp in (1.5,2.0,2.5,3.0):
    Zi=zones(b,A,imp_min_atr=imp)
    rep(f"zone impulse >= {imp} ATR (3R)", trades(b,A,Zi))

print(f"\n{'='*100}\nCROSS-ERA and CROSS-ASSET (1h, aligned, 3R)\n{'='*100}")
def ms(y): return int(np.datetime64(f'{y}-01-01').astype('datetime64[ms]').astype(np.int64))
M=trades(b,A,Z)
print(f"  {'split':<38}{'n':>6}{'win%':>7}{'EV R':>9}{'  95% CI':>22}{'PF':>7}")
for lbl,a_,z_ in (("BTC 2017-2019",ms(2017),ms(2020)),("BTC 2023-2024",ms(2023),ms(2025)),
                  ("BTC 2025-2026",ms(2025),ms(2027))):
    m=(M[:,2]>=a_)&(M[:,2]<z_); rep(lbl,M[m])
for lbl,m in (("BTC LONG (demand)",M[:,1]>0),("BTC SHORT (supply)",M[:,1]<0)): rep(lbl,M[m])
POOL=[M]
for sym,p in (("ETH","data/alt/ETHUSDT-1m.pkl"),("SOL","data/alt/SOLUSDT-1m.pkl"),
              ("XRP","data/alt/XRPUSDT-1m.pkl"),("DOGE","data/alt/DOGEUSDT-1m.pkl")):
    if not os.path.exists(p): continue
    bb,AA=prep(p,60); ZZ=zones(bb,AA); MM=trades(bb,AA,ZZ)
    rep(sym,MM); POOL.append(MM)
ALL=np.vstack(POOL); rep("POOLED all 5 assets",ALL)
print(f"\n  pooled opportunity rate: {len(ALL)} trades over ~9y x 5 assets "
      f"= {len(ALL)/9/5:.1f} per asset-year")
pickle.dump(ALL,open("/tmp/zones_htf.pkl","wb"))
