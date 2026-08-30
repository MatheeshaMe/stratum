"""Causal market-structure engine: swings, trend state, impulses, pullbacks, breaks.

Everything here is confirmed-only. A pivot at bar i is NOT known at bar i; it
becomes known at the later bar j where price has retraced `theta * ATR[i]` from
it. Every state array is indexed by the bar at which the information EXISTS,
never the bar the pivot occurred on. This is the discipline that killed three
earlier candidates in this project when it was violated.
"""
import numpy as np

def wilder(x, p=14):
    o=np.full(len(x), np.nan)
    if len(x)<=p: return o
    s=x[:p].mean(); o[p-1]=s
    for i in range(p,len(x)): s=(s*(p-1)+x[i])/p; o[i]=s
    return o

def atr(H,L,C,p=14):
    pc=np.roll(C,1); pc[0]=C[0]
    return wilder(np.maximum(H-L,np.maximum(np.abs(H-pc),np.abs(L-pc))),p)

def zigzag(H, L, A, theta=2.0):
    """ATR-normalised ZigZag. Returns confirmed pivots as
    (confirm_bar, pivot_bar, price, kind) with kind +1 high, -1 low.

    A pivot is confirmed once price moves theta*ATR against it. `confirm_bar`
    is the first bar at which a real-time system could know the pivot exists.
    """
    n=len(H); piv=[]
    dirn=0                      # +1 seeking a high, -1 seeking a low
    ext_i=0; ext_p=H[0]
    for i in range(1,n):
        a=A[i]
        if not np.isfinite(a) or a<=0: continue
        if dirn>=0:
            if H[i]>=ext_p: ext_i,ext_p=i,H[i]
            if dirn==0:
                if L[i]<=ext_p-theta*a: dirn=-1; piv.append((i,ext_i,ext_p,+1)); ext_i,ext_p=i,L[i]
                continue
            if L[i]<=ext_p-theta*a:
                piv.append((i,ext_i,ext_p,+1)); dirn=-1; ext_i,ext_p=i,L[i]
        else:
            if L[i]<=ext_p: ext_i,ext_p=i,L[i]
            if H[i]>=ext_p+theta*a:
                piv.append((i,ext_i,ext_p,-1)); dirn=+1; ext_i,ext_p=i,H[i]
    return piv

def structure_state(n, piv):
    """Per-bar structural state, valid from each pivot's CONFIRM bar onward.

    Returns dict of arrays:
      trend   +1 uptrend (HH & HL), -1 downtrend (LH & LL), 0 otherwise
      last_sh / last_sl   most recent confirmed swing high / low price
      prev_sh / prev_sl   the one before that
      leg_dir  direction of the leg currently forming
      leg_start_px, leg_start_i
      imp_size  size of the last completed impulse, in ATR
      pb_depth  retracement of the current pullback as a fraction of that impulse
      n_piv     pivots confirmed so far
    """
    out={k:np.full(n,np.nan) for k in
         ('last_sh','last_sl','prev_sh','prev_sl','leg_start_px','imp_atr')}
    out['trend']=np.zeros(n,dtype=np.int8)
    out['leg_dir']=np.zeros(n,dtype=np.int8)
    out['leg_start_i']=np.full(n,-1,dtype=np.int64)
    out['n_piv']=np.zeros(n,dtype=np.int32)
    highs=[]; lows=[]
    cur=0
    for k,(cb,pb,px,kind) in enumerate(piv):
        nxt=piv[k+1][0] if k+1<len(piv) else n
        if kind>0: highs.append((pb,px))
        else:      lows.append((pb,px))
        sh=highs[-1][1] if highs else np.nan
        sl=lows[-1][1]  if lows  else np.nan
        psh=highs[-2][1] if len(highs)>1 else np.nan
        psl=lows[-2][1]  if len(lows)>1  else np.nan
        tr=0
        if np.isfinite(sh) and np.isfinite(psh) and np.isfinite(sl) and np.isfinite(psl):
            if sh>psh and sl>psl: tr=+1
            elif sh<psh and sl<psl: tr=-1
        sl_,sh_=slice(cb,nxt),None
        out['last_sh'][cb:nxt]=sh; out['last_sl'][cb:nxt]=sl
        out['prev_sh'][cb:nxt]=psh; out['prev_sl'][cb:nxt]=psl
        out['trend'][cb:nxt]=tr
        out['leg_dir'][cb:nxt]=-kind          # after a high is confirmed, leg is down
        out['leg_start_px'][cb:nxt]=px
        out['leg_start_i'][cb:nxt]=pb
        out['n_piv'][cb:nxt]=k+1
        # size of the impulse that just ENDED, in ATR at its start
        if k>=1:
            _,pb0,px0,_=piv[k-1]
            out['imp_atr'][cb:nxt]=abs(px-px0)
    return out

def derived(C,H,L,A,S):
    """Bar-by-bar derived structure features. All causal."""
    n=len(C); d={}
    d['pb_frac']=np.full(n,np.nan)      # retracement of the last impulse so far
    d['dist_sh_atr']=(S['last_sh']-C)/A
    d['dist_sl_atr']=(C-S['last_sl'])/A
    d['imp_atr']=S['imp_atr']/A
    # pullback depth: how far price has retraced from the leg start
    lp=S['leg_start_px']; imp=S['imp_atr']
    with np.errstate(invalid='ignore',divide='ignore'):
        d['pb_frac']=np.where(imp>0, np.abs(C-lp)/imp, np.nan)
    # break of structure: close beyond the last confirmed swing in trend direction
    d['bos_up']=(C>S['last_sh']).astype(np.int8)
    d['bos_dn']=(C<S['last_sl']).astype(np.int8)
    # trend efficiency over the last 60 bars: net move / path length
    eff=np.full(n,np.nan)
    dif=np.abs(np.diff(C,prepend=C[0]))
    cs=np.cumsum(dif)
    W=60
    net=np.full(n,np.nan); net[W:]=np.abs(C[W:]-C[:-W])
    path=np.full(n,np.nan); path[W:]=cs[W:]-cs[:-W]
    with np.errstate(invalid='ignore',divide='ignore'):
        eff=np.where(path>0, net/path, np.nan)
    d['efficiency']=eff
    return d
