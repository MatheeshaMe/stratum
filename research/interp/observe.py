"""§21 — the market representation layer.

Every timestamp carries the FULL multi-timeframe context. Nothing is collapsed
into a single categorical state (§1). Observations are separated from
interpretation (§11): this module only records what objectively happened.
"""
import numpy as np, sys, os
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','trader'))
import features as FT
from numpy.lib.stride_tricks import sliding_window_view

TFS = {"1m":1, "5m":5, "15m":15, "1h":60, "4h":240}

def agg(T,O,H,L,C,V,tf):
    ms=tf*60000; key=T-(T%ms)
    _,st=np.unique(key,return_index=True); st=np.sort(st); en=np.append(st[1:],len(T))
    return dict(t=key[st],o=O[st],h=np.maximum.reduceat(H,st),l=np.minimum.reduceat(L,st),
                c=C[en-1],v=np.add.reduceat(V,st),i0=st)

def tf_layer(b):
    """One timeframe's observation set. All causal."""
    O,H,L,C,V=b['o'],b['h'],b['l'],b['c'],b['v']; n=len(C)
    A=FT.atr(H,L,C)
    piv=FT.swings(H,L,A,theta=3.0); S=FT.structure(n,piv)
    d={}
    # ── structure: the evolving sequence, not a static label (§3)
    d['trend']=S['trend']; d['sh']=S['sh']; d['sl']=S['sl']
    d['psh']=S['psh']; d['psl']=S['psl']
    with np.errstate(invalid='ignore',divide='ignore'):
        d['swing_mag_atr']=np.abs(S['sh']-S['sl'])/A
        d['bos_up']=((C>S['sh']) & (np.roll(C,1)<=np.roll(S['sh'],1))).astype(np.int8)
        d['bos_dn']=((C<S['sl']) & (np.roll(C,1)>=np.roll(S['sl'],1))).astype(np.int8)
    # ── liquidity: pools and the interaction TYPE (§4)
    W=48
    ph=np.roll(FT.roll_max(H,W),1); pl=np.roll(FT.roll_min(L,W),1)
    d['pool_hi']=ph; d['pool_lo']=pl
    d['sweep_hi']=((H>ph)&(C<ph)).astype(np.int8)      # poke and close back
    d['sweep_lo']=((L<pl)&(C>pl)).astype(np.int8)
    d['accept_hi']=((C>ph)&(np.roll(C,1)>np.roll(ph,1))).astype(np.int8)   # two closes beyond
    d['accept_lo']=((C<pl)&(np.roll(C,1)<np.roll(pl,1))).astype(np.int8)
    with np.errstate(invalid='ignore'):
        d['pen_hi_atr']=(H-ph)/A; d['pen_lo_atr']=(pl-L)/A
    eqh=np.zeros(n,np.int8); eql=np.zeros(n,np.int8)
    for i in range(W,n):
        if np.isfinite(ph[i]) and np.isfinite(A[i]) and A[i]>0:
            eqh[i]=int(np.sum(np.abs(H[i-W:i]-ph[i])<=0.15*A[i])>=2)
        if np.isfinite(pl[i]) and np.isfinite(A[i]) and A[i]>0:
            eql[i]=int(np.sum(np.abs(L[i-W:i]-pl[i])<=0.15*A[i])>=2)
    d['equal_hi']=eqh; d['equal_lo']=eql
    # ── price action: candle facts (§5)
    rng=np.maximum(H-L,1e-12); body=np.abs(C-O)
    d['body_frac']=body/rng
    d['wick_up']=(H-np.maximum(O,C))/rng
    d['wick_dn']=(np.minimum(O,C)-L)/rng
    d['close_loc']=(C-L)/rng
    d['range_atr']=rng/A
    d['dirn']=np.sign(C-O)
    eng=np.zeros(n,np.int8)
    eng[1:]=((body[1:]>body[:-1])&(np.sign(C-O)[1:]!=np.sign(C-O)[:-1])).astype(np.int8)
    d['engulf']=eng
    inside=np.zeros(n,np.int8)
    inside[1:]=((H[1:]<=H[:-1])&(L[1:]>=L[:-1])).astype(np.int8)
    d['inside']=inside
    # ── volatility / volume regime
    d['atr']=A; d['atr_pct']=A/C
    vma=np.convolve(V,np.ones(96)/96,'full')[:n]
    with np.errstate(invalid='ignore',divide='ignore'):
        d['rel_vol']=V/np.where(vma==0,np.nan,vma)
    R=FT.regime(b,A); d['vol_pct']=R['vol_pct']; d['efficiency']=R['efficiency']
    d['expansion']=R['expansion']
    Loc=FT.htf_location(b,A,S); d['range_pos']=Loc['range_pos']
    Ap=FT.approach(b,A)
    d['app_eff']=Ap['app_eff']; d['app_vel']=Ap['app_vel_atr']; d['app_decel']=Ap['app_decel']
    d['_piv']=piv; d['_S']=S
    return d

