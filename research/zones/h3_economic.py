#!/usr/bin/env python3
"""ECONOMIC TEST of the one surviving cell, plus HTF zones and out-of-sample.

An execution point that matters and that my earlier phases could not use: a
zone trade rests a LIMIT at the proximal edge. That is a MAKER fill by
construction, not a taker chase. Round trip falls from 10.26 bps to 6.63 bps
(maker in / taker out). Zone trading genuinely earns that.

Entry  : limit at the proximal edge, filled when price trades into it
Stop   : distal edge - buffer*ATR  (the zone is either right or it isn't)
Exit   : fixed R multiples AND unbounded trailing, compared
"""
import sys, os, pickle, numpy as np
sys.path.insert(0,'research/zones'); sys.path.insert(0,'research/btc3')
import zoneengine as ZE, events as E

MAKER=1.5/1e4; TAKER=4.5/1e4; HALF=0.63/1e4
COST_MT=MAKER+TAKER+HALF          # limit in, taker out
COST_TT=(TAKER+HALF)*2

def prep(path, tf=5):
    T,O,H,L,C,V,N=E.load(path)
    ms=tf*60000; key=T-(T%ms)
    _,st=np.unique(key,return_index=True); st=np.sort(st); en=np.append(st[1:],len(T))
    b=dict(t=key[st],o=O[st],h=np.maximum.reduceat(H,st),l=np.minimum.reduceat(L,st),
           c=C[en-1],v=np.add.reduceat(V,st))
    A=ZE.atr(b['h'],b['l'],b['c'])
    Z=ZE.find_zones(b['o'],b['h'],b['l'],b['c'],b['v'],A)
    return b,A,Z

def trades(b,A,Z,first_only=True,aligned_only=False,buf=0.25,rr=None,
           maxb=576,cost=COST_MT,trail=False):
    O,H,L,C=b['o'],b['h'],b['l'],b['c']; n=len(C)
    TE=ZE.touch_events(Z,H,L,C,A)
    out=[]
    for e in TE:
        if first_only and e['touch_idx']!=0: continue
        i=e['i']
        if i<250 or i>=n-maxb-2: continue
        side=e['side']
        if aligned_only:
            if np.sign(C[i]-C[i-200])!=side: continue
        entry=e['proximal']                       # limit rests here
        stop=e['distal']-buf*A[i] if side>0 else e['distal']+buf*A[i]
        risk=abs(entry-stop)
        if risk<=0 or risk/entry<0.0010 or risk/entry>0.06: continue
        # fill check: price must actually trade to the proximal edge
        if side>0 and L[i]>entry: continue
        if side<0 and H[i]<entry: continue
        tgt=entry+side*rr*risk if rr else None
        st_=stop; ex=None
        for j in range(i+1,min(i+1+maxb,n)):
            if trail:
                if side>0: st_=max(st_,C[j-1]-2.5*A[j])
                else:      st_=min(st_,C[j-1]+2.5*A[j])
            hs=(L[j]<=st_) if side>0 else (H[j]>=st_)
            ht=(tgt is not None) and ((H[j]>=tgt) if side>0 else (L[j]<=tgt))
            if hs and ht: ex=st_; break
            if hs: ex=st_; break
            if ht: ex=tgt; break
        if ex is None: ex=C[min(i+maxb,n-1)]
        R=side*(ex-entry)/risk - cost*entry/risk
        out.append((R, e['touch_idx'], side, b['t'][i], risk/entry*100))
    return np.array(out) if out else np.zeros((0,5))

def boot(R,it=4000,seed=0):
    rg=np.random.default_rng(seed)
    return tuple(np.percentile([rg.choice(R,len(R)).mean() for _ in range(it)],[2.5,97.5]))
def rep(lbl,M,extra=""):
    if len(M)<80: print(f"  {lbl:<44}{len(M):>7}  too few"); return None
    R=M[:,0]; w=R>0; lo,hi=boot(R)
    pf=R[w].sum()/max(-R[~w].sum(),1e-9)
    f="  <<<" if lo>0 else ""
    print(f"  {lbl:<44}{len(R):>7}{w.mean():>7.1%}{R.mean():>+9.3f}"
          f"   [{lo:+.3f},{hi:+.3f}]{pf:>7.2f}{R.sum():>+9.1f}{f}{extra}")
    return R

