"""Phase 3 — the contextual feature engine.

Six levels of the hierarchy, every feature causal, every feature justified by a
trader question rather than by being an available indicator.

L1 REGIME     what kind of market is this
L2 LOCATION   where are we in the higher-timeframe picture
L3 STRUCTURE  who is in control
L4 LIQUIDITY  where is the fuel, and what happened to it
L5 SETUP      where did displacement originate
L6 APPROACH   how is price arriving at that origin
"""
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

def wilder(x,p=14):
    o=np.full(len(x),np.nan)
    if len(x)<=p: return o
    s=x[:p].mean(); o[p-1]=s
    for i in range(p,len(x)): s=(s*(p-1)+x[i])/p; o[i]=s
    return o
def atr(H,L,C,p=14):
    pc=np.roll(C,1); pc[0]=C[0]
    return wilder(np.maximum(H-L,np.maximum(np.abs(H-pc),np.abs(L-pc))),p)
def roll_max(x,w):
    o=np.full(len(x),np.nan)
    if len(x)>=w: o[w-1:]=sliding_window_view(x,w).max(1)
    return o
def roll_min(x,w):
    o=np.full(len(x),np.nan)
    if len(x)>=w: o[w-1:]=sliding_window_view(x,w).min(1)
    return o

# ---------------------------------------------------------------- swings
def swings(H,L,A,theta=3.0):
    """Confirmed-only ZigZag. Returns (confirm_bar, pivot_bar, price, kind)."""
    n=len(H); piv=[]; dirn=0; ei=0; ep=H[0]
    for i in range(1,n):
        a=A[i]
        if not np.isfinite(a) or a<=0: continue
        if dirn>=0:
            if H[i]>=ep: ei,ep=i,H[i]
            if L[i]<=ep-theta*a:
                piv.append((i,ei,ep,+1)); dirn=-1; ei,ep=i,L[i]
        else:
            if L[i]<=ep: ei,ep=i,L[i]
            if H[i]>=ep+theta*a:
                piv.append((i,ei,ep,-1)); dirn=+1; ei,ep=i,H[i]
    return piv

def structure(n,piv):
    """Per-bar structure, written from each pivot's CONFIRM bar."""
    o={k:np.full(n,np.nan) for k in ('sh','sl','psh','psl','sh_i','sl_i')}
    o['trend']=np.zeros(n,np.int8); o['npiv']=np.zeros(n,np.int32)
    hs=[]; ls=[]
    for k,(cb,pb,px,kind) in enumerate(piv):
        nx=piv[k+1][0] if k+1<len(piv) else n
        (hs if kind>0 else ls).append((pb,px))
        sh=hs[-1][1] if hs else np.nan; sl=ls[-1][1] if ls else np.nan
        psh=hs[-2][1] if len(hs)>1 else np.nan; psl=ls[-2][1] if len(ls)>1 else np.nan
        tr=0
        if np.isfinite(sh) and np.isfinite(psh) and np.isfinite(sl) and np.isfinite(psl):
            if sh>psh and sl>psl: tr=1
            elif sh<psh and sl<psl: tr=-1
        for key,val in (('sh',sh),('sl',sl),('psh',psh),('psl',psl),
                        ('sh_i',hs[-1][0] if hs else np.nan),
                        ('sl_i',ls[-1][0] if ls else np.nan)):
            o[key][cb:nx]=val
        o['trend'][cb:nx]=tr; o['npiv'][cb:nx]=k+1
    return o

# ------------------------------------------------------------- L1 regime
def regime(b,A):
    C=b['c']; n=len(C); out={}
    atrp=A/C
    pct=np.full(n,np.nan)
    W=2016
    for a in range(W,n,96):
        w=atrp[a-W:a]; w=w[np.isfinite(w)]
        if len(w)<200: continue
        hi=min(a+96,n); pct[a:hi]=np.searchsorted(np.sort(w),atrp[a:hi])/len(w)
    out['vol_pct']=pct
    d=np.abs(np.diff(C,prepend=C[0])); cs=np.cumsum(d)
    W2=96
    net=np.full(n,np.nan); net[W2:]=np.abs(C[W2:]-C[:-W2])
    path=np.full(n,np.nan); path[W2:]=cs[W2:]-cs[:-W2]
    with np.errstate(invalid='ignore',divide='ignore'):
        out['efficiency']=np.where(path>0,net/path,np.nan)
    # expansion vs contraction: short ATR over long ATR
    a_s=np.full(n,np.nan); a_l=np.full(n,np.nan)
    a_s[23:]=sliding_window_view(atrp,24).mean(1); a_l[95:]=sliding_window_view(atrp,96).mean(1)
    with np.errstate(invalid='ignore',divide='ignore'):
        out['expansion']=a_s/a_l
    return out

