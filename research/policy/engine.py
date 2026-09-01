"""Adaptive policy engine: market state -> action, with dynamic stop and target.

Nothing here is a fixed parameter that a trader would call arbitrary:
  stop   = structural invalidation (last opposing confirmed swing +/- 0.25 ATR)
  target = next opposing liquidity (prior swing extreme beyond entry)
  R:R    = an OUTPUT of those two, never an input
"""
import numpy as np, sys, os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','trader'))
import features as FT

MAKER=1.5/1e4; TAKER=4.5/1e4; HALF=0.63/1e4
COST_LIMIT=MAKER+TAKER+HALF
COST_MKT=(TAKER+HALF)*2
ACTIONS=["L_CONT","S_CONT","L_REV","S_REV","L_BRK","S_BRK","WAIT"]

def agg(T,O,H,L,C,V,N,tf):
    ms=tf*60000; key=T-(T%ms)
    _,st=np.unique(key,return_index=True); st=np.sort(st); en=np.append(st[1:],len(T))
    return dict(t=key[st],o=O[st],h=np.maximum.reduceat(H,st),l=np.minimum.reduceat(L,st),
                c=C[en-1],v=np.add.reduceat(V,st))

def market_state(b):
    """Everything the system knows, causal. Returns ctx dict + discrete state id."""
    C,H,L=b['c'],b['h'],b['l']; n=len(C)
    A=FT.atr(H,L,C)
    piv=FT.swings(H,L,A,theta=3.0); S=FT.structure(n,piv)
    R=FT.regime(b,A); Loc=FT.htf_location(b,A,S); Lq=FT.liquidity(b,A,S); Ap=FT.approach(b,A)
    # HTF trend: close beyond trailing 96-bar extreme, carried forward
    hi=np.roll(FT.roll_max(H,96),1); lo=np.roll(FT.roll_min(L,96),1)
    tr=np.zeros(n,np.int8); last=0
    for i in range(n):
        if np.isfinite(hi[i]) and C[i]>hi[i]: last=1
        elif np.isfinite(lo[i]) and C[i]<lo[i]: last=-1
        tr[i]=last
    ctx=dict(A=A,S=S,htf=tr,piv=piv,**R,**Loc,**Lq,**Ap)
    # discrete state: trend(3) x vol(3) x location(3)
    vp=ctx['vol_pct']; rp=ctx['range_pos']
    vb=np.where(np.isnan(vp),1,np.where(vp<0.33,0,np.where(vp<0.67,1,2)))
    lb=np.where(np.isnan(rp),1,np.where(rp<0.33,0,np.where(rp<0.67,1,2)))
    tb=(tr+1)                       # 0 down, 1 flat, 2 up
    ctx['state']=(tb*9+vb*3+lb).astype(np.int16)
    return ctx

def next_liquidity(b,ctx,i,side,horizon=240):
    """Target = the next opposing liquidity pool ABOVE/BELOW price, causal."""
    H,L,C=b['h'],b['l'],b['c']
    piv=ctx['piv']
    best=np.nan
    for cb,pb,px,kind in reversed(piv):
        if cb>i: continue
        if i-cb>horizon: break
        if side>0 and kind>0 and px>C[i]:
            best=px if not np.isfinite(best) else min(best,px)
        if side<0 and kind<0 and px<C[i]:
            best=px if not np.isfinite(best) else max(best,px)
    if not np.isfinite(best):
        # fall back to the trailing range boundary
        best = ctx['prior_hi'][i] if side>0 else ctx['prior_lo'][i]
    return best

def structural_stop(ctx,i,side,buf=0.25):
    lvl = ctx['S']['sl'][i] if side>0 else ctx['S']['sh'][i]
    if not np.isfinite(lvl): return np.nan
    return lvl - buf*ctx['A'][i] if side>0 else lvl + buf*ctx['A'][i]

