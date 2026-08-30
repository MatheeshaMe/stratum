#!/usr/bin/env python3
"""PHASE 13 -- the sealed 2020-2022 test. ONE SHOT.

The hypothesis is frozen in FROZEN_HYPOTHESIS.md. No parameter is read from,
or changed after, this result.
"""
import sys, os, pickle, numpy as np
sys.path.insert(0,'research/struct'); sys.path.insert(0,'research/btc3')
import zigzag as Z, backtest as BT, events as E

def load5(path):
    T,O,H,L,C,V,N=E.load(path)
    ms=5*60000; key=T-(T%ms)
    _,st=np.unique(key,return_index=True); st=np.sort(st); en=np.append(st[1:],len(T))
    b=dict(t=key[st],o=O[st],h=np.maximum.reduceat(H,st),l=np.minimum.reduceat(L,st),
           c=C[en-1],v=np.add.reduceat(V,st))
    A=Z.atr(b['h'],b['l'],b['c'])
    piv=Z.zigzag(b['h'],b['l'],A,theta=3.0)
    S=Z.structure_state(len(b['c']),piv); D=Z.derived(b['c'],b['h'],b['l'],A,S)
    return b,A,S,D,piv

def boot(R,it=5000,seed=0):
    rg=np.random.default_rng(seed)
    return tuple(np.percentile([rg.choice(R,len(R)).mean() for _ in range(it)],[2.5,97.5]))

b,A,S,D,piv=load5("data/sealed_spot/BTCUSDT-1m.pkl")
c=b['c']
print(f"SEALED WINDOW 2020-01-01 .. 2022-12-31")
print(f"  5m bars {len(c):,}   pivots {len(piv):,}   "
      f"BTC {c[0]:,.0f} -> {c[-1]:,.0f} (peak {c.max():,.0f})")
yrs=(b['t'][-1]-b['t'][0])/(365.25*86400*1000)
print(f"  regime: {yrs:.2f}y, {(c[-1]/c[0])**(1/yrs)-1:+.1%}/yr, "
      f"max drawdown {(1-(c/np.maximum.accumulate(c)).min()):.1%}\n")

tr_up=S['trend']==1; tr_dn=S['trend']==-1
bu=(c>S['last_sh']); bu[1:]&=~(c[:-1]>S['last_sh'][:-1])
bd=(c<S['last_sl']); bd[1:]&=~(c[:-1]<S['last_sl'][:-1])
eff=D['efficiency']
sl=tr_up&bu&(eff>0.35); ss=tr_dn&bd&(eff>0.35)
tr=BT.run(b,A,S,D,sl,ss,exit_mode="trail_struct")
st=BT.stats(tr)
R=np.array([t['R'] for t in tr]); SD=np.array([t['side'] for t in tr])
lo,hi=boot(R)
print("="*90)
print("FROZEN HYPOTHESIS RESULT  (trend + BOS + efficiency>0.35, trailing structural exit)")
print("="*90)
print(f"  n                {st['n']}")
print(f"  win rate         {st['win']:.1%}")
print(f"  EV per trade     {st['ev']:+.4f} R")
print(f"  95% CI           [{lo:+.4f}, {hi:+.4f}]")
print(f"  profit factor    {st['pf']:.3f}")
print(f"  total R          {st['tot']:+.1f}")
print(f"  max drawdown     {st['dd']:.1f} R")
print(f"  median hold      {st['med_bars']:.0f} bars ({st['med_bars']*5/60:.1f}h)")
print(f"  largest winner   {st['mx']:.1f} R")
print(f"  LONG  n={int((SD>0).sum())}  EV {R[SD>0].mean():+.4f}R")
print(f"  SHORT n={int((SD<0).sum())}  EV {R[SD<0].mean():+.4f}R")
print("\n  PRE-REGISTERED PASS CRITERIA")
c1=lo>0; c2=st['n']>=150; c3=st['pf']>1.0
c4=(R[SD>0].mean()>0 and R[SD<0].mean()>0) if (SD>0).any() and (SD<0).any() else False
for lbl,ok in (("1. EV>0 with CI excluding zero",c1),("2. n >= 150",c2),
               ("3. profit factor > 1.0",c3),("4. sign holds LONG and SHORT",c4)):
    print(f"    [{'PASS' if ok else 'FAIL'}] {lbl}")
print(f"\n  VERDICT: {'PASS' if all([c1,c2,c3,c4]) else 'FAIL'}")

print("\n" + "="*90)
print("CONTEXT -- unfiltered structural baseline on the same sealed window")
print("="*90)
tr0=BT.run(b,A,S,D,tr_up&bu,tr_dn&bd,exit_mode="trail_struct")
st0=BT.stats(tr0); R0=np.array([t['R'] for t in tr0]); l0,h0=boot(R0)
print(f"  trend + BOS, no filter:  n={st0['n']}  win {st0['win']:.1%}  "
      f"EV {st0['ev']:+.4f}R  CI [{l0:+.4f},{h0:+.4f}]  PF {st0['pf']:.3f}")
print("\n  by year:")
for y in (2020,2021,2022):
    a=int(np.datetime64(f'{y}-01-01').astype('datetime64[ms]').astype(np.int64))
    z=int(np.datetime64(f'{y+1}-01-01').astype('datetime64[ms]').astype(np.int64))
    TT=np.array([t['t'] for t in tr]); m=(TT>=a)&(TT<z)
    if m.sum()<15: print(f"    {y}  n={int(m.sum())} too few"); continue
    l2,h2=boot(R[m])
    print(f"    {y}  n={int(m.sum()):>4}  win {(R[m]>0).mean():>5.1%}  "
          f"EV {R[m].mean():>+8.4f}R  CI [{l2:+.4f},{h2:+.4f}]  totR {R[m].sum():>+7.1f}")
