#!/usr/bin/env python3
"""The honest version of 'real vs false breakout'.

The acceptance/failure split is defined using bars AFTER the breakout, so
comparing their forward paths is circular -- acceptance literally selects paths
that went up. The only non-circular question is:

    Using ONLY information available AT the breakout bar, can you predict
    whether the breakout will be accepted?

Purged, embargoed, forward-only CV. Baseline = the unconditional acceptance rate.
"""
import sys, os, pickle, numpy as np
sys.path.insert(0,'research/struct'); sys.path.insert(0,'research/btc3')
import zigzag as Z, events as E
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score, brier_score_loss

T,O,H,L,C,V,N=E.load("data/spot/BTCUSDT-1m.pkl")
def agg(mins):
    ms=mins*60000; key=T-(T%ms)
    _,st=np.unique(key,return_index=True); st=np.sort(st); en=np.append(st[1:],len(T))
    return dict(t=key[st],o=O[st],h=np.maximum.reduceat(H,st),l=np.minimum.reduceat(L,st),
                c=C[en-1],v=np.add.reduceat(V,st),i1m=st)
b=agg(5); A=Z.atr(b['h'],b['l'],b['c'])
piv=Z.zigzag(b['h'],b['l'],A,theta=3.0); S=Z.structure_state(len(b['c']),piv)
D=Z.derived(b['c'],b['h'],b['l'],A,S)
b60=agg(60); A60=Z.atr(b60['h'],b60['l'],b60['c'])
p60=Z.zigzag(b60['h'],b60['l'],A60,theta=3.0); S60=Z.structure_state(len(b60['c']),p60)
hi_=np.clip(np.searchsorted(b60['t'],b['t'],side='right')-2,0,len(b60['c'])-1)
trend_1h=S60['trend'][hi_]
c=b['c']; n=len(c); lvl=S['last_sh']
bos=(c>lvl); bos[1:]&=~(c[:-1]>lvl[:-1])
K=12
idx=np.where(bos)[0]; idx=idx[(idx>200)&(idx<n-K-2)]
y=np.zeros(len(idx))
for k,i in enumerate(idx):
    seg=c[i+1:i+1+K]
    two=np.any((seg[:-1]>lvl[i])&(seg[1:]>lvl[i]))
    back=np.any(seg<lvl[i])
    y[k]=1.0 if (two and not back) else 0.0
vma=np.convolve(b['v'],np.ones(20)/20,'full')[:n]
rng=(b['h']-b['l'])
F=np.column_stack([
  b['v'][idx]/np.where(vma[idx]==0,np.nan,vma[idx]),
  (c[idx]-b['l'][idx])/np.where(rng[idx]==0,np.nan,rng[idx]),
  rng[idx]/A[idx],
  D['efficiency'][idx], D['imp_atr'][idx], D['pb_frac'][idx],
  S['trend'][idx], trend_1h[idx],
  (c[idx]/lvl[idx]-1)*1e4,                      # how far beyond the level, bps
  A[idx]/c[idx]*100,
  ((b['t'][idx]//3600000)%24).astype(float),
  (c[idx]/c[idx-12]-1)*100, (c[idx]/c[idx-72]-1)*100])
ok=np.isfinite(F).all(1)
F,y,idx=F[ok],y[ok],idx[ok]
print(f"breakouts: {len(y):,}   unconditional acceptance rate: {y.mean():.1%}")
nf=5; edges=np.linspace(0,len(y),nf+1).astype(int); P=np.full(len(y),np.nan)
EMB=200
for f in range(1,nf):
    te=np.arange(edges[f],edges[f+1])
    tr=np.concatenate([np.arange(0,max(0,edges[f]-EMB)),
                       np.arange(min(len(y),edges[f+1]+EMB),len(y))])
    if len(te)<200 or len(tr)<1000: continue
    m=HistGradientBoostingClassifier(max_depth=4,max_iter=200,learning_rate=0.05,
        min_samples_leaf=100,random_state=0)
    m.fit(F[tr],y[tr]); P[te]=m.predict_proba(F[te])[:,1]
s=np.isfinite(P)
auc=roc_auc_score(y[s],P[s]); br=brier_score_loss(y[s],P[s])
brb=brier_score_loss(y[s],np.full(s.sum(),y[s].mean()))
print(f"purged CV  n={s.sum():,}  AUC={auc:.4f}  Brier={br:.4f} vs base {brb:.4f} "
      f"skill={1-br/brb:+.2%}")
print(f"\n  {'model decile':<16}{'n':>8}{'predicted':>11}{'actual':>9}")
q=np.quantile(P[s],np.linspace(0,1,11))
for i in range(10):
    m=(P>=q[i])&(P<q[i+1]) if i<9 else (P>=q[i])
    m&=s
    if m.sum()<50: continue
    print(f"  {i+1:<16}{int(m.sum()):>8}{P[m].mean():>11.1%}{y[m].mean():>9.1%}")
print("\n  If AUC is near 0.5, acceptance is not predictable at the breakout bar,")
print("  and the accepted/failed populations can only be separated in hindsight.")