def action_trigger(action,b,ctx,i):
    """Does this action have a live setup at bar i? Returns (side, entry, cost)."""
    C,H,L,O=b['c'],b['h'],b['l'],b['o']; A=ctx['A']
    tr=ctx['htf'][i]; rp=ctx['range_pos'][i]; a=A[i]
    if not np.isfinite(a) or a<=0: return None
    sh,sl=ctx['S']['sh'][i],ctx['S']['sl'][i]
    if action=="L_CONT":
        if tr!=1: return None
        if not (np.isfinite(sl) and C[i]>sl and C[i]<C[i-1]): return None
        return 1, C[i], COST_MKT
    if action=="S_CONT":
        if tr!=-1: return None
        if not (np.isfinite(sh) and C[i]<sh and C[i]>C[i-1]): return None
        return -1, C[i], COST_MKT
    if action=="L_REV":
        if not (ctx['sweep_lo'][i]==1): return None
        if not (np.isfinite(rp) and rp<0.35): return None
        return 1, C[i], COST_MKT
    if action=="S_REV":
        if not (ctx['sweep_hi'][i]==1): return None
        if not (np.isfinite(rp) and rp>0.65): return None
        return -1, C[i], COST_MKT
    if action=="L_BRK":
        if not (np.isfinite(sh) and C[i]>sh and C[i-1]<=sh): return None
        return 1, C[i], COST_MKT
    if action=="S_BRK":
        if not (np.isfinite(sl) and C[i]<sl and C[i-1]>=sl): return None
        return -1, C[i], COST_MKT
    return None

def run_trade(b,ctx,i,side,entry,cost,maxb=120,manage="target",trail_buf=0.25):
    """Dynamic stop and target. Same-bar ambiguity resolves AGAINST the trade;
    the entry bar may trigger the stop but never the target (C9/C10)."""
    H,L,C=b['h'],b['l'],b['c']; A=ctx['A']; n=len(C)
    stop=structural_stop(ctx,i,side)
    if not np.isfinite(stop): return None
    # C11: the stop MUST sit beyond the entry in the losing direction. A sweep
    # bar's new extreme is not yet a confirmed pivot, so the structural level is
    # often on the wrong side -- those setups are not tradeable, not free wins.
    if side>0 and stop>=entry: return None
    if side<0 and stop<=entry: return None
    risk=abs(entry-stop)
    if risk<=0 or risk/entry<0.0015 or risk/entry>0.12: return None
    tgt=next_liquidity(b,ctx,i,side)
    if not np.isfinite(tgt): return None
    if side>0 and tgt<=entry: return None
    if side<0 and tgt>=entry: return None
    rr=(abs(tgt-entry))/risk
    if rr<0.3 or rr>50: return None
    st=stop
    for j in range(i,min(i+1+maxb,n)):
        if j==i:
            if (L[j]<=st) if side>0 else (H[j]>=st):
                return dict(R=side*(st-entry)/risk-cost*entry/risk,bars=0,rr=rr,
                            exit="stop",risk_pct=risk/entry*100)
            continue
        if manage=="trail":
            lvl=ctx['S']['sl'][j] if side>0 else ctx['S']['sh'][j]
            if np.isfinite(lvl):
                cand=(lvl-trail_buf*A[j]) if side>0 else (lvl+trail_buf*A[j])
                if side>0 and cand<L[j]: st=max(st,cand)      # C12
                if side<0 and cand>H[j]: st=min(st,cand)
        hs=(L[j]<=st) if side>0 else (H[j]>=st)
        ht=(H[j]>=tgt) if side>0 else (L[j]<=tgt)
        if hs: return dict(R=side*(st-entry)/risk-cost*entry/risk,bars=j-i,rr=rr,
                           exit="stop",risk_pct=risk/entry*100)
        if manage=="target" and ht:
            return dict(R=side*(tgt-entry)/risk-cost*entry/risk,bars=j-i,rr=rr,
                        exit="target",risk_pct=risk/entry*100)
    j=min(i+maxb,n-1)
    return dict(R=side*(C[j]-entry)/risk-cost*entry/risk,bars=j-i,rr=rr,
                exit="time",risk_pct=risk/entry*100)
