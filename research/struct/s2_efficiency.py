#!/usr/bin/env python3
"""Drill-down on the one positive cell: trend + BOS + trend-efficiency filter.

Checks, in order:
  1  threshold sensitivity -- plateau or knife edge?
  2  temporal stability -- three eras
  3  long vs short
  4  cost sensitivity
  5  the multiple-testing context
"""
import sys, os, pickle, numpy as np
sys.path.insert(0,'research/struct'); sys.path.insert(0,'research/btc3')
import zigzag as Z, backtest as BT, events as E

T,O,H,L,C,V,N=E.load("data/spot/BTCUSDT-1m.pkl")
def agg(mins):
    ms=mins*60000; key=T-(T%ms)
    _,st=np.unique(key,return_index=True); st=np.sort(st); en=np.append(st[1:],len(T))
    return dict(t=key[st],o=O[st],h=np.maximum.reduceat(H,st),l=np.minimum.reduceat(L,st),
                c=C[en-1],v=np.add.reduceat(V,st),i1m=st)
b=agg(5); A=Z.atr(b['h'],b['l'],b['c'])
piv=Z.zigzag(b['h'],b['l'],A,theta=3.0)
S=Z.structure_state(len(b['c']),piv); D=Z.derived(b['c'],b['h'],b['l'],A,S)
c=b['c']
tr_up=S['trend']==1; tr_dn=S['trend']==-1
bos_up=(c>S['last_sh']); bos_up[1:]&=~(c[:-1]>S['last_sh'][:-1])
bos_dn=(c<S['last_sl']); bos_dn[1:]&=~(c[:-1]<S['last_sl'][:-1])
eff=D['efficiency']

def boot(R,iters=4000,seed=0):
    if len(R)<20: return (np.nan,np.nan)
    rg=np.random.default_rng(seed)
    m=np.array([rg.choice(R,len(R)).mean() for _ in range(iters)])
    return np.percentile(m,2.5),np.percentile(m,97.5)

print("1  EFFICIENCY THRESHOLD SENSITIVITY  (trend + BOS, trailing structural exit)\n")
print(f"  {'eff >':<8}{'n':>7}{'win%':>8}{'EV R':>9}{'  95% CI':>22}{'PF':>7}{'totR':>9}{'t':>7}")
for th in (0.0,0.20,0.25,0.30,0.35,0.40,0.45,0.50):
    sl=tr_up&bos_up&(eff>th); ss=tr_dn&bos_dn&(eff>th)
    tr=BT.run(b,A,S,D,sl,ss,exit_mode="trail_struct")
    st=BT.stats(tr)
    if not st: continue
    R=np.array([t['R'] for t in tr]); lo,hi=boot(R)
    print(f"  {th:<8.2f}{st['n']:>7}{st['win']:>8.1%}{st['ev']:>+9.3f}"
          f"   [{lo:+.3f},{hi:+.3f}]{st['pf']:>7.2f}{st['tot']:>+9.1f}{st['t']:>+7.2f}")

print("\n2  TEMPORAL STABILITY  (eff > 0.35)\n")
sl=tr_up&bos_up&(eff>0.35); ss=tr_dn&bos_dn&(eff>0.35)
tr=BT.run(b,A,S,D,sl,ss,exit_mode="trail_struct")
R=np.array([t['R'] for t in tr]); TT=np.array([t['t'] for t in tr])
def ms(y): return int(np.datetime64(f'{y}-01-01').astype('datetime64[ms]').astype(np.int64))
print(f"  {'era':<16}{'n':>6}{'win%':>8}{'EV R':>9}{'  95% CI':>22}{'totR':>9}")
for lbl,lo_,hi_ in (("2017-2018",ms(2017),ms(2019)),("2019",ms(2019),ms(2020)),
                    ("2023-2024",ms(2023),ms(2025)),("2025-2026",ms(2025),ms(2027))):
    m=(TT>=lo_)&(TT<hi_)
    if m.sum()<25: print(f"  {lbl:<16}{int(m.sum()):>6}  too few"); continue
    lo,hi=boot(R[m])
    print(f"  {lbl:<16}{int(m.sum()):>6}{(R[m]>0).mean():>8.1%}{R[m].mean():>+9.3f}"
          f"   [{lo:+.3f},{hi:+.3f}]{R[m].sum():>+9.1f}")

print("\n3  LONG vs SHORT  (eff > 0.35)\n")
SD=np.array([t['side'] for t in tr])
for lbl,m in (("LONG",SD>0),("SHORT",SD<0)):
    lo,hi=boot(R[m])
    print(f"  {lbl:<8}n={int(m.sum()):>5}  win {(R[m]>0).mean():>5.1%}  "
          f"EV {R[m].mean():>+7.3f}  CI [{lo:+.3f},{hi:+.3f}]  totR {R[m].sum():>+8.1f}")

print("\n4  COST SENSITIVITY  (eff > 0.35, trailing structural)\n")
print(f"  {'execution':<28}{'RT bps':>9}{'EV R':>9}{'  95% CI':>22}")
for lbl,ce,xe in (("maker in / maker out","maker","maker"),
                  ("maker in / taker out","maker","taker"),
                  ("taker in / taker out (used)","taker","taker")):
    t2=BT.run(b,A,S,D,sl,ss,exit_mode="trail_struct",cost_entry=ce,cost_exit=xe)
    R2=np.array([t['R'] for t in t2]); lo,hi=boot(R2)
    rt=(1.5 if ce=="maker" else 5.13)+(1.5 if xe=="maker" else 5.13)
    print(f"  {lbl:<28}{rt:>9.2f}{R2.mean():>+9.3f}   [{lo:+.3f},{hi:+.3f}]")

print("\n5  MULTIPLE TESTING CONTEXT")
print("  setups x exits already run: 30 cells. Expected significant at a=0.05: ~1.5")
print("  efficiency thresholds now added: 8 more.")
