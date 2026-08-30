#!/usr/bin/env python3
"""Is the sealed-window long result STRUCTURE, or just beta?

2020-2022 BTC went 7,180 -> 68,734 -> 16,542. A long-biased system with a
6.3-hour median hold captures drift. The control: random long entries with the
SAME holding-period distribution and the SAME cost, on the same window.
"""
import sys, os, pickle, numpy as np
sys.path.insert(0,'research/struct'); sys.path.insert(0,'research/btc3')
import zigzag as Z, backtest as BT, events as E
MAKER=1.5/1e4; TAKER=4.5/1e4; HALF=0.63/1e4; COST=(TAKER+HALF)*2

def load5(path):
    T,O,H,L,C,V,N=E.load(path)
    ms=5*60000; key=T-(T%ms)
    _,st=np.unique(key,return_index=True); st=np.sort(st); en=np.append(st[1:],len(T))
    b=dict(t=key[st],o=O[st],h=np.maximum.reduceat(H,st),l=np.minimum.reduceat(L,st),
           c=C[en-1],v=np.add.reduceat(V,st))
    A=Z.atr(b['h'],b['l'],b['c'])
    piv=Z.zigzag(b['h'],b['l'],A,theta=3.0)
    return b,A,Z.structure_state(len(b['c']),piv),Z.derived(b['c'],b['h'],b['l'],A,Z.structure_state(len(b['c']),piv))

def boot(R,it=5000,seed=0):
    rg=np.random.default_rng(seed)
    return tuple(np.percentile([rg.choice(R,len(R)).mean() for _ in range(it)],[2.5,97.5]))

b,A,S,D=load5("data/sealed_spot/BTCUSDT-1m.pkl")
c=b['c']; n=len(c)
tr_up=S['trend']==1; tr_dn=S['trend']==-1
bu=(c>S['last_sh']); bu[1:]&=~(c[:-1]>S['last_sh'][:-1])
bd=(c<S['last_sl']); bd[1:]&=~(c[:-1]<S['last_sl'][:-1])
eff=D['efficiency']
tr=BT.run(b,A,S,D,tr_up&bu&(eff>0.35),tr_dn&bd&(eff>0.35),exit_mode="trail_struct")
R=np.array([t['R'] for t in tr]); SD=np.array([t['side'] for t in tr])
BARS=np.array([t['bars'] for t in tr]); RISK=np.array([t['risk_pct'] for t in tr])
L=BARS[SD>0]; RK=RISK[SD>0]
print(f"Actual LONG trades: n={len(L)}  EV {R[SD>0].mean():+.4f}R  "
      f"median hold {np.median(L):.0f} bars  median risk {np.median(RK):.2f}%")

# control: random long entries, same holding-period and risk distribution
rng=np.random.default_rng(0); sims=[]
for s in range(400):
    ev=[]
    for k in range(len(L)):
        i=rng.integers(300,n-3000)
        hold=int(L[rng.integers(0,len(L))]); risk=RK[rng.integers(0,len(RK))]/100
        entry=b['o'][i+1]; j=min(i+hold,n-1)
        gross=(c[j]-entry)/entry/risk
        ev.append(gross-COST/risk)
    sims.append(np.mean(ev))
sims=np.array(sims)
print(f"\nRANDOM LONG control ({len(sims)} simulations, matched hold and risk):")
print(f"  mean {sims.mean():+.4f}R   p5 {np.percentile(sims,5):+.4f}   "
      f"p50 {np.median(sims):+.4f}   p95 {np.percentile(sims,95):+.4f}")
act=R[SD>0].mean()
pv=(sims>=act).mean()
print(f"  actual structural LONG = {act:+.4f}R")
print(f"  fraction of random-long controls that BEAT it: {pv:.1%}")
print(f"  -> {'structure adds nothing beyond long exposure' if pv>0.10 else 'structure beats matched random longs'}")

print(f"\nSame control for SHORT:")
Sh=BARS[SD<0]; RKs=RISK[SD<0]
sims2=[]
for s in range(400):
    ev=[]
    for k in range(len(Sh)):
        i=rng.integers(300,n-3000)
        hold=int(Sh[rng.integers(0,len(Sh))]); risk=RKs[rng.integers(0,len(RKs))]/100
        entry=b['o'][i+1]; j=min(i+hold,n-1)
        ev.append(-(c[j]-entry)/entry/risk-COST/risk)
    sims2.append(np.mean(ev))
sims2=np.array(sims2); acts=R[SD<0].mean()
print(f"  random SHORT mean {sims2.mean():+.4f}R   actual structural SHORT {acts:+.4f}R   "
      f"beaten by {(sims2>=acts).mean():.1%} of controls")
print(f"\nBuy-and-hold reference over the sealed window: "
      f"{(c[-1]/c[0]-1)*100:+.0f}% total, peak-to-entry {(c.max()/c[0]-1)*100:+.0f}%")