b5,A5,Z5=prep("data/spot/BTCUSDT-1m.pkl",5)
print(f"BTC 5m: {len(b5['c']):,} bars, {len(Z5):,} zones")
print(f"\n{'='*112}\nECONOMIC TEST — limit entry at the proximal edge (maker), "
      f"stop beyond distal edge\n{'='*112}")
print(f"  {'configuration':<44}{'n':>7}{'win%':>7}{'EV R':>9}{'  95% CI':>22}{'PF':>7}{'totR':>9}")
for rr in (1.0,1.5,2.0,3.0):
    rep(f"first touch, all, target {rr}R", trades(b5,A5,Z5,rr=rr))
print()
for rr in (1.0,1.5,2.0,3.0):
    rep(f"first touch, TREND-ALIGNED, target {rr}R", trades(b5,A5,Z5,aligned_only=True,rr=rr))
print()
rep("first touch, aligned, 2.5ATR trailing", trades(b5,A5,Z5,aligned_only=True,trail=True))
rep("first touch, all, 2.5ATR trailing", trades(b5,A5,Z5,trail=True))
print()
rep("aligned 2R, TAKER cost (no maker edge)",
    trades(b5,A5,Z5,aligned_only=True,rr=2.0,cost=COST_TT))
rep("aligned 2R, later touches only",
    trades(b5,A5,Z5,first_only=False,aligned_only=True,rr=2.0)[
        trades(b5,A5,Z5,first_only=False,aligned_only=True,rr=2.0)[:,1]>0])

print(f"\n{'='*112}\nHIGHER TIMEFRAME ZONES — the brief says these matter most\n{'='*112}")
print(f"  {'configuration':<44}{'n':>7}{'win%':>7}{'EV R':>9}{'  95% CI':>22}{'PF':>7}{'totR':>9}")
for tf,lab,mb in ((60,"1h",240),(240,"4h",120)):
    bh,Ah,Zh=prep("data/spot/BTCUSDT-1m.pkl",tf)
    print(f"  -- {lab} zones: {len(Zh):,} --")
    for rr in (1.5,2.0,3.0):
        rep(f"{lab} first touch, aligned, {rr}R",
            trades(bh,Ah,Zh,aligned_only=True,rr=rr,maxb=mb))
    rep(f"{lab} first touch, all, {rr}R", trades(bh,Ah,Zh,rr=2.0,maxb=mb))

print(f"\n{'='*112}\nOUT-OF-SAMPLE — the aligned 2R config across eras and assets\n{'='*112}")
def ms(y): return int(np.datetime64(f'{y}-01-01').astype('datetime64[ms]').astype(np.int64))
M=trades(b5,A5,Z5,aligned_only=True,rr=2.0)
print(f"  {'split':<24}{'n':>7}{'win%':>7}{'EV R':>9}{'  95% CI':>22}")
for lbl,a,z in (("2017-2019",ms(2017),ms(2020)),("2023-2024",ms(2023),ms(2025)),
                ("2025-2026",ms(2025),ms(2027))):
    m=(M[:,3]>=a)&(M[:,3]<z)
    if m.sum()<80: continue
    R=M[m,0]; lo,hi=boot(R)
    print(f"  {lbl:<24}{int(m.sum()):>7}{(R>0).mean():>7.1%}{R.mean():>+9.3f}   [{lo:+.3f},{hi:+.3f}]")
for lbl,m in (("LONG (demand)",M[:,2]>0),("SHORT (supply)",M[:,2]<0)):
    R=M[m,0]; lo,hi=boot(R)
    print(f"  {lbl:<24}{int(m.sum()):>7}{(R>0).mean():>7.1%}{R.mean():>+9.3f}   [{lo:+.3f},{hi:+.3f}]")
for sym,p in (("ETH","data/alt/ETHUSDT-1m.pkl"),("SOL","data/alt/SOLUSDT-1m.pkl"),
              ("XRP","data/alt/XRPUSDT-1m.pkl"),("DOGE","data/alt/DOGEUSDT-1m.pkl")):
    if not os.path.exists(p): continue
    bb,AA,ZZ=prep(p,5); MM=trades(bb,AA,ZZ,aligned_only=True,rr=2.0)
    if len(MM)<80: continue
    R=MM[:,0]; lo,hi=boot(R)
    print(f"  {sym:<24}{len(R):>7}{(R>0).mean():>7.1%}{R.mean():>+9.3f}   [{lo:+.3f},{hi:+.3f}]")
