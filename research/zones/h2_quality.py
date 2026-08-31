#!/usr/bin/env python3
"""P2 — does zone QUALITY create the asymmetry that zone EXISTENCE did not?

Touch #1 gave MFE/MAE = 1.005 against a random-band control of 1.020. So the
zone alone is nothing. The theory says quality is what separates a real zone
from a marked-up pause. Every quality axis from the brief is tested here, plus
the compound 'pro' signal: liquidity sweep INTO the zone, then rejection.

All cuts are on FIRST TOUCHES ONLY (the case the mechanism most favours) unless
stated. Baseline for every row is the random-band control on the same data.
"""
import sys, os, pickle, numpy as np
sys.path.insert(0,'research/zones'); sys.path.insert(0,'research/btc3')
import zoneengine as ZE

b,A,Z=pickle.load(open("/tmp/zones_btc.pkl","rb"))
O,H,L,C,V=b['o'],b['h'],b['l'],b['c'],b['v']; n=len(C)
TE=ZE.touch_events(Z,H,L,C,A)
FWD=48

# swing extremes for the liquidity-sweep test (causal, simple rolling)
from numpy.lib.stride_tricks import sliding_window_view
W=48
roll_lo=np.full(n,np.nan); roll_hi=np.full(n,np.nan)
roll_lo[W-1:]=sliding_window_view(L,W).min(1); roll_hi[W-1:]=sliding_window_view(H,W).max(1)
prior_lo=np.roll(roll_lo,1); prior_hi=np.roll(roll_hi,1)

rows=[]
for e in TE:
    i=e['i']
    if i<W+2 or i>=n-FWD-2: continue
    r=ZE.reaction(H,L,C,A,i,e['side'],fwd=FWD)
    if r is None: continue
    # liquidity sweep: price takes out the prior 4h extreme on this bar AND closes back
    if e['side']>0:
        sweep = (L[i] < prior_lo[i]) and (C[i] > prior_lo[i])
    else:
        sweep = (H[i] > prior_hi[i]) and (C[i] < prior_hi[i])
    # rejection candle at the touch
    body=abs(C[i]-O[i]); rng=max(H[i]-L[i],1e-12)
    wick = (min(O[i],C[i])-L[i])/rng if e['side']>0 else (H[i]-max(O[i],C[i]))/rng
    rej = wick>0.5 and body/rng<0.4
    # trend context (200-bar slope sign)
    trend = np.sign(C[i]-C[i-200]) if i>200 else 0
    rows.append((e['touch_idx'], e['side'], r['mfe'], r['mae'], r['net'],
                 e['imp_atr'], e['base_width_atr'], e['fvg_atr'], e['imp_body_ratio'],
                 e['imp_vol']/max(e['base_vol'],1e-9), float(sweep), float(rej),
                 float(trend==e['side']), i, e['base_bars']))
M=np.array(rows,dtype=float)
print(f"scored first+later touches: {len(M):,}")
F=M[M[:,0]==0]
print(f"first touches: {len(F):,}\n")

rng_=np.random.default_rng(0); ctrl=[]
widths=np.array([z['base_width_atr'] for z in Z])
for _ in range(20000):
    i=int(rng_.integers(60,n-FWD-2)); a=A[i]
    if not np.isfinite(a) or a<=0: continue
    s=1 if rng_.random()<0.5 else -1
    r=ZE.reaction(H,L,C,A,i,s,fwd=FWD)
    if r: ctrl.append((r['mfe'],r['mae'],r['net']))
CT=np.array(ctrl)
def bmr(mfe,mae,it=3000,seed=0):
    rg=np.random.default_rng(seed); N=len(mfe); o=np.empty(it)
    for k in range(it):
        s=rg.integers(0,N,N); o[k]=np.median(mfe[s])/max(np.median(mae[s]),1e-9)
    return np.percentile(o,2.5),np.percentile(o,97.5)
BASE=np.median(CT[:,0])/np.median(CT[:,1])
print(f"CONTROL random band  n={len(CT):,}  MFE/MAE = {BASE:.3f}  "
      f"medNet {np.median(CT[:,2]):+.3f}\n")
print(f"{'first-touch cut':<40}{'n':>7}{'MFE/MAE':>10}{'  95% CI':>20}"
      f"{'vs base':>9}{'medNet':>9}")
def cut(lbl,m):
    if m.sum()<200: print(f"{lbl:<40}{int(m.sum()):>7}  too few"); return
    mfe,mae,net=F[m,2],F[m,3],F[m,4]
    ratio=np.median(mfe)/max(np.median(mae),1e-9)
    lo,hi=bmr(mfe,mae)
    sig="*" if (lo>BASE or hi<BASE) else " "
    print(f"{lbl:<40}{int(m.sum()):>7}{ratio:>10.3f}   [{lo:.3f},{hi:.3f}]"
          f"{ratio-BASE:>+9.3f}{sig}{np.median(net):>+9.3f}")
allm=np.ones(len(F),bool)
cut("ALL first touches",allm)
print()
q=lambda col,p: np.nanquantile(F[:,col],p)
cut("impulse >= 3 ATR",           F[:,5]>=3.0)
cut("impulse >= 4 ATR",           F[:,5]>=4.0)
cut("impulse top decile",         F[:,5]>=q(5,0.90))
cut("FVG present",                F[:,7]>0)
cut("FVG >= 0.5 ATR",             F[:,7]>=0.5)
cut("impulse body ratio >= 0.75", F[:,8]>=0.75)
cut("impulse volume >= 2x base",  F[:,9]>=2.0)
print()
cut("tight base (<0.5 ATR)",      F[:,6]<0.5)
cut("wide base (>1.0 ATR)",       F[:,6]>1.0)
cut("single-bar base",            F[:,14]==1)
print()
cut("trend-aligned (continuation)",F[:,12]>0.5)
cut("counter-trend",              F[:,12]<0.5)
print()
cut("LIQUIDITY SWEEP into zone",  F[:,10]>0.5)
cut("rejection candle at touch",  F[:,11]>0.5)
cut("SWEEP + rejection",          (F[:,10]>0.5)&(F[:,11]>0.5))
cut("SWEEP + rejection + aligned",(F[:,10]>0.5)&(F[:,11]>0.5)&(F[:,12]>0.5))
print()
cut("PRO STACK: fresh+imp>=3+FVG+sweep",
    (F[:,5]>=3.0)&(F[:,7]>0)&(F[:,10]>0.5))
cut("PRO STACK + rejection",
    (F[:,5]>=3.0)&(F[:,7]>0)&(F[:,10]>0.5)&(F[:,11]>0.5))
print(f"\n  * = 95% CI on the ratio excludes the random-band baseline ({BASE:.3f})")
pickle.dump((F,CT,BASE),open("/tmp/zones_h2.pkl","wb"))