def sequences(b, d, win=12):
    """§5/§18 — sequences, because a sweep is an EVENT whose meaning is set by
    what follows. Each returns a 0/1 flag on the bar the SEQUENCE COMPLETES."""
    C,H,L,O=b['c'],b['h'],b['l'],b['o']; n=len(C); A=d['atr']
    out={k:np.zeros(n,np.int8) for k in
         ("sweep_reclaim_disp_up","sweep_accept_dn","sweep_reclaim_disp_dn","sweep_accept_up",
          "compress_expand_up","compress_expand_dn","brk_fail_rev_up","brk_fail_rev_dn",
          "impulse_pull_cont_up","impulse_pull_cont_dn")}
    sl_,sh_=d['sl'],d['sh']; pl,ph=d['pool_lo'],d['pool_hi']
    for i in range(win+2, n-1):
        a=A[i]
        if not np.isfinite(a) or a<=0: continue
        # sweep low -> reclaim -> bullish displacement (all within `win`)
        j=np.where(d['sweep_lo'][max(i-win,0):i+1]==1)[0]
        if len(j):
            k=max(i-win,0)+j[-1]
            reclaim = np.isfinite(pl[k]) and C[i]>pl[k]
            disp    = (C[i]-O[i])>0 and (C[i]-C[k])>1.0*a
            if reclaim and disp: out["sweep_reclaim_disp_up"][i]=1
            if np.isfinite(pl[k]) and C[i]<pl[k] and (C[k]-C[i])>0.5*a:
                out["sweep_accept_dn"][i]=1
        j=np.where(d['sweep_hi'][max(i-win,0):i+1]==1)[0]
        if len(j):
            k=max(i-win,0)+j[-1]
            reclaim = np.isfinite(ph[k]) and C[i]<ph[k]
            disp    = (C[i]-O[i])<0 and (C[k]-C[i])>1.0*a
            if reclaim and disp: out["sweep_reclaim_disp_dn"][i]=1
            if np.isfinite(ph[k]) and C[i]>ph[k] and (C[i]-C[k])>0.5*a:
                out["sweep_accept_up"][i]=1
        # compression -> expansion
        r=d['range_atr']
        if np.isfinite(r[i]) and np.nanmean(r[max(i-win,0):i])<0.7 and r[i]>1.5:
            if C[i]>O[i]: out["compress_expand_up"][i]=1
            else:         out["compress_expand_dn"][i]=1
        # breakout -> failure -> reversal
        if d['bos_up'][max(i-win,0):i].sum()>0 and np.isfinite(sh_[i]) and C[i]<sh_[i] \
           and (C[i]-O[i])<0 and (O[i]-C[i])>0.8*a: out["brk_fail_rev_dn"][i]=1
        if d['bos_dn'][max(i-win,0):i].sum()>0 and np.isfinite(sl_[i]) and C[i]>sl_[i] \
           and (C[i]-O[i])>0 and (C[i]-O[i])>0.8*a: out["brk_fail_rev_up"][i]=1
        # impulse -> pullback -> continuation
        if d['trend'][i]==1 and d['bos_up'][i]==1 and np.nanmin(C[max(i-win,0):i])<C[i]-0.5*a:
            out["impulse_pull_cont_up"][i]=1
        if d['trend'][i]==-1 and d['bos_dn'][i]==1 and np.nanmax(C[max(i-win,0):i])>C[i]+0.5*a:
            out["impulse_pull_cont_dn"][i]=1
    return out

def build(T,O,H,L,C,V, base_tf="5m"):
    """Multi-timeframe representation aligned to the base timeframe grid (§2)."""
    layers={}; bars={}
    for name,tf in TFS.items():
        b=agg(T,O,H,L,C,V,tf); bars[name]=b; layers[name]=tf_layer(b)
        layers[name]["_seq"]=sequences(b,layers[name])
    bb=bars[base_tf]; nb=len(bb['c'])
    aligned={}
    for name in TFS:
        if name==base_tf:
            for k,v in layers[name].items():
                if k.startswith('_'): continue
                aligned[f"{name}.{k}"]=v
            for k,v in layers[name]["_seq"].items(): aligned[f"{name}.seq.{k}"]=v
            continue
        src=bars[name]
        # map each base bar to the last CLOSED higher-timeframe bar (causal)
        idx=np.searchsorted(src['t'], bb['t'], side='right')-2
        idx=np.clip(idx,0,len(src['c'])-1)
        for k,v in layers[name].items():
            if k.startswith('_'): continue
            aligned[f"{name}.{k}"]=np.asarray(v)[idx]
        for k,v in layers[name]["_seq"].items():
            aligned[f"{name}.seq.{k}"]=np.asarray(v)[idx]
    return bb, aligned, bars, layers
