"""Phases 4-6 — setup engine, entry models, management models.

Theses are PRE-SPECIFIED here, before any of them is scored, so the interaction
search is not a fishing expedition over 2^6 context cells.

Execution is C9-correct throughout: a limit filled during bar i has its stop
live on bar i.
"""
import numpy as np, sys, os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import features as FT

MAKER=1.5/1e4; TAKER=4.5/1e4; HALF=0.63/1e4
COST_LIMIT_IN = MAKER + TAKER + HALF        # rest a limit, exit taker
COST_MKT_IN   = (TAKER+HALF)*2              # cross on entry and exit

def agg(T,O,H,L,C,V,N,tf):
    ms=tf*60000; key=T-(T%ms)
    _,st=np.unique(key,return_index=True); st=np.sort(st); en=np.append(st[1:],len(T))
    return dict(t=key[st],o=O[st],h=np.maximum.reduceat(H,st),l=np.minimum.reduceat(L,st),
                c=C[en-1],v=np.add.reduceat(V,st),i0=st)

def build_context(b, htf_mult=4):
    """Everything a trader would have on screen, causal."""
    A=FT.atr(b['h'],b['l'],b['c']); n=len(b['c'])
    piv=FT.swings(b['h'],b['l'],A,theta=3.0)
    S=FT.structure(n,piv)
    R=FT.regime(b,A); Loc=FT.htf_location(b,A,S); Lq=FT.liquidity(b,A,S); Ap=FT.approach(b,A)
    # higher timeframe trend, built on the same series by coarse aggregation
    W=htf_mult*24
    hi=np.roll(FT.roll_max(b['h'],W),1); lo=np.roll(FT.roll_min(b['l'],W),1)
    htf=np.zeros(n,np.int8)
    htf[np.isfinite(hi)&(b['c']>hi)]=1
    htf[np.isfinite(lo)&(b['c']<lo)]=-1
    # carry the last non-zero HTF state forward
    last=0
    for i in range(n):
        if htf[i]!=0: last=htf[i]
        else: htf[i]=last
    ctx=dict(A=A,S=S,htf=htf,**R,**Loc,**Lq,**Ap)
    return ctx, piv

def find_zones(b,A,imp_min_atr=2.0,imp_max_bars=3,body_ratio=0.55,
               base_max_bars=3,base_max_atr=1.0,base_body_ratio=0.5):
    O,H,L,C,V=b['o'],b['h'],b['l'],b['c'],b['v']; n=len(C)
    body=np.abs(C-O); rng=np.maximum(H-L,1e-12); br=body/rng
    Z=[]
    for i in range(30,n-1):
        a=A[i]
        if not np.isfinite(a) or a<=0: continue
        for k in range(1,imp_max_bars+1):
            j=i+k-1
            if j>=n: break
            disp=C[j]-O[i]
            if abs(disp)<imp_min_atr*a: continue
            sl=slice(i,j+1); dirn=1 if disp>0 else -1
            if np.any((C[sl]-O[sl])*dirn<=0): continue
            if br[sl].mean()<body_ratio: continue
            for m in range(1,base_max_bars+1):
                s=i-m
                if s<1: break
                bs=slice(s,i)
                if br[bs].mean()>base_body_ratio: continue
                hh=H[bs].max(); ll=L[bs].min()
                if (hh-ll)>base_max_atr*a: continue
                fvg=0.0
                if k>=3:
                    if dirn>0 and L[i+2]>H[i]: fvg=(L[i+2]-H[i])/a
                    if dirn<0 and H[i+2]<L[i]: fvg=(L[i]-H[i+2])/a
                Z.append(dict(side=dirn,confirm=j,lo=ll,hi=hh,
                              prox=(hh if dirn>0 else ll),
                              dist=(ll if dirn>0 else hh),
                              imp_atr=abs(disp)/a,fvg=fvg,
                              width_atr=(hh-ll)/a,a_form=a,
                              bos=int((dirn>0 and C[j]>H[max(s-20,0):s].max()) or
                                      (dirn<0 and C[j]<L[max(s-20,0):s].min()))))
                break
            break
    return Z

def zone_touches(Z,b,A,max_life=480):
    """First touch of each zone, with a running touch index. Causal."""
    H,L,C=b['h'],b['l'],b['c']; n=len(C); out=[]
    for zi,z in enumerate(Z):
        s=z['confirm']+1; e=min(s+max_life,n-1)
        if e<=s: continue
        seg=slice(s,e)
        if z['side']>0: dead=np.where(C[seg]<z['dist']-0.5*A[seg])[0]
        else:           dead=np.where(C[seg]>z['dist']+0.5*A[seg])[0]
        stop=(dead[0]+1) if len(dead) else (e-s)
        if stop<=0: continue
        inz=(L[s:s+stop]<=z['hi'])&(H[s:s+stop]>=z['lo'])
        if not inz.any(): continue
        edge=inz.copy(); edge[1:]&=~inz[:-1]
        for tc,i in enumerate(np.where(edge)[0]+s):
            out.append(dict(z=zi,i=int(i),touch=tc,**z))
    out.sort(key=lambda d:d['i'])
    return out