# ------------------------------------------------------- L2 HTF location
def htf_location(b,A,S,W=480):
    C=b['c']; H=b['h']; L=b['l']; n=len(C); out={}
    hi=roll_max(H,W); lo=roll_min(L,W)
    # shift by one bar so the window is strictly historical
    hi=np.roll(hi,1); lo=np.roll(lo,1); hi[0]=np.nan; lo[0]=np.nan
    rngw=np.maximum(hi-lo,1e-12)
    out['range_pos']=(C-lo)/rngw            # 0 = discount low, 1 = premium high
    out['dist_hi_atr']=(hi-C)/A
    out['dist_lo_atr']=(C-lo)/A
    out['range_atr']=rngw/A
    return out

# --------------------------------------------------------- L4 liquidity
def liquidity(b,A,S,lookback=96, eq_tol=0.15):
    """Where stops sit, and what just happened to them."""
    C=b['c']; H=b['h']; L=b['l']; n=len(C); out={}
    ph=np.roll(roll_max(H,lookback),1); pl=np.roll(roll_min(L,lookback),1)
    out['prior_hi']=ph; out['prior_lo']=pl
    # sweep: penetrate a prior extreme, then close back inside on the SAME bar
    out['sweep_lo']=((L<pl)&(C>pl)).astype(np.int8)
    out['sweep_hi']=((H>ph)&(C<ph)).astype(np.int8)
    # clean break: close beyond the extreme
    out['break_lo']=(C<pl).astype(np.int8)
    out['break_hi']=(C>ph).astype(np.int8)
    with np.errstate(invalid='ignore'):
        out['pen_lo_atr']=(pl-L)/A
        out['pen_hi_atr']=(H-ph)/A
    # equal lows/highs: prior extreme retested within eq_tol ATR, twice
    eq_lo=np.zeros(n,np.int8); eq_hi=np.zeros(n,np.int8)
    for i in range(lookback,n):
        if np.isfinite(pl[i]) and np.isfinite(A[i]) and A[i]>0:
            seg=L[i-lookback:i]
            eq_lo[i]=int(np.sum(np.abs(seg-pl[i])<=eq_tol*A[i])>=2)
        if np.isfinite(ph[i]) and np.isfinite(A[i]) and A[i]>0:
            seg=H[i-lookback:i]
            eq_hi[i]=int(np.sum(np.abs(seg-ph[i])<=eq_tol*A[i])>=2)
    out['equal_lo']=eq_lo; out['equal_hi']=eq_hi
    return out

# ------------------------------------------------------------ L6 approach
def approach(b,A,W=12):
    """How price is arriving: fast and efficient, or slow and exhausted."""
    C=b['c']; H=b['h']; L=b['l']; V=b['v']; n=len(C); out={}
    d=np.abs(np.diff(C,prepend=C[0])); cs=np.cumsum(d)
    net=np.full(n,np.nan); net[W:]=C[W:]-C[:-W]
    path=np.full(n,np.nan); path[W:]=cs[W:]-cs[:-W]
    with np.errstate(invalid='ignore',divide='ignore'):
        out['app_eff']=np.where(path>0,np.abs(net)/path,np.nan)
        out['app_vel_atr']=np.abs(net)/A
        # deceleration: last third of the approach vs the first third
        k=max(W//3,1)
        r1=np.full(n,np.nan); r2=np.full(n,np.nan)
        r1[W:]=np.abs(C[W-k:n-k]-C[:n-W])
        r2[W:]=np.abs(C[W:]-C[W-k:n-k])
        out['app_decel']=np.where(r1>0,r2/r1,np.nan)
    vma=np.convolve(V,np.ones(96)/96,'full')[:n]
    vs=np.full(n,np.nan); vs[W-1:]=sliding_window_view(V,W).mean(1)
    with np.errstate(invalid='ignore',divide='ignore'):
        out['app_vol']=vs/np.where(vma==0,np.nan,vma)
    out['app_dir']=np.sign(net)
    return out
