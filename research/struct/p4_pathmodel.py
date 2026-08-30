#!/usr/bin/env python3
"""PHASE 4/5/6 -- the path model.

Not 'will the next candle be green'. The target is the TRADE OUTCOME:
    did this structural entry reach +k R before the structural stop?
for k in {0.5, 1, 2, 3, 5}. This is meta-labelling: the structural rule is the
primary model, the ML layer decides which of its signals to take.

Features are measured strictly AT the entry bar. Purged + embargoed forward CV.
Pooled across 5 assets, with a held-out asset test and a held-out era test.
"""
import sys, os, pickle, numpy as np
sys.path.insert(0,'research/struct'); sys.path.insert(0,'research/btc3')
import zigzag as Z, events as E
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, brier_score_loss

MAKER=1.5/1e4; TAKER=4.5/1e4; HALF=0.63/1e4; COST=(TAKER+HALF)*2
SYMS=[("BTC","data/spot/BTCUSDT-1m.pkl"),("ETH","data/alt/ETHUSDT-1m.pkl"),
      ("SOL","data/alt/SOLUSDT-1m.pkl"),("XRP","data/alt/XRPUSDT-1m.pkl"),
      ("DOGE","data/alt/DOGEUSDT-1m.pkl")]

def build(sym,path,buf=0.25,maxb=2000):
    T,O,H,L,C,V,N=E.load(path)
    ms=5*60000; key=T-(T%ms)
    _,st=np.unique(key,return_index=True); st=np.sort(st); en=np.append(st[1:],len(T))
    b=dict(t=key[st],o=O[st],h=np.maximum.reduceat(H,st),l=np.minimum.reduceat(L,st),
           c=C[en-1],v=np.add.reduceat(V,st),n=np.add.reduceat(N,st))
    A=Z.atr(b['h'],b['l'],b['c'])
    piv=Z.zigzag(b['h'],b['l'],A,theta=3.0)
    S=Z.structure_state(len(b['c']),piv); D=Z.derived(b['c'],b['h'],b['l'],A,S)
    n=len(b['c']); c,h,l,o,v=b['c'],b['h'],b['l'],b['o'],b['v']
    lsh,lsl=S['last_sh'],S['last_sl']
    up=S['trend']==1; dn=S['trend']==-1
    bu=(c>lsh); bu[1:]&=~(c[:-1]>lsh[:-1])
    bd=(c<lsl); bd[1:]&=~(c[:-1]<lsl[:-1])
    vma=np.convolve(v,np.ones(20)/20,'full')[:n]
    rng=h-l
    ev=[(i,+1) for i in np.where(up&bu)[0]]+[(i,-1) for i in np.where(dn&bd)[0]]
    ev=[(i,s) for i,s in ev if 300<i<n-maxb-2]
    ev.sort()
    F=[];Y=[];MT=[];TT=[];SD=[]
    for i,side in ev:
        a=A[i]
        if not np.isfinite(a) or a<=0: continue
        entry=o[i+1]
        stop=(lsl[i]-buf*a) if side>0 else (lsh[i]+buf*a)
        if not np.isfinite(stop): continue
        risk=abs(entry-stop)
        if risk<=0 or risk/entry<0.0015 or risk/entry>0.08: continue
        # walk the trade: max R reached before the structural trailing stop
        st_=stop; peak=-9e9; exi=None
        for j in range(i+1,min(i+1+maxb,n)):
            if side>0:
                peak=max(peak,(h[j]-entry)/risk)
                if np.isfinite(lsl[j]): st_=max(st_,lsl[j]-buf*A[j])
                if l[j]<=st_: exi=j; ex=st_; break
            else:
                peak=max(peak,(entry-l[j])/risk)
                if np.isfinite(lsh[j]): st_=min(st_,lsh[j]+buf*A[j])
                if h[j]>=st_: exi=j; ex=st_; break
        if exi is None: exi=min(i+maxb,n-1); ex=c[exi]
        R=side*(ex-entry)/risk - COST*entry/risk
        lvl=lsh[i] if side>0 else lsl[i]
        F.append([v[i]/max(vma[i],1e-9), (c[i]-l[i])/max(rng[i],1e-9), rng[i]/a,
                  D['efficiency'][i], D['imp_atr'][i], D['pb_frac'][i],
                  side*(c[i]/lvl-1)*1e4, a/c[i]*100, S['n_piv'][i],
                  (c[i]/c[i-12]-1)*100*side, (c[i]/c[i-72]-1)*100*side,
                  (c[i]/c[i-288]-1)*100*side,
                  ((b['t'][i]//3600000)%24), risk/entry*100,
                  b['n'][i]/max(v[i],1e-9)*1e6, side])
        Y.append(peak); MT.append(R); TT.append(b['t'][i]); SD.append(side)
    return (np.array(F),np.array(Y),np.array(MT),np.array(TT,dtype=np.int64),
            np.array(SD),np.full(len(F),sym,dtype=object))

CACHE="/tmp/p4_pool.pkl"
if os.path.exists(CACHE):
    F,Y,MT,TT,SD,SY=pickle.load(open(CACHE,"rb"))
else:
    parts=[build(s,p) for s,p in SYMS if os.path.exists(p)]
    F=np.vstack([p[0] for p in parts]); Y=np.concatenate([p[1] for p in parts])
    MT=np.concatenate([p[2] for p in parts]); TT=np.concatenate([p[3] for p in parts])
    SD=np.concatenate([p[4] for p in parts]); SY=np.concatenate([p[5] for p in parts])
    pickle.dump((F,Y,MT,TT,SD,SY),open(CACHE,"wb"))
ok=np.isfinite(F).all(1)&np.isfinite(Y)&np.isfinite(MT)
F,Y,MT,TT,SD,SY=F[ok],Y[ok],MT[ok],TT[ok],SD[ok],SY[ok]
order=np.argsort(TT); F,Y,MT,TT,SD,SY=F[order],Y[order],MT[order],TT[order],SD[order],SY[order]
print(f"pooled structural entries: {len(Y):,} across {len(set(SY))} assets")
print(f"  unconditional EV/trade: {MT.mean():+.4f} R   win rate {(MT>0).mean():.1%}")
print(f"  peak-R distribution: median {np.median(Y):.2f}  p75 {np.percentile(Y,75):.2f} "
      f"p90 {np.percentile(Y,90):.2f}  p99 {np.percentile(Y,99):.2f}\n")

def purged(nn, nf=6, emb=300):
    ed=np.linspace(0,nn,nf+1).astype(int)
    for f in range(1,nf):
        te=np.arange(ed[f],ed[f+1])
        tr=np.concatenate([np.arange(0,max(0,ed[f]-emb)),
                           np.arange(min(nn,ed[f+1]+emb),nn)])
        if len(te)>300 and len(tr)>2000: yield tr,te

print(f"{'target':<28}{'base':>8}{'AUC gbm':>10}{'AUC logit':>11}{'Brier skill':>13}")
MODELS={}
for k in (0.5,1.0,2.0,3.0,5.0):
    y=(Y>=k).astype(float)
    P=np.full(len(y),np.nan); PL=np.full(len(y),np.nan)
    for tr,te in purged(len(y)):
        m=HistGradientBoostingClassifier(max_depth=4,max_iter=250,learning_rate=0.05,
            min_samples_leaf=150,l2_regularization=1.0,random_state=0)
        m.fit(F[tr],y[tr]); P[te]=m.predict_proba(F[te])[:,1]
        sc=StandardScaler().fit(F[tr])
        lg=LogisticRegression(max_iter=2000,C=0.5).fit(sc.transform(F[tr]),y[tr])
        PL[te]=lg.predict_proba(sc.transform(F[te]))[:,1]
    s=np.isfinite(P)
    auc=roc_auc_score(y[s],P[s]); aucl=roc_auc_score(y[s],PL[s])
    br=brier_score_loss(y[s],P[s]); bb=brier_score_loss(y[s],np.full(s.sum(),y[s].mean()))
    print(f"P(peak >= {k:>3.1f}R before stop){y.mean():>8.1%}{auc:>10.4f}{aucl:>11.4f}"
          f"{1-br/bb:>12.2%}")
    MODELS[k]=P
pickle.dump((MODELS,MT,TT,SD,SY,Y),open("/tmp/p4_models.pkl","wb"))
