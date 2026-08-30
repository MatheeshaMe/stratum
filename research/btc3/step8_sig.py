#!/usr/bin/env python3
"""Step 8 -- significance and out-of-sample check on the notable segments."""
import sys, os, pickle, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
DS=pickle.load(open("/tmp/btc3_dataset.pkl","rb"))
d=DS[("1h","C2C")]
CUT=np.datetime64('2021-01-01').astype('datetime64[ms]').astype(np.int64)
early=d['t0']<CUT; late=d['t0']>=CUT
def boot(x,iters=5000,seed=0):
    x=x[np.isfinite(x)]
    if len(x)<15: return (np.nan,np.nan,np.nan)
    rg=np.random.default_rng(seed); m=np.array([rg.choice(x,len(x)).mean() for _ in range(iters)])
    return x.mean(),np.percentile(m,2.5),np.percentile(m,97.5)
hr=d['pre_hour_utc']
print("Segment robustness on fwd_24h (%), 1h +3% events\n")
print(f"{'segment':<28}{'n':>5}{'mean':>8}{'  95% CI':>20}"
      f"{'  2017-19 n/mean':>20}{'  2023-26 n/mean':>20}")
SEG=[("ALL",np.ones(len(hr),bool)),
     ("Asia 00-08 UTC",(hr>=0)&(hr<8)),
     ("Europe 08-13 UTC",(hr>=8)&(hr<13)),
     ("US 13-21 UTC",(hr>=13)&(hr<21)),
     ("21-24 UTC",(hr>=21)),
     ("broke 24h high",d['dur_broke_24h_high']>0.5),
     ("did not break",d['dur_broke_24h_high']<0.5),
     ("bull regime",d['regime_ret30d']>10),
     ("bear regime",d['regime_ret30d']<-10),
     ("sideways",np.abs(d['regime_ret30d'])<=10)]
for lbl,m in SEG:
    x=d['fwd_24h'][m]; mu,lo,hi=boot(x)
    e=d['fwd_24h'][m&early]; l=d['fwd_24h'][m&late]
    e=e[np.isfinite(e)]; l=l[np.isfinite(l)]
    sig="*" if (lo>0 or hi<0) else " "
    print(f"{lbl:<28}{int(m.sum()):>5}{mu:>+8.3f}{sig} [{lo:+.3f},{hi:+.3f}]"
          f"{len(e):>8}/{e.mean() if len(e) else np.nan:>+7.2f}"
          f"{len(l):>8}/{l.mean() if len(l) else np.nan:>+7.2f}")
print(f"\n  segments tested: {len(SEG)-1}, expected significant by chance ~{0.05*(len(SEG)-1):.1f}")
print("\nP(up at 24h) with Wilson CI")
def wil(k,n):
    if n==0: return (np.nan,np.nan)
    p=k/n; z=1.96; dd=1+z*z/n
    c=(p+z*z/(2*n))/dd; h=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/dd
    return c-h,c+h
for lbl,m in SEG:
    x=d['fwd_24h'][m]; x=x[np.isfinite(x)]
    if len(x)<15: continue
    k=int((x>0).sum()); lo,hi=wil(k,len(x))
    sig="*" if lo>0.5 or hi<0.5 else " "
    print(f"  {lbl:<28}{k}/{len(x)} = {k/len(x):.1%}{sig}  [{lo:.1%},{hi:.1%}]")
