#!/usr/bin/env python3
"""Step 4 -- what PRECEDES a +3% move, and what the move itself looks like."""
import sys, os, pickle, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import events as E

T,O,H,L,C,V,N = E.load("data/spot/BTCUSDT-1m.pkl")
n=len(C); IND=pickle.load(open("/tmp/btc3_ind.pkl","rb"))
DS=pickle.load(open("/tmp/btc3_dataset.pkl","rb"))

# matched baseline: random reference points, same feature construction
rng=np.random.default_rng(1)
BI=rng.choice(np.arange(10081,n-10081), 20000, replace=False)
def feats_at(ref):
    d={}
    for lab,k in (("5m",5),("15m",15),("30m",30),("1h",60),("4h",240),
                  ("12h",720),("24h",1440)):
        d[f'pre_ret_{lab}']=(C[ref]/C[np.maximum(ref-k,0)]-1)*100
    d['pre_atr_pct']=IND['atr14'][ref]/C[ref]*100
    d['pre_rsi']=IND['rsi14'][ref]; d['pre_mfi']=IND['mfi14'][ref]
    d['pre_vol_ratio']=(IND['vsum20'][ref]/20)/(IND['vsum1440'][ref]/1440)
    d['pre_vol_accel']=(IND['vsum20'][ref]/20)/np.where(IND['vsum100'][ref]/100==0,np.nan,IND['vsum100'][ref]/100)
    for lab in ('ema9h','ema20h','ema200h'):
        d[f'pre_{lab}_dist']=(C[ref]/IND[lab][ref]-1)*100
    d['pre_above_ema200h']=(C[ref]>IND['ema200h'][ref]).astype(float)
    d['pre_dist_24h_high']=(C[ref]/IND['hh1440'][ref]-1)*100
    d['pre_dist_24h_low']=(C[ref]/IND['ll1440'][ref]-1)*100
    d['pre_dist_7d_high']=(C[ref]/IND['hh10080'][ref]-1)*100
    rng24=(IND['hh1440'][ref]-IND['ll1440'][ref])/C[ref]*100
    d['pre_range24_pct']=rng24
    d['pre_compression']=rng24/np.where(d['pre_atr_pct']==0,np.nan,d['pre_atr_pct'])
    k30=43200
    d['regime_ret30d']=np.where(ref>k30,(C[ref]/C[np.maximum(ref-k30,0)]-1)*100,np.nan)
    return d
BF=feats_at(BI)

def cohen(a,b):
    a=a[np.isfinite(a)]; b=b[np.isfinite(b)]
    if len(a)<20 or len(b)<20: return np.nan,np.nan,np.nan
    s=np.sqrt(((len(a)-1)*a.var(ddof=1)+(len(b)-1)*b.var(ddof=1))/(len(a)+len(b)-2))
    dcoh=(a.mean()-b.mean())/s if s>0 else np.nan
    # bootstrap CI on the mean difference
    rg=np.random.default_rng(0); m=np.empty(2000)
    for i in range(2000):
        m[i]=rg.choice(a,len(a)).mean()-rg.choice(b,len(b)).mean()
    return dcoh, np.percentile(m,2.5), np.percentile(m,97.5)

for key in [("1h","C2C"),("24h","C2C")]:
    d=DS[key]; nev=len(d['t0'])
    print(f"\n{'='*116}")
    print(f"BEFORE a +3% move in {key[0]}  -- state at T_ref (BEFORE the move begins)  n={nev}")
    print(f"vs 20,000 random reference points from the same 9-year sample")
    print(f"{'='*116}")
    print(f"{'feature':<26}{'event mean':>12}{'baseline':>11}{'diff':>10}"
          f"{'Cohen d':>10}{'  95% CI on diff':>24}")
    feats=[f for f in BF if f in d]
    res=[]
    for f in feats:
        a=d[f]; b=BF[f]
        dc,lo,hi=cohen(a,b)
        if not np.isfinite(dc): continue
        res.append((abs(dc),dc,lo,hi,f,np.nanmean(a),np.nanmean(b)))
    res.sort(reverse=True)
    for ad,dc,lo,hi,f,am,bm in res:
        sig="*" if (lo>0 or hi<0) else " "
        big="  <<<" if ad>=0.30 else ""
        print(f"{f:<26}{am:>+12.3f}{bm:>+11.3f}{am-bm:>+10.3f}{dc:>+10.2f}{sig}"
              f"  [{lo:+.3f},{hi:+.3f}]{big}")
    print("  Cohen d: 0.2 small, 0.5 medium, 0.8 large.  * = 95% CI on the difference excludes 0")

print(f"\n\n{'='*116}\nDURING the move\n{'='*116}")
print(f"{'window':<8}{'n':>6}{'maxDD% (med)':>14}{'impulses (med)':>16}"
      f"{'frac in last 20%':>18}{'vol vs normal':>15}{'broke 24h high':>16}")
for key in [("5m","C2C"),("15m","C2C"),("1h","C2C"),("4h","C2C"),("24h","C2C")]:
    d=DS[key]
    print(f"{key[0]:<8}{len(d['t0']):>6}{np.nanmedian(d['dur_maxdd_pct']):>14.2f}"
          f"{np.nanmedian(d['dur_impulses']):>16.0f}"
          f"{np.nanmedian(d['dur_frac_in_last_20pct']):>18.2f}"
          f"{np.nanmedian(d['dur_vol_vs_normal']):>15.2f}"
          f"{np.nanmean(d['dur_broke_24h_high']):>16.1%}")
