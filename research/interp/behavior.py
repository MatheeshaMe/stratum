"""Four-class forward behaviour measurement (§4).

DIRECTION  mean fwd return, P(up), P(+k ATR before -k ATR)
MAGNITUDE  MFE, MAE, forward range, tail mass
TIMING     bars to first touch of +/-0.25 / 0.5 / 1 / 2 ATR
PATH       variance, skew, kurtosis, MAE-before-MFE ordering

Everything in ATR units. Everything causal: bar i uses only bars > i for the
forward window and only bars <= i for conditioning.
"""
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

THRESH=[0.25,0.5,1.0,2.0]

def forward_block(b, A, FWD=48, stride=3):
    """Returns a dict of forward-behaviour arrays on a strided grid."""
    C,H,L=b['c'],b['h'],b['l']; n=len(C)
    idx=np.arange(2000, n-FWD-2, stride)
    out={k:np.full(len(idx),np.nan) for k in
         ("fret","frange","mfe","mae","t_mfe","t_mae","mae_first")}
    for k in THRESH:
        out[f"t_up_{k}"]=np.full(len(idx),np.nan)
        out[f"t_dn_{k}"]=np.full(len(idx),np.nan)
        out[f"up_first_{k}"]=np.full(len(idx),np.nan)
    for m,i in enumerate(idx):
        a=A[i]
        if not np.isfinite(a) or a<=0: continue
        hs=H[i+1:i+1+FWD]; ls=L[i+1:i+1+FWD]; c0=C[i]
        up=(hs-c0)/a; dn=(c0-ls)/a
        out["fret"][m]=(C[i+FWD]-c0)/a
        out["frange"][m]=(hs.max()-ls.min())/a
        out["mfe"][m]=up.max(); out["mae"][m]=dn.max()
        out["t_mfe"][m]=int(np.argmax(up))+1; out["t_mae"][m]=int(np.argmax(dn))+1
        out["mae_first"][m]=1.0 if out["t_mae"][m]<out["t_mfe"][m] else 0.0
        for k in THRESH:
            u=np.argmax(up>=k)+1 if (up>=k).any() else np.nan
            d=np.argmax(dn>=k)+1 if (dn>=k).any() else np.nan
            out[f"t_up_{k}"][m]=u; out[f"t_dn_{k}"][m]=d
            if np.isfinite(u) or np.isfinite(d):
                uu=u if np.isfinite(u) else 1e9; dd=d if np.isfinite(d) else 1e9
                out[f"up_first_{k}"][m]=1.0 if uu<dd else 0.0
    return idx, out

def block_ci(x, block=48, iters=1200, seed=0):
    x=x[np.isfinite(x)]
    if len(x)<100: return (np.nan,np.nan)
    rg=np.random.default_rng(seed); nb=int(np.ceil(len(x)/block)); m=np.empty(iters)
    for k in range(iters):
        st=rg.integers(0,len(x),nb)
        s=np.concatenate([np.take(x,np.arange(i,i+block),mode='wrap') for i in st])[:len(x)]
        m[k]=s.mean()
    return np.percentile(m,2.5),np.percentile(m,97.5)

def profile(F, mask, base=None):
    """Full four-class profile for a conditional subset."""
    def nm(k): 
        v=F[k][mask]; v=v[np.isfinite(v)]
        return v
    fr=nm("fret")
    if len(fr)<100: return None
    p=dict(n=int(len(fr)))
    # DIRECTION
    p["mean"]=fr.mean(); p["p_up"]=(fr>0).mean()
    for k in THRESH:
        v=nm(f"up_first_{k}")
        p[f"upfirst_{k}"]=v.mean() if len(v) else np.nan
    # MAGNITUDE
    p["mfe"]=np.median(nm("mfe")); p["mae"]=np.median(nm("mae"))
    p["range"]=np.median(nm("frange")); p["tail2"]=(np.abs(fr)>2).mean()
    # TIMING
    for k in THRESH:
        u=nm(f"t_up_{k}"); d=nm(f"t_dn_{k}")
        both=np.concatenate([u,d])
        p[f"t_{k}"]=np.median(both) if len(both) else np.nan
    # PATH
    p["sd"]=fr.std()
    p["skew"]=float(((fr-fr.mean())**3).mean()/max(fr.std()**3,1e-9))
    p["kurt"]=float(((fr-fr.mean())**4).mean()/max(fr.std()**4,1e-9))
    v=nm("mae_first"); p["mae_first"]=v.mean() if len(v) else np.nan
    if base is not None:
        p["d_mean"]=p["mean"]-base["mean"]
        p["d_pup"]=p["p_up"]-base["p_up"]
        for k in THRESH: p[f"d_upfirst_{k}"]=p[f"upfirst_{k}"]-base[f"upfirst_{k}"]
        p["r_mfe"]=p["mfe"]/base["mfe"]; p["r_mae"]=p["mae"]/base["mae"]
        p["r_range"]=p["range"]/base["range"]; p["r_tail"]=p["tail2"]/base["tail2"]
        p["r_sd"]=p["sd"]/base["sd"]; p["d_skew"]=p["skew"]-base["skew"]
        for k in THRESH: p[f"r_t_{k}"]=p[f"t_{k}"]/max(base[f"t_{k}"],1e-9)
        p["d_maefirst"]=p["mae_first"]-base["mae_first"]
    return p
