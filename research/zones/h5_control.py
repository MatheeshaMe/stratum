#!/usr/bin/env python3
"""THE CONTROL THAT DECIDES IT.

1h zones + trend alignment + 3R gives pooled +0.179R, CI [+0.100,+0.258].
But the same config WITHOUT alignment gives -0.010. So alignment is carrying
most of it. The question is whether the ZONE adds anything to alignment, or
whether this is momentum with a box drawn around it.

CONTROL A  trend-aligned entries at RANDOM times, matched stop-distance
           distribution, same 3R target, same cost. If this matches, the zone
           is decoration.
CONTROL B  trend-aligned entries at a generic pullback (0.5 ATR against trend)
           with no zone requirement.
CONTROL C  zones with the impulse requirement REMOVED (base only). Isolates the
           impulse -- the part the mechanism claims creates the resting orders.
"""
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
def walk(b,A,i,side,entry,stop,rr=3.0,maxb=120,cost=COST):
    H,L,C=b['h'],b['l'],b['c']; n=len(C)
    risk=abs(entry-stop)
    if risk<=0 or risk/entry<0.0010 or risk/entry>0.10: return None
    tgt=entry+side*rr*risk
    for j in range(i+1,min(i+1+maxb,n)):
        if (L[j]<=stop) if side>0 else (H[j]>=stop): return side*(stop-entry)/risk-cost*entry/risk
        if (H[j]>=tgt) if side>0 else (L[j]<=tgt): return side*(tgt-entry)/risk-cost*entry/risk
    j=min(i+maxb,n-1)
    return side*(C[j]-entry)/risk-cost*entry/risk
def boot(R,it=4000,seed=0):
    rg=np.random.default_rng(seed)
    return tuple(np.percentile([rg.choice(R,len(R)).mean() for _ in range(it)],[2.5,97.5]))

REAL=[]; CA=[]; CB=[]; CC=[]
rng=np.random.default_rng(0)
for sym,p in SYMS:
    if not os.path.exists(p): continue
    b,A=prep(p); C=b['c']; H=b['h']; L=b['l']; n=len(C)
    Z=ZE.find_zones(b['o'],b['h'],b['l'],b['c'],b['v'],A)
    risks=[]
    for e in ZE.touch_events(Z,H,L,C,A):
        if e['touch_idx']!=0: continue
        i=e['i']
        if i<250 or i>=n-122: continue
        side=e['side']
        if np.sign(C[i]-C[i-200])!=side: continue
        entry=e['proximal']; stop=e['distal']-0.25*A[i] if side>0 else e['distal']+0.25*A[i]
        if (side>0 and L[i]>entry) or (side<0 and H[i]<entry): continue
        r=walk(b,A,i,side,entry,stop)
        if r is not None: REAL.append(r); risks.append(abs(entry-stop)/entry)
    risks=np.array(risks)
    if len(risks)<50: continue
    # CONTROL A: random time, aligned direction, matched risk distribution
    for _ in range(len(risks)*3):
        i=int(rng.integers(250,n-122)); a=A[i]
        if not np.isfinite(a) or a<=0: continue
        side=int(np.sign(C[i]-C[i-200]))
        if side==0: continue
        rk=risks[rng.integers(0,len(risks))]*C[i]
        r=walk(b,A,i,side,C[i],C[i]-side*rk)
        if r is not None: CA.append(r)
    # CONTROL B: aligned generic pullback, no zone
    for i in range(250,n-122):
        a=A[i]
        if not np.isfinite(a) or a<=0: continue
        side=int(np.sign(C[i]-C[i-200]))
        if side==0: continue
        ext=H[i-12:i].max() if side>0 else L[i-12:i].min()
        if side>0 and not (C[i]<=ext-0.5*a and C[i]>ext-1.5*a): continue
        if side<0 and not (C[i]>=ext+0.5*a and C[i]<ext+1.5*a): continue
        rk=risks[rng.integers(0,len(risks))]*C[i]
        r=walk(b,A,i,side,C[i],C[i]-side*rk)
        if r is not None: CB.append(r)
    # CONTROL C: base with NO impulse requirement
    Zc=ZE.find_zones(b['o'],b['h'],b['l'],b['c'],b['v'],A,imp_min_atr=0.3,body_ratio=0.0)
    for e in ZE.touch_events(Zc,H,L,C,A):
        if e['touch_idx']!=0: continue
        i=e['i']
        if i<250 or i>=n-122: continue
        side=e['side']
        if np.sign(C[i]-C[i-200])!=side: continue
        entry=e['proximal']; stop=e['distal']-0.25*A[i] if side>0 else e['distal']+0.25*A[i]
        if (side>0 and L[i]>entry) or (side<0 and H[i]<entry): continue
        r=walk(b,A,i,side,entry,stop)
        if r is not None: CC.append(r)

print(f"{'population':<46}{'n':>8}{'win%':>8}{'EV R':>9}{'  95% CI':>22}{'PF':>7}")
for lbl,X in (("REAL: 1h zones, aligned, 3R",REAL),
              ("CONTROL A: aligned random entry, matched risk",CA),
              ("CONTROL B: aligned generic pullback, no zone",CB),
              ("CONTROL C: base only, impulse requirement removed",CC)):
    R=np.array(X)
    if len(R)<80: print(f"{lbl:<46}{len(R):>8}  too few"); continue
    w=R>0; lo,hi=boot(R)
    print(f"{lbl:<46}{len(R):>8,}{w.mean():>8.1%}{R.mean():>+9.3f}"
          f"   [{lo:+.3f},{hi:+.3f}]{R[w].sum()/max(-R[~w].sum(),1e-9):>7.2f}")
RA=np.array(REAL); A_=np.array(CA)
diff=RA.mean()-A_.mean()
rg=np.random.default_rng(1)
d=np.array([rg.choice(RA,len(RA)).mean()-rg.choice(A_,len(A_)).mean() for _ in range(4000)])
print(f"\n  REAL minus CONTROL A: {diff:+.3f} R   95% CI "
      f"[{np.percentile(d,2.5):+.3f},{np.percentile(d,97.5):+.3f}]")
print(f"  -> {'the ZONE adds real value over alignment alone' if np.percentile(d,2.5)>0 else 'the zone adds nothing beyond trend alignment'}")
