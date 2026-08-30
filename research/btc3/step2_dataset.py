#!/usr/bin/env python3
"""Step 2 -- build the structured event dataset: before / during / after."""
import sys, os, pickle, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import events as E
from numpy.lib.stride_tricks import sliding_window_view

T,O,H,L,C,V,N = E.load("data/spot/BTCUSDT-1m.pkl")
n=len(C)
CACHE="/tmp/btc3_ind.pkl"
if os.path.exists(CACHE):
    IND=pickle.load(open(CACHE,"rb"))
else:
    print("computing indicators over 3.1M bars ...", flush=True)
    IND={}
    IND['atr14']=E.atr(H,L,C,14)
    IND['rsi14']=E.rsi(C,14)
    IND['mfi14']=E.mfi(H,L,C,V,14)
    for p in (9,20,200):
        IND[f'ema{p}']=E.ema(C,p)
    # hourly-scale versions: EMA on 1m with 60x periods
    for p,lab in ((9*60,'ema9h'),(20*60,'ema20h'),(200*60,'ema200h')):
        IND[lab]=E.ema(C,p)
    def rsum(x,w):
        o=np.full(n,np.nan)
        if n>=w: o[w-1:]=sliding_window_view(x,w).sum(1)
        return o
    for w in (20,100,1440):
        IND[f'vsum{w}']=rsum(V,w)
    for w in (60,240,1440,10080):
        IND[f'hh{w}']=E.rolling_max(H,w); IND[f'll{w}']=E.rolling_min(L,w)
    pickle.dump(IND,open(CACHE,"wb"))
print("indicators ready", flush=True)

def ret(i,k):
    j=np.maximum(i-k,0); return C[i]/C[j]-1.0
def valid(i,k): return (T[i]-T[np.maximum(i-k,0)])==k*60000

HORIZ=[("5m",5),("15m",15),("30m",30),("1h",60),("2h",120),("4h",240),
       ("8h",480),("12h",720),("24h",1440),("48h",2880),("72h",4320),("7d",10080)]

