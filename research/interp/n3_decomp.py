#!/usr/bin/env python3
"""N-3 — decomposition of the frequency/payoff compensation."""
import numpy as np

def decompose(fret_c, fret_b):
    """Exact FREQ / PAYOFF / INTERACTION split of Δmean."""
    c=fret_c[np.isfinite(fret_c)]; b=fret_b[np.isfinite(fret_b)]
    if len(c)<200 or len(b)<200: return None
    def parts(x):
        up=x[x>0]; dn=x[x<=0]
        if len(up)<10 or len(dn)<10: return None
        return x.mean(), (x>0).mean(), up.mean(), dn.mean()
    pc=parts(c); pb=parts(b)
    if pc is None or pb is None: return None
    mc,p_c,u_c,d_c = pc; mb,p_b,u_b,d_b = pb
    dp=p_c-p_b; du=u_c-u_b; dd=d_c-d_b
    FREQ = dp*(u_b-d_b)
    PAY  = p_b*du + (1-p_b)*dd
    INT  = dp*(du-dd)
    kappa = (-PAY/FREQ) if FREQ>1e-9 else np.nan
    if FREQ>1e-9:
        if kappa>=0.75: typ="A"
        elif kappa>=0.25: typ="B"
        else: typ="D" if (du>=0 and abs(d_c)<=abs(d_b)) else "C"
    else: typ="—"
    return dict(n=len(c), mean=mc, d_mean=mc-mb, p_up=p_c, d_p=dp,
                u=u_c, d_u=du, d=d_c, d_d=dd,
                FREQ=FREQ, PAYOFF=PAY, INTER=INT, kappa=kappa, type=typ)

def kappa_ci(fret_c, fret_b, iters=1200, block=48, seed=0):
    rg=np.random.default_rng(seed)
    c=fret_c[np.isfinite(fret_c)]; b=fret_b[np.isfinite(fret_b)]
    ks=[]
    nbc=int(np.ceil(len(c)/block)); nbb=int(np.ceil(len(b)/block))
    for _ in range(iters):
        sc=np.concatenate([np.take(c,np.arange(i,i+block),mode='wrap')
                           for i in rg.integers(0,len(c),nbc)])[:len(c)]
        sb=np.concatenate([np.take(b,np.arange(i,i+block),mode='wrap')
                           for i in rg.integers(0,len(b),nbb)])[:len(b)]
        r=decompose(sc,sb)
        if r and np.isfinite(r['kappa']): ks.append(r['kappa'])
    if len(ks)<100: return (np.nan,np.nan)
    return np.percentile(ks,2.5), np.percentile(ks,97.5)
