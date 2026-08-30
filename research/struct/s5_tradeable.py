#!/usr/bin/env python3
"""Does predictable breakout-acceptance translate into money?

AUC 0.635 on acceptance is real. Acceptance is a PATH property, not a P&L
outcome. This trades the model's top deciles with a structural stop and an
unbounded structural exit, full taker cost, and splits by era.
"""
import sys, os, pickle, numpy as np
sys.path.insert(0,'research/struct'); sys.path.insert(0,'research/btc3')
import zigzag as Z, events as E
from sklearn.ensemble import HistGradientBoostingClassifier

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
K=12; idx=np.where(bos)[0]; idx=idx[(idx>200)&(idx<n-3000)]
y=np.array([1.0 if (np.any((c[i+1:i+1+K][:-1]>lvl[i])&(c[i+1:i+1+K][1:]>lvl[i]))
                    and not np.any(c[i+1:i+1+K]<lvl[i])) else 0.0 for i in idx])
vma=np.convolve(b['v'],np.ones(20)/20,'full')[:n]; rng=b['h']-b['l']
F=np.column_stack([b['v'][idx]/np.where(vma[idx]==0,np.nan,vma[idx]),
  (c[idx]-b['l'][idx])/np.where(rng[idx]==0,np.nan,rng[idx]), rng[idx]/A[idx],
  D['efficiency'][idx], D['imp_atr'][idx], D['pb_frac'][idx],
  S['trend'][idx], trend_1h[idx], (c[idx]/lvl[idx]-1)*1e4, A[idx]/c[idx]*100,
  ((b['t'][idx]//3600000)%24).astype(float),
  (c[idx]/c[idx-12]-1)*100, (c[idx]/c[idx-72]-1)*100])
ok=np.isfinite(F).all(1); F,y,idx=F[ok],y[ok],idx[ok]
nf=5; edges=np.linspace(0,len(y),nf+1).astype(int); P=np.full(len(y),np.nan); EMB=200
for f in range(1,nf):
    te=np.arange(edges[f],edges[f+1])
    tr=np.concatenate([np.arange(0,max(0,edges[f]-EMB)),
                       np.arange(min(len(y),edges[f+1]+EMB),len(y))])
    m=HistGradientBoostingClassifier(max_depth=4,max_iter=200,learning_rate=0.05,
        min_samples_leaf=100,random_state=0)
    m.fit(F[tr],y[tr]); P[te]=m.predict_proba(F[te])[:,1]

MAKER=1.5/1e4; TAKER=4.5/1e4; HALF=0.63/1e4
def trade(i, exit_mode="trail_struct", rr=None, buf=0.25, maxb=2000):
    entry=b['o'][i+1]; stop=S['last_sl'][i]-buf*A[i]
    if not np.isfinite(stop): return None
    risk=entry-stop
    if risk<=0 or risk/entry<0.0015 or risk/entry>0.08: return None
    tgt=entry+rr*risk if rr else None
    for j in range(i+1,min(i+1+maxb,n)):
        if exit_mode=="trail_struct" and np.isfinite(S['last_sl'][j]):
            stop=max(stop,S['last_sl'][j]-buf*A[j])
        hs=b['l'][j]<=stop; ht=(tgt is not None) and b['h'][j]>=tgt
        if hs: return ((stop-entry)/risk-((TAKER+HALF)*2)*entry/risk, j-i)
        if ht: return ((tgt-entry)/risk-((TAKER+HALF)+MAKER)*entry/risk, j-i)
    j=min(i+maxb,n-1)
    return ((c[j]-entry)/risk-((TAKER+HALF)*2)*entry/risk, j-i)

s=np.isfinite(P)
q=np.quantile(P[s],[0.5,0.7,0.8,0.9])
def ms(yy): return int(np.datetime64(f'{yy}-01-01').astype('datetime64[ms]').astype(np.int64))
tt=b['t'][idx]
print("Trading the acceptance model's top slices. Structural stop, unbounded")
print("trailing structural exit, taker in / taker out.\n")
print(f"{'selection':<22}{'n':>7}{'acc%':>7}{'win%':>7}{'EV R':>9}{'  95% CI':>22}"
      f"{'PF':>7}{'totR':>9}{'medBars':>9}")
def boot(R,it=4000):
    rg=np.random.default_rng(0)
    m=np.array([rg.choice(R,len(R)).mean() for _ in range(it)])
    return np.percentile(m,2.5),np.percentile(m,97.5)
store={}
for lbl,sel in (("all breakouts",s),("top 50%",s&(P>=q[0])),("top 30%",s&(P>=q[1])),
                ("top 20%",s&(P>=q[2])),("top 10%",s&(P>=q[3]))):
    out=[trade(i) for i in idx[sel]]
    R=np.array([o[0] for o in out if o]); B=np.array([o[1] for o in out if o])
    if len(R)<50: continue
    lo,hi=boot(R); w=R>0
    pf=R[w].sum()/max(-R[~w].sum(),1e-9)
    store[lbl]=(R,tt[sel][:len(R)])
    flag="  <<<" if lo>0 else ""
    print(f"{lbl:<22}{len(R):>7}{y[sel].mean():>7.1%}{w.mean():>7.1%}{R.mean():>+9.3f}"
          f"   [{lo:+.3f},{hi:+.3f}]{pf:>7.2f}{R.sum():>+9.1f}{np.median(B):>9.0f}{flag}")
print(f"\nTEMPORAL SPLIT of the top-10% slice")
R,tts=store.get("top 10%",(None,None))
if R is not None:
    for lbl,a,z in (("2017-2018",ms(2017),ms(2019)),("2019",ms(2019),ms(2020)),
                    ("2023-2024",ms(2023),ms(2025)),("2025-2026",ms(2025),ms(2027))):
        m=(tts>=a)&(tts<z)
        if m.sum()<25: print(f"  {lbl:<12}{int(m.sum()):>5}  too few"); continue
        lo,hi=boot(R[m])
        print(f"  {lbl:<12}n={int(m.sum()):>4}  win {(R[m]>0).mean():>5.1%}  "
              f"EV {R[m].mean():>+7.3f}  CI [{lo:+.3f},{hi:+.3f}]  totR {R[m].sum():>+7.1f}")
