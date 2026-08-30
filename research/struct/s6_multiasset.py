#!/usr/bin/env python3
"""Multi-asset: does market structure pay on higher-volatility alts?"""
import sys, os, pickle, numpy as np
sys.path.insert(0,'research/struct'); sys.path.insert(0,'research/btc3')
import zigzag as Z, backtest as BT, events as E

SYMS=[("BTCUSDT","data/spot/BTCUSDT-1m.pkl"),("ETHUSDT","data/alt/ETHUSDT-1m.pkl"),
      ("SOLUSDT","data/alt/SOLUSDT-1m.pkl"),("XRPUSDT","data/alt/XRPUSDT-1m.pkl"),
      ("DOGEUSDT","data/alt/DOGEUSDT-1m.pkl")]
def boot(R,it=3000):
    rg=np.random.default_rng(0)
    return tuple(np.percentile([rg.choice(R,len(R)).mean() for _ in range(it)],[2.5,97.5]))
print(f"{'symbol':<10}{'bars':>11}{'ATR%':>7}{'setup':<26}{'n':>7}{'win%':>7}"
      f"{'EV R':>9}{'  95% CI':>22}{'PF':>7}{'totR':>9}")
summary={}
for sym,path in SYMS:
    if not os.path.exists(path): print(f"{sym:<10} missing"); continue
    T,O,H,L,C,V,N=E.load(path)
    ms_=5*60000; key=T-(T%ms_)
    _,st=np.unique(key,return_index=True); st=np.sort(st); en=np.append(st[1:],len(T))
    b=dict(t=key[st],o=O[st],h=np.maximum.reduceat(H,st),l=np.minimum.reduceat(L,st),
           c=C[en-1],v=np.add.reduceat(V,st),i1m=st)
    A=Z.atr(b['h'],b['l'],b['c'])
    piv=Z.zigzag(b['h'],b['l'],A,theta=3.0)
    S=Z.structure_state(len(b['c']),piv); D=Z.derived(b['c'],b['h'],b['l'],A,S)
    c=b['c']
    tr_up=S['trend']==1; tr_dn=S['trend']==-1
    bu=(c>S['last_sh']); bu[1:]&=~(c[:-1]>S['last_sh'][:-1])
    bd=(c<S['last_sl']); bd[1:]&=~(c[:-1]<S['last_sl'][:-1])
    atrp=np.nanmedian(A/c)*100
    for lbl,(sl,ss) in (("trend+BOS, trail struct",(tr_up&bu,tr_dn&bd)),
                        ("trend+BOS+eff>0.35",(tr_up&bu&(D['efficiency']>0.35),
                                               tr_dn&bd&(D['efficiency']>0.35)))):
        tr=BT.run(b,A,S,D,sl,ss,exit_mode="trail_struct")
        s2=BT.stats(tr)
        if not s2: continue
        R=np.array([t['R'] for t in tr]); lo,hi=boot(R)
        flag="  <<<" if lo>0 else ""
        print(f"{sym:<10}{len(b['c']):>11,}{atrp:>7.3f}{lbl:<26}{s2['n']:>7}"
              f"{s2['win']:>7.1%}{s2['ev']:>+9.3f}   [{lo:+.3f},{hi:+.3f}]"
              f"{s2['pf']:>7.2f}{s2['tot']:>+9.1f}{flag}")
        summary[(sym,lbl)]=(s2['ev'],lo,hi,s2['n'])
    print()
pos=[k for k,v in summary.items() if v[1]>0]
print(f"cells with 95% CI above zero: {len(pos)} of {len(summary)}")
for k in pos: print("   ",k,summary[k])
