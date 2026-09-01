#!/usr/bin/env python3
"""Do the surviving observations replicate? Split-era + cross-asset.

Discovery here was ALL of BTC, so the honest validation is (a) a chronological
split and (b) four assets the observations were never tuned on.
"""
import sys, os, pickle, numpy as np
sys.path.insert(0,'research/interp'); sys.path.insert(0,'research/btc3')
import observe as OB, events as E
from divergence import forward_stats, block_ci, FWD

WATCH=["4h.accept_hi","4h.sweep_lo","1h.seq.sweep_accept_up","4h.seq.sweep_accept_up",
       "4h.seq.sweep_reclaim_disp_up","1h.seq.sweep_reclaim_disp_up",
       "5m.seq.compress_expand_up","5m.seq.compress_expand_dn","5m.accept_hi"]

def measure(T,O,H,L,C,V,label,tsplit=None):
    bb,al,_,_=OB.build(T,O,H,L,C,V,base_tf="5m")
    A=al["5m.atr"]
    fret,frange,ttr=forward_stats(bb,A)
    ok=np.isfinite(fret)&np.isfinite(frange)&np.isfinite(A)&(A>0); ok[:2000]=False
    out={}
    windows=[("all",ok)]
    if tsplit is not None:
        windows=[("early",ok&(bb['t']<tsplit)),("late",ok&(bb['t']>=tsplit))]
    for wn,wm in windows:
        base_mu=fret[wm].mean(); base_rng=np.median(frange[wm]); base_ttr=np.median(ttr[wm])
        for k in WATCH:
            if k not in al: continue
            m=wm&(al[k]==1)
            if m.sum()<300: continue
            lo,hi=block_ci(fret[m]-base_mu)
            out[(label,wn,k)]=dict(n=int(m.sum()),d_mu=fret[m].mean()-base_mu,lo=lo,hi=hi,
                rng_ratio=np.median(frange[m])/max(base_rng,1e-9),
                ttr_ratio=np.median(ttr[m])/max(base_ttr,1e-9))
    return out

if __name__=="__main__":
    R={}
    T,O,H,L,C,V,N=E.load("data/spot/BTCUSDT-1m-full.pkl")
    split=int(np.datetime64('2022-01-01').astype('datetime64[ms]').astype(np.int64))
    R.update(measure(T,O,H,L,C,V,"BTC",tsplit=split))
    for sym,p in (("ETH","data/alt/ETHUSDT-1m.pkl"),("SOL","data/alt/SOLUSDT-1m.pkl"),
                  ("XRP","data/alt/XRPUSDT-1m.pkl"),("DOGE","data/alt/DOGEUSDT-1m.pkl")):
        if os.path.exists(p):
            T2,O2,H2,L2,C2,V2,N2=E.load(p)
            R.update(measure(T2,O2,H2,L2,C2,V2,sym))
    pickle.dump(R,open("/tmp/interp_val.pkl","wb"))
    print("DIRECTIONAL — Δmean in ATR, does the SIGN replicate?\n")
    hdr=f"{'observation':<34}" + "".join(f"{c:>13}" for c in
        ["BTC early","BTC late","ETH","SOL","XRP","DOGE"])
    print(hdr); print("-"*len(hdr))
    for k in WATCH:
        row=f"{k:<34}"; vals=[]
        for lab,wn in (("BTC","early"),("BTC","late"),("ETH","all"),("SOL","all"),
                       ("XRP","all"),("DOGE","all")):
            r=R.get((lab,wn,k))
            if r is None: row+=f"{'--':>13}"; continue
            s="*" if (r['lo']>0 or r['hi']<0) else " "
            row+=f"{r['d_mu']:>+12.3f}{s}"; vals.append(r['d_mu'])
        agree = "same sign" if vals and all(np.sign(v)==np.sign(vals[0]) for v in vals) else ""
        print(row+f"  {agree}")
    print("\n\nMAGNITUDE / TIMING — range ratio and bars-to-1ATR ratio (1.00 = no info)\n")
    hdr2=f"{'observation':<34}" + "".join(f"{c:>15}" for c in
        ["BTC early","BTC late","ETH","SOL","XRP","DOGE"])
    print(hdr2); print("-"*len(hdr2))
    for k in WATCH:
        row=f"{k:<34}"
        for lab,wn in (("BTC","early"),("BTC","late"),("ETH","all"),("SOL","all"),
                       ("XRP","all"),("DOGE","all")):
            r=R.get((lab,wn,k))
            row += f"{'--':>15}" if r is None else f"{r['rng_ratio']:>8.2f}/{r['ttr_ratio']:<6.2f}"
        print(row)
