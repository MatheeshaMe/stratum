#!/usr/bin/env python3
"""P1 — FRESHNESS DECAY. The experiment that discriminates S/D from S/R.

S/D theory: resting orders are CONSUMED. reaction(1st) > reaction(2nd) > ...
S/R theory: repeated holds CONFIRM a level. Later touches are no weaker.

These predict opposite signs, so the touch-count profile is a real test.

Two controls, because "zones react" is meaningless without them:
  RANDOM BAND    same width, random price and time, tracked identically.
                 Isolates 'is a price band special at all'.
  BASE-NO-IMPULSE consolidations of the same shape that did NOT produce an
                 impulse. Isolates the IMPULSE — the part the mechanism claims
                 matters — from the consolidation.
"""
import sys, os, pickle, numpy as np
sys.path.insert(0,'research/zones'); sys.path.insert(0,'research/btc3')
import zoneengine as ZE, events as E

b,A,Z=pickle.load(open("/tmp/zones_btc.pkl","rb"))
O,H,L,C,V=b['o'],b['h'],b['l'],b['c'],b['v']
n=len(C)
TE=ZE.touch_events(Z,H,L,C,A)
print(f"zones {len(Z):,}  touch events {len(TE):,}")
FWD=48

def collect(events):
    rows=[]
    for e in events:
        r=ZE.reaction(H,L,C,A,e['i'],e['side'],fwd=FWD)
        if r is None: continue
        rows.append((e['touch_idx'],e['side'],r['mfe'],r['mae'],r['ratio'],r['net'],
                     e.get('imp_atr',np.nan),e.get('base_width_atr',np.nan),
                     e.get('fvg_atr',np.nan),e['i']))
    return np.array(rows,dtype=float) if rows else np.zeros((0,10))
R=collect(TE)
print(f"scored touches: {len(R):,}\n")

def boot_med_ratio(mfe,mae,it=3000,seed=0):
    rg=np.random.default_rng(seed); n_=len(mfe); out=np.empty(it)
    for k in range(it):
        s=rg.integers(0,n_,n_)
        out[k]=np.median(mfe[s])/max(np.median(mae[s]),1e-9)
    return np.percentile(out,2.5),np.percentile(out,97.5)
def boot_mean(x,it=3000,seed=0):
    rg=np.random.default_rng(seed)
    return tuple(np.percentile([rg.choice(x,len(x)).mean() for _ in range(it)],[2.5,97.5]))

# ---------- controls ----------
rng=np.random.default_rng(0)
ctrl=[]
widths=np.array([z['base_width_atr'] for z in Z])
for _ in range(len(Z)):
    i=int(rng.integers(60,n-FWD-2)); a=A[i]
    if not np.isfinite(a) or a<=0: continue
    w=widths[rng.integers(0,len(widths))]*a
    side=1 if rng.random()<0.5 else -1
    ctrl.append(dict(i=i,side=side,touch_idx=0))
RC=collect(ctrl)

# bases that did NOT produce an impulse
body=np.abs(C-O); rngb=np.maximum(H-L,1e-12); br=body/rngb
noimp=[]
for i in range(30,n-FWD-2,7):
    a=A[i]
    if not np.isfinite(a) or a<=0: continue
    bs=slice(i-2,i)
    if br[bs].mean()>0.5: continue
    if (H[bs].max()-L[bs].min())>1.0*a: continue
    j=min(i+2,n-1)
    if abs(C[j]-O[i])>=2.0*a: continue          # an impulse DID follow -> skip
    noimp.append(dict(i=i,side=(1 if rng.random()<0.5 else -1),touch_idx=0))
RN=collect(noimp)

print("="*104)
print(f"P1  FRESHNESS DECAY — reaction by touch index (forward {FWD} bars = {FWD*5/60:.0f}h)")
print("="*104)
print(f"{'population':<34}{'n':>8}{'medMFE':>9}{'medMAE':>9}{'MFE/MAE':>10}"
      f"{'  95% CI ratio':>22}{'medNet':>9}{'P(MFE>2A)':>11}")
def row(lbl,M):
    if len(M)<100: print(f"{lbl:<34}{len(M):>8}  too few"); return None
    mfe,mae,net=M[:,2],M[:,3],M[:,5]
    lo,hi=boot_med_ratio(mfe,mae)
    print(f"{lbl:<34}{len(M):>8,}{np.median(mfe):>9.2f}{np.median(mae):>9.2f}"
          f"{np.median(mfe)/max(np.median(mae),1e-9):>10.3f}   [{lo:.3f},{hi:.3f}]"
          f"{np.median(net):>+9.3f}{(mfe>2).mean():>11.1%}")
    return (np.median(mfe)/max(np.median(mae),1e-9),lo,hi)
row("CONTROL random band",RC)
row("CONTROL base, NO impulse",RN)
print()
prof=[]
for t in range(0,6):
    m=R[R[:,0]==t] if t<5 else R[R[:,0]>=5]
    lbl=f"ZONE touch #{t+1}" if t<5 else "ZONE touch #6+"
    r=row(lbl,m)
    if r: prof.append((t,r[0],len(m)))
print()
row("ZONE all touches pooled",R)
print()
print("  Mechanism predicts a DECLINING ratio across touch numbers.")
print("  Support/resistance logic predicts flat or rising.")
if len(prof)>=4:
    ts=np.array([p[0] for p in prof]); rs=np.array([p[1] for p in prof])
    sl=np.polyfit(ts,rs,1)[0]
    print(f"  observed slope across touch #1..#{len(prof)}: {sl:+.4f} per touch")
pickle.dump((R,RC,RN),open("/tmp/zones_h1.pkl","wb"))