# ------------------------------------------------------------ entry models
def entry_signal(model, b, ctx, e, conf_bars=6):
    """Returns (entry_bar, entry_price, cost) or None. Causal."""
    O,H,L,C=b['o'],b['h'],b['l'],b['c']; n=len(C); A=ctx['A']
    i=e['i']; side=e['side']; prox=e['prox']
    if model=="A":                                   # blind limit at proximal edge
        if (side>0 and L[i]>prox) or (side<0 and H[i]<prox): return None
        return i, prox, COST_LIMIT_IN
    if model=="B":                                   # rejection candle, then market
        for j in range(i,min(i+conf_bars,n-1)):
            rng=max(H[j]-L[j],1e-12); body=abs(C[j]-O[j])
            wick=(min(O[j],C[j])-L[j])/rng if side>0 else (H[j]-max(O[j],C[j]))/rng
            if wick>0.45 and body/rng<0.5 and side*(C[j]-O[j])>0:
                return j+1, O[j+1], COST_MKT_IN
        return None
    if model=="C":                                   # sweep + reversal close
        for j in range(i,min(i+conf_bars,n-1)):
            swept = ctx['sweep_lo'][j] if side>0 else ctx['sweep_hi'][j]
            if swept and side*(C[j]-O[j])>0:
                return j+1, O[j+1], COST_MKT_IN
        return None
    if model=="D":                                   # local CHoCH then pullback limit
        for j in range(i,min(i+conf_bars*2,n-1)):
            sh,sl_=ctx['S']['sh'][j],ctx['S']['sl'][j]
            broke=(np.isfinite(sh) and C[j]>sh) if side>0 else (np.isfinite(sl_) and C[j]<sl_)
            if broke:
                lim=C[j]-side*0.5*A[j]
                for k in range(j+1,min(j+conf_bars,n-1)):
                    if (side>0 and L[k]<=lim) or (side<0 and H[k]>=lim):
                        return k, lim, COST_LIMIT_IN
                return None
        return None
    if model=="E":                                   # momentum continuation, market
        for j in range(i,min(i+conf_bars,n-1)):
            if side*(C[j]-C[max(j-3,0)])>1.0*A[j]:
                return j+1, O[j+1], COST_MKT_IN
        return None
    return None

# -------------------------------------------------------- management models
def manage(b,ctx,i,side,entry,stop,mode="fixed",rr=3.0,maxb=120,cost=0.0,
           trail_atr=2.5):
    """C9-correct: the stop is live on the entry bar."""
    H,L,C=b['h'],b['l'],b['c']; A=ctx['A']; n=len(C)
    risk=abs(entry-stop)
    if risk<=0 or risk/entry<0.0010 or risk/entry>0.12: return None
    tgt=entry+side*rr*risk if rr else None
    st=stop; mfe=0.0; mae=0.0
    for j in range(i,min(i+1+maxb,n)):
        hi=(H[j]-entry)/risk if side>0 else (entry-L[j])/risk
        lo=(entry-L[j])/risk if side>0 else (H[j]-entry)/risk
        mfe=max(mfe,hi); mae=max(mae,lo)
        if j==i:
            # C10: the limit fills partway through bar i. OHLC gives no intrabar
            # path, so the entry bar may trigger the STOP but never the target.
            if (L[j]<=st) if side>0 else (H[j]>=st):
                return dict(R=side*(st-entry)/risk-cost*entry/risk,bars=0,
                            mfe=mfe,mae=mae,exit="stop",risk_pct=risk/entry*100)
            continue
        if mode=="trail_atr":
            st = max(st,C[j-1]-trail_atr*A[j]) if side>0 else min(st,C[j-1]+trail_atr*A[j])
        elif mode=="trail_struct":
            lvl = ctx['S']['sl'][j] if side>0 else ctx['S']['sh'][j]
            if np.isfinite(lvl):
                st = max(st,lvl-0.25*A[j]) if side>0 else min(st,lvl+0.25*A[j])
        hs=(L[j]<=st) if side>0 else (H[j]>=st)
        ht=(tgt is not None) and ((H[j]>=tgt) if side>0 else (L[j]<=tgt))
        if hs: return dict(R=side*(st-entry)/risk-cost*entry/risk,bars=j-i,
                           mfe=mfe,mae=mae,exit="stop",risk_pct=risk/entry*100)
        if ht: return dict(R=side*(tgt-entry)/risk-cost*entry/risk,bars=j-i,
                           mfe=mfe,mae=mae,exit="target",risk_pct=risk/entry*100)
    j=min(i+maxb,n-1)
    return dict(R=side*(C[j]-entry)/risk-cost*entry/risk,bars=j-i,mfe=mfe,mae=mae,
                exit="time",risk_pct=risk/entry*100)
