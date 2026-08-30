#!/usr/bin/env python3
"""Step 3 -- what happens AFTER +3%, against the unconditional baseline."""
import sys, os, pickle, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import events as E

T,O,H,L,C,V,N = E.load("data/spot/BTCUSDT-1m.pkl")
n=len(C)
DS=pickle.load(open("/tmp/btc3_dataset.pkl","rb"))
HORIZ=[("5m",5),("15m",15),("30m",30),("1h",60),("2h",120),("4h",240),
       ("8h",480),("12h",720),("24h",1440),("48h",2880),("72h",4320),("7d",10080)]

rng=np.random.default_rng(0)
BASE_I=rng.choice(np.arange(10081,n-10081), 40000, replace=False)
def base_fwd(k):
    j=np.minimum(BASE_I+k,n-1); ok=(T[j]-T[BASE_I])==k*60000
    return np.where(ok,(C[j]/C[BASE_I]-1)*100,np.nan)
BASE={lab:base_fwd(k) for lab,k in HORIZ}

def block_ci(x, block=8, iters=4000, seed=0):
    x=x[np.isfinite(x)]
    if len(x)<20: return (np.nan,np.nan)
    rg=np.random.default_rng(seed); nb=int(np.ceil(len(x)/block)); m=np.empty(iters)
    for k in range(iters):
        st=rg.integers(0,len(x),nb)
        s=np.concatenate([np.take(x,np.arange(i,i+block),mode='wrap') for i in st])[:len(x)]
        m[k]=s.mean()
    return np.percentile(m,2.5),np.percentile(m,97.5)

def q(x,p): 
    x=x[np.isfinite(x)]; return np.percentile(x,p) if len(x) else np.nan

for key in [("1h","C2C"),("4h","C2C"),("24h","C2C")]:
    d=DS[key]; nev=len(d['t0'])
    print(f"\n{'='*118}")
    print(f"AFTER a +3% move in {key[0]} (close-to-close, >=24h apart)   n={nev}")
    print(f"{'='*118}")
    print(f"{'horizon':<8}{'n':>6}{'mean%':>9}{'median%':>9}{'sd':>8}{'P(up)':>8}"
          f"{'p25':>8}{'p75':>8}{'p90':>8}{'base mean':>11}{'excess':>9}{'  95% CI excess':>20}")
    for lab,k in HORIZ:
        x=d[f'fwd_{lab}']; xf=x[np.isfinite(x)]
        if len(xf)<20: continue
        b=BASE[lab]; bm=np.nanmean(b)
        ex=xf.mean()-bm
        lo,hi=block_ci(x-bm)
        sig="*" if (lo>0 or hi<0) else " "
        print(f"{lab:<8}{len(xf):>6}{xf.mean():>+9.3f}{np.median(xf):>+9.3f}{xf.std():>8.3f}"
              f"{(xf>0).mean():>8.1%}{q(x,25):>+8.2f}{q(x,75):>+8.2f}{q(x,90):>+8.2f}"
              f"{bm:>+11.3f}{ex:>+9.3f}{sig}  [{lo:+.3f},{hi:+.3f}]")

    print(f"\n  CONTINUATION vs REVERSAL after the +3% (from T0)")
    print(f"  {'horizon':<8}{'+1%':>8}{'+2%':>8}{'+3%':>8}{'+5%':>8}{'+10%':>8}"
          f"{'-1%':>8}{'-2%':>8}{'-3%':>8}{'back to start':>15}{'full rev':>10}")
    for lab,k in [("1h",60),("4h",240),("24h",1440),("48h",2880),("7d",10080)]:
        mfe=d[f'mfe_{lab}']; mae=d[f'mae_{lab}']
        f=np.isfinite(mfe)&np.isfinite(mae)
        if f.sum()<20: continue
        row=f"  {lab:<8}"
        for th in (1,2,3,5,10): row+=f"{(mfe[f]>=th).mean():>8.1%}"
        for th in (1,2,3):      row+=f"{(mae[f]<=-th).mean():>8.1%}"
        # back to the pre-move price = -move_pct/(1+move) approx; use exact ref price
        back=(d['px_ref'][f]/d['px_0'][f]-1)*100
        row+=f"{(mae[f]<=back).mean():>15.1%}"
        row+=f"{(mae[f]<=back).mean():>10.1%}"
        print(row)
    print("  ('back to start' = price traded down to the pre-move reference price)")

print(f"\n\n{'='*118}\nTIME SPLIT -- does the AFTER behaviour replicate across eras?")
print(f"  discovery 2017-08..2019-12   |   validation 2023-01..2026-07 "
      f"(2020-2022 sealed, excluded)\n{'='*118}")
CUT=np.datetime64('2021-01-01').astype('datetime64[ms]').astype(np.int64)
print(f"{'window':<8}{'era':<14}{'n':>6}" + "".join(f"{l:>11}" for l,_ in
      [("1h",0),("4h",0),("24h",0),("7d",0)]))
for key in [("1h","C2C"),("4h","C2C"),("24h","C2C")]:
    d=DS[key]
    for era,m in (("2017-2019",d['t0']<CUT),("2023-2026",d['t0']>=CUT)):
        row=f"{key[0]:<8}{era:<14}{m.sum():>6}"
        for lab in ("1h","4h","24h","7d"):
            x=d[f'fwd_{lab}'][m]; xf=x[np.isfinite(x)]
            row+=f"{xf.mean():>+11.3f}" if len(xf)>15 else f"{'-':>11}"
        print(row)
    print()
