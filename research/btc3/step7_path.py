#!/usr/bin/env python3
"""Step 7 -- normalised event timeline and archetype classification."""
import sys, os, pickle, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import events as E
T,O,H,L,C,V,N=E.load("data/spot/BTCUSDT-1m.pkl")
n=len(C); DS=pickle.load(open("/tmp/btc3_dataset.pkl","rb"))
IND=pickle.load(open("/tmp/btc3_ind.pkl","rb"))

MARKS=[("T-24h",-1440),("T-12h",-720),("T-4h",-240),("T-1h",-60),("T-30m",-30),
       ("T-15m",-15),("T0",0),("T+15m",15),("T+30m",30),("T+1h",60),("T+4h",240),
       ("T+12h",720),("T+24h",1440),("T+48h",2880),("T+7d",10080)]

for key in [("1h","C2C"),("24h","C2C")]:
    d=DS[key]; i0=d['i0']
    ok=(i0>10081)&(i0<n-10081)
    i0=i0[ok]
    print(f"\n{'='*104}")
    print(f"NORMALISED PATH around a +3% {key[0]} event  (price indexed to 100 at T0)  n={len(i0)}")
    print(f"{'='*104}")
    print(f"{'point':<8}{'median':>9}{'mean':>9}{'p10':>9}{'p25':>9}{'p75':>9}{'p90':>9}"
          f"{'  %above T0':>13}")
    for lab,off in MARKS:
        j=np.clip(i0+off,0,n-1)
        good=(T[j]-T[i0])==off*60000
        x=np.where(good, C[j]/C[i0]*100, np.nan); x=x[np.isfinite(x)]
        if len(x)<20: continue
        print(f"{lab:<8}{np.median(x):>9.2f}{x.mean():>9.2f}{np.percentile(x,10):>9.2f}"
              f"{np.percentile(x,25):>9.2f}{np.percentile(x,75):>9.2f}"
              f"{np.percentile(x,90):>9.2f}{(x>100).mean():>12.1%}")

# ---------------------------------------------------------------- archetypes
print(f"\n\n{'='*112}\nARCHETYPES of the 1h +3% event (rules fixed a priori, not fitted)\n{'='*112}")
d=DS[("1h","C2C")]
pre24=d['pre_ret_24h']; pre4=d['pre_ret_4h']; dist=d['pre_dist_24h_high']
brk=d['dur_broke_24h_high']; imp=d['dur_impulses']; dd=d['dur_maxdd_pct']
vol=d['dur_vol_vs_normal']; atr=d['pre_atr_pct']
cls=np.full(len(pre24),"unclassified",dtype=object)
cls[(pre24<-3)&(dist<-5)]              = "recovery / V-bounce"
cls[(pre24>=-3)&(brk>0.5)]             = "breakout to new 24h high"
cls[(pre24>=-3)&(brk<0.5)&(dd>-0.5)]   = "grind (no pullback)"
cls[(vol>3)&(imp<=8)]                  = "vertical spike"
uniq,cnt=np.unique(cls,return_counts=True)
order=np.argsort(-cnt)
print(f"{'archetype':<28}{'n':>6}{'share':>8}{'pre24h%':>10}{'maxDD%':>9}{'vol x':>8}"
      f"{'fwd 4h%':>10}{'fwd 24h%':>10}{'P(up 24h)':>11}{'full rev 7d':>13}")
for k in order:
    a=uniq[k]; m=cls==a
    if m.sum()<10: continue
    f4=d['fwd_4h'][m]; f24=d['fwd_24h'][m]; rv=d['gave_back_full_7d'][m]
    print(f"{a:<28}{m.sum():>6}{m.mean():>8.1%}{np.nanmedian(pre24[m]):>+10.2f}"
          f"{np.nanmedian(dd[m]):>9.2f}{np.nanmedian(vol[m]):>8.2f}"
          f"{np.nanmedian(f4):>+10.2f}{np.nanmedian(f24):>+10.2f}"
          f"{np.nanmean(f24>0):>11.1%}{np.nanmean(rv):>13.1%}")

print(f"\n\nSEGMENTATION of the 1h +3% event")
print(f"{'segment':<34}{'n':>6}{'fwd 4h med%':>13}{'fwd 24h med%':>14}"
      f"{'P(up 24h)':>11}{'P(+3% more 24h)':>17}{'P(full rev 7d)':>16}")
def seg(lbl,m):
    if m.sum()<15: return
    print(f"{lbl:<34}{m.sum():>6}{np.nanmedian(d['fwd_4h'][m]):>+13.2f}"
          f"{np.nanmedian(d['fwd_24h'][m]):>+14.2f}{np.nanmean(d['fwd_24h'][m]>0):>11.1%}"
          f"{np.nanmean(d['mfe_24h'][m]>=3):>17.1%}{np.nanmean(d['gave_back_full_7d'][m]):>16.1%}")
seg("ALL", np.ones(len(pre24),bool))
seg("above EMA200(h) at T_ref", d['pre_above_ema200h']>0.5)
seg("below EMA200(h) at T_ref", d['pre_above_ema200h']<0.5)
seg("bull regime (30d ret > +10%)", d['regime_ret30d']>10)
seg("bear regime (30d ret < -10%)", d['regime_ret30d']<-10)
seg("sideways (|30d ret| <= 10%)", np.abs(d['regime_ret30d'])<=10)
seg("high vol (ATR pct > median)", atr>np.nanmedian(atr))
seg("low vol (ATR pct <= median)", atr<=np.nanmedian(atr))
seg("broke 24h high during move", brk>0.5)
seg("did NOT break 24h high", brk<0.5)
seg("deep prior drawdown (<-5%)", dist<-5)
seg("shallow prior drawdown (>=-5%)", dist>=-5)
hr=d['pre_hour_utc']
seg("Asia 00-08 UTC", (hr>=0)&(hr<8))
seg("Europe 08-13 UTC", (hr>=8)&(hr<13))
seg("US 13-21 UTC", (hr>=13)&(hr<21))
