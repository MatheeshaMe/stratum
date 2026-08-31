#!/usr/bin/env python3
"""C9 FIXED: the stop is live from the entry bar. Full re-run of the candidate."""
import sys, os, pickle, numpy as np
sys.path.insert(0,'research/zones'); sys.path.insert(0,'research/btc3')
import zoneengine as ZE, events as E
MAKER=1.5/1e4; TAKER=4.5/1e4; HALF=0.63/1e4; COST=MAKER+TAKER+HALF
SYMS=[("BTC","data/spot/BTCUSDT-1m.pkl"),("ETH","data/alt/ETHUSDT-1m.pkl"),
      ("SOL","data/alt/SOLUSDT-1m.pkl"),("XRP","data/alt/XRPUSDT-1m.pkl"),
      ("DOGE","data/alt/DOGEUSDT-1m.pkl")]
def prep(path,tf=60):
    T,O,H,L,C,V,N=E.load(path)
    ms=tf*60000; key=T-(T%ms)
    _,st=np.unique(key,return_index=True); st=np.sort(st); en=np.append(st[1:],len(T))
    b=dict(t=key[st],o=O[st],h=np.maximum.reduceat(H,st),l=np.minimum.reduceat(L,st),
           c=C[en-1],v=np.add.reduceat(V,st))
    return b, ZE.atr(b['h'],b['l'],b['c'])
def walk(b,A,i,side,entry,stop,rr=3.0,maxb=120,cost=COST,entry_bar_live=True):
    H,L,C=b['h'],b['l'],b['c']; n=len(C)
    risk=abs(entry-stop)
    if risk<=0 or risk/entry<0.0010 or risk/entry>0.10: return None
    tgt=entry+side*rr*risk
    start = i if entry_bar_live else i+1
    for j in range(start,min(i+1+maxb,n)):
        if j==i:
            # C9: after the limit fills during bar i, the rest of bar i can stop us
            hs=(L[j]<=stop) if side>0 else (H[j]>=stop)
            if hs: return side*(stop-entry)/risk-cost*entry/risk
            continue
        if (L[j]<=stop) if side>0 else (H[j]>=stop):
            return side*(stop-entry)/risk-cost*entry/risk
        if (H[j]>=tgt) if side>0 else (L[j]<=tgt):
            return side*(tgt-entry)/risk-cost*entry/risk
    j=min(i+maxb,n-1)
    return side*(C[j]-entry)/risk-cost*entry/risk
def boot(R,it=4000,seed=0):
    rg=np.random.default_rng(seed)
    return tuple(np.percentile([rg.choice(R,len(R)).mean() for _ in range(it)],[2.5,97.5]))

def collect(entry_bar_live, rr=3.0, imp=2.0, aligned=True):
    per={}; allr=[]
    for sym,p in SYMS:
        if not os.path.exists(p): continue
        b,A=prep(p); C,H,L=b['c'],b['h'],b['l']; n=len(C)
        Z=ZE.find_zones(b['o'],b['h'],b['l'],b['c'],b['v'],A,imp_min_atr=imp)
        out=[]
        for e in ZE.touch_events(Z,H,L,C,A):
            if e['touch_idx']!=0: continue
            i=e['i']
            if i<250 or i>=n-122: continue
            side=e['side']
            if aligned and np.sign(C[i]-C[i-200])!=side: continue
            entry=e['proximal']; stop=e['distal']-0.25*A[i] if side>0 else e['distal']+0.25*A[i]
            if (side>0 and L[i]>entry) or (side<0 and H[i]<entry): continue
            r=walk(b,A,i,side,entry,stop,rr=rr,entry_bar_live=entry_bar_live)
            if r is not None: out.append((r,side,b['t'][i]))
        if out: per[sym]=np.array(out); allr.append(np.array(out))
    return per, (np.vstack(allr) if allr else np.zeros((0,3)))

print("="*104)
print("C9 IMPACT — same configuration, stop live from the entry bar")
print("="*104)
print(f"  {'fill model':<44}{'n':>8}{'win%':>8}{'EV R':>9}{'  95% CI':>22}{'PF':>7}")
for lbl,ebl in (("OPTIMISTIC (stop from bar i+1) -- the bug",False),
                ("CORRECT (stop live on the entry bar)",True)):
    _,M=collect(ebl)
    R=M[:,0]; w=R>0; lo,hi=boot(R)
    print(f"  {lbl:<44}{len(R):>8,}{w.mean():>8.1%}{R.mean():>+9.3f}"
          f"   [{lo:+.3f},{hi:+.3f}]{R[w].sum()/max(-R[~w].sum(),1e-9):>7.2f}")

per,M=collect(True)
print(f"\n{'='*104}\nCORRECTED RESULT — 1h zones, first touch, trend-aligned, 3R\n{'='*104}")
print(f"  {'split':<28}{'n':>8}{'win%':>8}{'EV R':>9}{'  95% CI':>22}{'PF':>7}")
def rep(lbl,R):
    if len(R)<60: print(f"  {lbl:<28}{len(R):>8}  too few"); return
    w=R>0; lo,hi=boot(R)
    print(f"  {lbl:<28}{len(R):>8,}{w.mean():>8.1%}{R.mean():>+9.3f}"
          f"   [{lo:+.3f},{hi:+.3f}]{R[w].sum()/max(-R[~w].sum(),1e-9):>7.2f}"
          f"{'  <<<' if lo>0 else ''}")
rep("POOLED all 5 assets",M[:,0])
for sym,X in per.items(): rep(sym,X[:,0])
rep("LONG (demand)",M[M[:,1]>0,0]); rep("SHORT (supply)",M[M[:,1]<0,0])
def ms(y): return int(np.datetime64(f'{y}-01-01').astype('datetime64[ms]').astype(np.int64))
for lbl,a_,z_ in (("2017-2019",ms(2017),ms(2020)),("2023-2024",ms(2023),ms(2025)),
                  ("2025-2026",ms(2025),ms(2027))):
    m=(M[:,2]>=a_)&(M[:,2]<z_); rep(lbl,M[m,0])

print(f"\n{'='*104}\nPARAMETER PLATEAU after C9\n{'='*104}")
print(f"  {'config':<28}{'n':>8}{'win%':>8}{'EV R':>9}{'  95% CI':>22}{'PF':>7}")
for rr in (2.0,3.0,4.0,5.0):
    _,MM=collect(True,rr=rr); rep(f"target {rr}R",MM[:,0])
for imp in (1.5,2.0,3.0):
    _,MM=collect(True,imp=imp); rep(f"impulse >= {imp} ATR",MM[:,0])
_,MM=collect(True,aligned=False); rep("no trend filter",MM[:,0])
pickle.dump(M,open("/tmp/zones_final.pkl","wb"))