def build(idx, W):
    """idx = T0 indices. Returns a dict of arrays, one row per event."""
    idx=idx[(idx>10080+W)&(idx<n-10081)]
    ref=idx-W
    d={}
    d['t0']=T[idx]; d['i0']=idx; d['iref']=ref
    d['px_ref']=C[ref]; d['px_0']=C[idx]
    d['move_pct']=(C[idx]/C[ref]-1)*100
    # ---------- BEFORE (measured AT T_ref, strictly before the move) ----------
    for lab,k in (("5m",5),("15m",15),("30m",30),("1h",60),("4h",240),
                  ("12h",720),("24h",1440)):
        d[f'pre_ret_{lab}']=ret(ref,k)*100
    a=IND['atr14'][ref]; d['pre_atr_pct']=a/C[ref]*100
    d['pre_rsi']=IND['rsi14'][ref]; d['pre_mfi']=IND['mfi14'][ref]
    d['pre_vol_ratio']=(IND['vsum20'][ref]/20)/(IND['vsum1440'][ref]/1440)
    d['pre_vol_accel']=(IND['vsum20'][ref]/20)/np.where(IND['vsum100'][ref]/100==0,np.nan,
                                                        IND['vsum100'][ref]/100)
    for lab in ('ema9h','ema20h','ema200h'):
        d[f'pre_{lab}_dist']=(C[ref]/IND[lab][ref]-1)*100
    d['pre_above_ema200h']=(C[ref]>IND['ema200h'][ref]).astype(float)
    d['pre_dist_24h_high']=(C[ref]/IND['hh1440'][ref]-1)*100
    d['pre_dist_24h_low']=(C[ref]/IND['ll1440'][ref]-1)*100
    d['pre_dist_7d_high']=(C[ref]/IND['hh10080'][ref]-1)*100
    rng24=(IND['hh1440'][ref]-IND['ll1440'][ref])/C[ref]*100
    d['pre_range24_pct']=rng24
    d['pre_compression']=rng24/np.where(d['pre_atr_pct']==0,np.nan,d['pre_atr_pct'])
    # consecutive candle runs on 15m
    up=(C>np.roll(C,15)); run=np.zeros(n,dtype=np.int32)
    d['pre_consec_up15']=np.array([sum(1 for k in range(1,13)
        if C[max(r-15*k,0)]>C[max(r-15*(k+1),0)]) for r in ref])
    # drawdown from the trailing 24h high, at T_ref
    d['pre_dd_from_24h_high']=(C[ref]/IND['hh1440'][ref]-1)*100
    hr=((T[ref]//3600000)%24); d['pre_hour_utc']=hr
    # regime: 30d trailing return and 30d realised vol
    k30=43200
    d['regime_ret30d']=np.where(ref>k30,(C[ref]/C[np.maximum(ref-k30,0)]-1)*100,np.nan)
    d['regime_vol']=np.array([np.std(np.diff(np.log(C[max(r-k30,0):r:60]))) *np.sqrt(24*365)*100
                              if r>k30 else np.nan for r in ref])
    # ---------- DURING (T_ref -> T0) ----------
    mdd=np.empty(len(idx)); nimp=np.empty(len(idx)); frac_last=np.empty(len(idx))
    vdur=np.empty(len(idx)); brk=np.empty(len(idx))
    for j,(r,i) in enumerate(zip(ref,idx)):
        seg=C[r:i+1]
        pk=np.maximum.accumulate(seg); mdd[j]=((seg-pk)/pk).min()*100
        dd=np.diff(seg); nimp[j]=int(np.sum((dd[:-1]<=0)&(dd[1:]>0)))+1
        q=max(1,len(seg)//5); frac_last[j]=(seg[-1]-seg[-q])/(seg[-1]-seg[0]+1e-12)
        vdur[j]=V[r:i+1].sum()/max(W,1)
        brk[j]=1.0 if H[r:i+1].max()>=IND['hh1440'][r] else 0.0
    d['dur_maxdd_pct']=mdd; d['dur_impulses']=nimp
    d['dur_frac_in_last_20pct']=frac_last
    d['dur_vol_vs_normal']=vdur/np.where(IND['vsum1440'][ref]/1440==0,np.nan,
                                          IND['vsum1440'][ref]/1440)
    d['dur_broke_24h_high']=brk
    # ---------- AFTER (from T0) ----------
    for lab,k in HORIZ:
        j=np.minimum(idx+k,n-1)
        ok=(T[j]-T[idx])==k*60000
        r_=np.where(ok,(C[j]/C[idx]-1)*100,np.nan)
        d[f'fwd_{lab}']=r_
        # MFE / MAE within the horizon
        mfe=np.empty(len(idx)); mae=np.empty(len(idx))
        for m,(i,jj) in enumerate(zip(idx,j)):
            mfe[m]=(H[i+1:jj+1].max()/C[i]-1)*100 if jj>i else np.nan
            mae[m]=(L[i+1:jj+1].min()/C[i]-1)*100 if jj>i else np.nan
        d[f'mfe_{lab}']=np.where(ok,mfe,np.nan); d[f'mae_{lab}']=np.where(ok,mae,np.nan)
    # retrace to the pre-move reference price, within 24h and 7d
    for lab,k in (("24h",1440),("7d",10080)):
        j=np.minimum(idx+k,n-1)
        back=np.array([ (L[i+1:jj+1].min()<=C[r]) if jj>i else False
                        for i,jj,r in zip(idx,j,ref)])
        d[f'gave_back_full_{lab}']=back.astype(float)
    return d

EV=pickle.load(open("/tmp/btc3_events.pkl","rb"))
OUT={}
for key in [("1h","C2C"),("4h","C2C"),("24h","C2C"),("15m","C2C"),("5m","C2C"),("1h","L2H")]:
    W,raw,d1,d24 = EV[key]
    ds = build(d24, W)
    OUT[key]=ds
    print(f"{key}  W={W}m  events={len(ds['t0']):,}", flush=True)
pickle.dump(OUT, open("/tmp/btc3_dataset.pkl","wb"))
print("dataset written")
