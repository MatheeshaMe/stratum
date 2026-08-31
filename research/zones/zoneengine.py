"""Supply/demand zone engine — base + impulse origin, causal throughout.

MECHANISM BEING TESTED
  A large order fills only partially at a price. The unfilled remainder rests.
  Price leaves fast (the impulse). When price returns, the remainder fills and
  pushes price away again.

That mechanism makes three sharp, falsifiable predictions, and they are what
this module is built to test — not to illustrate:

  P1  FRESHNESS DECAY. Resting orders are CONSUMED by touches. So
      reaction(1st touch) > reaction(2nd) > reaction(3rd+). This is the
      opposite of support/resistance logic, where repeated holds CONFIRM a
      level. The two theories disagree on the sign, which makes touch count a
      discriminating experiment rather than a descriptive one.

  P2  IMPULSE STRENGTH PROXIES ORDER SIZE. A bigger, more one-sided departure
      implies more unfilled remainder, so reaction should scale with impulse
      quality (displacement, body ratio, fair-value gap).

  P3  ORIGIN BEATS REPETITION. A never-touched zone should work on its FIRST
      visit — something plain S/R cannot predict, because S/R has no reason to
      expect a reaction at a price that has never reacted before.

CAUSALITY
  A zone is only knowable AFTER its impulse completes. `confirm_i` is the first
  bar at which a real-time system could draw the box. Touch counts are running
  counts using only prior touches. Nothing in a zone's state at time t uses a
  bar after t.
"""
import numpy as np

def wilder(x,p=14):
    o=np.full(len(x),np.nan)
    if len(x)<=p: return o
    s=x[:p].mean(); o[p-1]=s
    for i in range(p,len(x)): s=(s*(p-1)+x[i])/p; o[i]=s
    return o

def atr(H,L,C,p=14):
    pc=np.roll(C,1); pc[0]=C[0]
    return wilder(np.maximum(H-L,np.maximum(np.abs(H-pc),np.abs(L-pc))),p)

def find_zones(O,H,L,C,V,A,
               imp_min_atr=2.0, imp_max_bars=3, body_ratio=0.55,
               base_max_bars=3, base_max_atr=1.0, base_body_ratio=0.5):
    """Return list of zone dicts. Causal: confirm_i = last bar of the impulse.

    A zone is (base, impulse):
      base    : 1..base_max_bars bars, each with small body ratio, total range
                <= base_max_atr * ATR
      impulse : 1..imp_max_bars bars immediately after, net displacement
                >= imp_min_atr * ATR, dominant-direction body ratio >= body_ratio
    """
    n=len(C); zones=[]
    body=np.abs(C-O); rng=np.maximum(H-L,1e-12)
    br=body/rng
    for i in range(30, n-1):
        a=A[i]
        if not np.isfinite(a) or a<=0: continue
        for k in range(1, imp_max_bars+1):
            j=i+k-1
            if j>=n: break
            disp=C[j]-O[i]
            if abs(disp) < imp_min_atr*a: continue
            seg=slice(i,j+1)
            # every impulse bar must push the same way with a real body
            dirn=1 if disp>0 else -1
            bodies=(C[seg]-O[seg])*dirn
            if np.any(bodies<=0): continue
            if br[seg].mean() < body_ratio: continue
            # find the base immediately before
            for m in range(1, base_max_bars+1):
                s=i-m
                if s<1: break
                bs=slice(s,i)
                if br[bs].mean() > base_body_ratio: continue
                hi=H[bs].max(); lo=L[bs].min()
                if (hi-lo) > base_max_atr*a: continue
                # fair value gap inside the impulse: bar j-1 low > bar j-3 high (up)
                fvg=0.0
                if k>=3:
                    if dirn>0 and L[i+2]>H[i]: fvg=(L[i+2]-H[i])/a
                    if dirn<0 and H[i+2]<L[i]: fvg=(L[i]-H[i+2])/a
                zones.append(dict(
                    side=dirn,                 # +1 demand (buy zone), -1 supply
                    confirm_i=j,               # first bar the zone is knowable
                    base_lo=lo, base_hi=hi,
                    proximal=(hi if dirn>0 else lo),   # edge price meets first
                    distal=(lo if dirn>0 else hi),
                    base_bars=m, imp_bars=k,
                    imp_atr=abs(disp)/a,
                    imp_body_ratio=float(br[seg].mean()),
                    base_width_atr=(hi-lo)/a,
                    fvg_atr=fvg,
                    base_vol=float(V[bs].sum()/max(m,1)),
                    imp_vol=float(V[seg].sum()/max(k,1)),
                    atr_at_form=a, price_at_form=C[j]))
                break
            break
    return zones

def touch_events(zones, H, L, C, A, max_life_bars=8640, touch_buffer=0.0):
    """Every time price enters a zone, emitted in time order with a CAUSAL
    touch index (0 = first ever touch of that zone).

    A touch starts when price trades into the zone band and ends when price
    leaves it. Consecutive bars inside the zone are ONE touch.
    """
    n=len(C); out=[]
    for zi,z in enumerate(zones):
        lo,hi=z['base_lo'],z['base_hi']
        if touch_buffer:
            pad=touch_buffer*z['atr_at_form']; lo-=pad; hi+=pad
        start=z['confirm_i']+1
        end=min(start+max_life_bars, n-1)
        if end<=start: continue
        sl=slice(start,end)
        # death: first bar closing decisively through the distal edge
        if z['side']>0: dead=np.where(C[sl] < z['distal']-0.5*A[sl])[0]
        else:           dead=np.where(C[sl] > z['distal']+0.5*A[sl])[0]
        stop=(dead[0]+1) if len(dead) else (end-start)
        if stop<=0: continue
        inz=(L[start:start+stop]<=hi)&(H[start:start+stop]>=lo)
        if not inz.any(): continue
        edge=inz.copy(); edge[1:]&=~inz[:-1]
        idxs=np.where(edge)[0]+start
        for tc,i in enumerate(idxs):
            out.append(dict(zone=zi, i=int(i), touch_idx=tc, **z))
    out.sort(key=lambda d: d['i'])
    return out

def reaction(H,L,C,A,i,side,fwd=48):
    """Non-circular reaction measure, from the bar AFTER the touch begins."""
    n=len(C)
    j0=i+1; j1=min(i+1+fwd,n)
    if j1<=j0: return None
    px=C[i]; a=A[i]
    if not np.isfinite(a) or a<=0: return None
    mfe=(H[j0:j1].max()-px)/a if side>0 else (px-L[j0:j1].min())/a
    mae=(px-L[j0:j1].min())/a if side>0 else (H[j0:j1].max()-px)/a
    return dict(mfe=mfe, mae=mae, ratio=mfe/max(mae,1e-9), net=side*(C[j1-1]-px)/a)
