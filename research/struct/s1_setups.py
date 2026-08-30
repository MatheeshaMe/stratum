#!/usr/bin/env python3
"""Structural setups x exit modes. The core experiment."""
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
c=b['c']; n=len(c)
print(f"5m bars {n:,}  pivots {len(piv):,}")
tr_up=S['trend']==1; tr_dn=S['trend']==-1
# BOS = first bar whose close breaks the last confirmed swing (rising edge)
bos_up=(c>S['last_sh']); bos_up[1:]&=~(c[:-1]>S['last_sh'][:-1])
bos_dn=(c<S['last_sl']); bos_dn[1:]&=~(c[:-1]<S['last_sl'][:-1])
pb=D['pb_frac']; eff=D['efficiency']; imp=D['imp_atr']

SETUPS={
 "S1 trend + BOS (continuation)":      (tr_up&bos_up, tr_dn&bos_dn),
 "S2 BOS only (no trend filter)":      (bos_up, bos_dn),
 "S3 trend + BOS + shallow pullback":  (tr_up&bos_up&(pb<0.6), tr_dn&bos_dn&(pb<0.6)),
 "S4 CHoCH (reversal)":                (tr_dn&bos_up, tr_up&bos_dn),
 "S5 trend + BOS + efficient":         (tr_up&bos_up&(eff>0.35), tr_dn&bos_dn&(eff>0.35)),
 "S6 trend + BOS + big impulse":       (tr_up&bos_up&(imp>4), tr_dn&bos_dn&(imp>4)),
}
EXITS=[("trail_struct (unbounded)",dict(exit_mode="trail_struct")),
       ("trail 3xATR (unbounded)",dict(exit_mode="trail_atr")),
       ("fixed 1:2",dict(exit_mode="fixed",rr=2.0)),
       ("fixed 1:3",dict(exit_mode="fixed",rr=3.0)),
       ("trail_struct + 1:5 cap",dict(exit_mode="trail_struct",rr=5.0))]
print(f"\n{'setup':<34}{'exit':<26}{'n':>7}{'win%':>7}{'avgW':>7}{'avgL':>7}"
      f"{'EV R':>8}{'PF':>7}{'totR':>9}{'maxDD':>8}{'p99':>7}{'max':>7}{'t':>7}")
res={}
for sname,(sl,ss) in SETUPS.items():
    for ename,kw in EXITS:
        tr=BT.run(b,A,S,D,sl,ss,**kw)
        st=BT.stats(tr,f"{sname}|{ename}")
        if not st: continue
        res[(sname,ename)]=(st,tr)
        print(f"{sname:<34}{ename:<26}{st['n']:>7}{st['win']:>7.1%}{st['avg_w']:>7.2f}"
              f"{st['avg_l']:>7.2f}{st['ev']:>+8.3f}{st['pf']:>7.2f}{st['tot']:>+9.1f}"
              f"{st['dd']:>8.1f}{st['p99']:>7.1f}{st['mx']:>7.1f}{st['t']:>+7.2f}")
pickle.dump({k:v[0] for k,v in res.items()}, open("/tmp/struct_s1.pkl","wb"))
pickle.dump({k:v[1] for k,v in res.items()}, open("/tmp/struct_trades.pkl","wb"))
