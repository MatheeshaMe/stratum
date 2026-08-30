#!/usr/bin/env python3
"""PHASE 3 -- where is the actual entry moment?

Prior work measured MFE/MAE from arbitrary bars and from the breakout bar, and
found the ratio pinned near 1.0. That was never tested from an OPTIMISED entry.
A retest entry buys lower, which should mechanically shrink MAE. If structural
information is monetizable anywhere, it is here.

Nine entry variants per BOS event. Every one is measured as EV PER OPPORTUNITY
(a variant that never triggers scores 0 for that opportunity), so selectivity
cannot flatter itself.
"""
import sys, os, pickle, numpy as np
sys.path.insert(0,'research/struct'); sys.path.insert(0,'research/btc3')
import zigzag as Z, events as E

MAKER=1.5/1e4; TAKER=4.5/1e4; HALF=0.63/1e4
TAKER_ALL=(TAKER+HALF)*2
MAKER_IN=(MAKER)+(TAKER+HALF)

def load5(path):
    T,O,H,L,C,V,N=E.load(path)
    ms=5*60000; key=T-(T%ms)
    _,st=np.unique(key,return_index=True); st=np.sort(st); en=np.append(st[1:],len(T))
    b=dict(t=key[st],o=O[st],h=np.maximum.reduceat(H,st),l=np.minimum.reduceat(L,st),
           c=C[en-1],v=np.add.reduceat(V,st))
    A=Z.atr(b['h'],b['l'],b['c'])
    piv=Z.zigzag(b['h'],b['l'],A,theta=3.0)
    S=Z.structure_state(len(b['c']),piv); D=Z.derived(b['c'],b['h'],b['l'],A,S)
    return b,A,S,D

def structural_trade(b,A,S,side,ent_i,entry_px,buf=0.25,maxb=2000,cost=TAKER_ALL):
    """Structural stop + unbounded trailing structural exit. Returns (R, bars, mfe, mae)."""
    n=len(b['c']); O,H,L,C=b['o'],b['h'],b['l'],b['c']
    stop = (S['last_sl'][ent_i]-buf*A[ent_i]) if side>0 else (S['last_sh'][ent_i]+buf*A[ent_i])
    if not np.isfinite(stop): return None
    risk=abs(entry_px-stop)
    if risk<=0 or risk/entry_px<0.0015 or risk/entry_px>0.08: return None
    for j in range(ent_i+1, min(ent_i+1+maxb,n)):
        if side>0 and np.isfinite(S['last_sl'][j]): stop=max(stop,S['last_sl'][j]-buf*A[j])
        if side<0 and np.isfinite(S['last_sh'][j]): stop=min(stop,S['last_sh'][j]+buf*A[j])
        if (side>0 and L[j]<=stop) or (side<0 and H[j]>=stop):
            ex,exi=stop,j; break
    else:
        exi=min(ent_i+maxb,n-1); ex=C[exi]
    g=side*(ex-entry_px)/risk
    mfe=(H[ent_i+1:exi+1].max()-entry_px)/risk if side>0 else (entry_px-L[ent_i+1:exi+1].min())/risk
    mae=(entry_px-L[ent_i+1:exi+1].min())/risk if side>0 else (H[ent_i+1:exi+1].max()-entry_px)/risk
    return (g-cost*entry_px/risk, exi-ent_i, mfe, mae)

def run_variants(b,A,S,D,W=24,cost=TAKER_ALL):
    n=len(b['c']); c,h,l,o=b['c'],b['h'],b['l'],b['o']
    lsh,lsl=S['last_sh'],S['last_sl']
    up=(S['trend']==1); dn=(S['trend']==-1)
    bu=(c>lsh); bu[1:]&=~(c[:-1]>lsh[:-1])
    bd=(c<lsl); bd[1:]&=~(c[:-1]<lsl[:-1])
    events=[(i,+1) for i in np.where(up&bu)[0]]+[(i,-1) for i in np.where(dn&bd)[0]]
    events=[(i,s) for i,s in events if 200<i<n-2100]
    events.sort()
    out={k:[] for k in "ABCDEFGHI"}
    for i,side in events:
        lvl=lsh[i] if side>0 else lsl[i]
        if not np.isfinite(lvl) or not np.isfinite(A[i]): continue
        a=A[i]
        # A immediate: next bar open
        out['A'].append(structural_trade(b,A,S,side,i,o[i+1],cost=cost))
        # B breakout close (same bar close, filled next open -- identical fill, kept for parity)
        out['B'].append(structural_trade(b,A,S,side,i,o[i+1],cost=cost))
        # C first continuation candle: next bar closes further in direction
        j=i+1
        if j<n-1 and side*(c[j]-c[i])>0: out['C'].append(structural_trade(b,A,S,side,j,o[j+1],cost=cost))
        else: out['C'].append(None)
        # D retest of the breakout level within W bars
        hit=None
        for j in range(i+1,min(i+1+W,n-1)):
            if (side>0 and l[j]<=lvl) or (side<0 and h[j]>=lvl): hit=j; break
        out['D'].append(structural_trade(b,A,S,side,hit,lvl,cost=cost) if hit else None)
        # E retest + rejection: after the retest, a bar closes back through in direction
        if hit:
            rej=None
            for j in range(hit,min(hit+W,n-1)):
                if side*(c[j]-lvl)>0: rej=j; break
            out['E'].append(structural_trade(b,A,S,side,rej,o[rej+1],cost=cost) if rej else None)
        else: out['E'].append(None)
        # F new structural extreme after the breakout
        f=None
        for j in range(i+1,min(i+1+W*3,n-1)):
            if side>0 and np.isfinite(lsh[j]) and lsh[j]>lvl: f=j; break
            if side<0 and np.isfinite(lsl[j]) and lsl[j]<lvl: f=j; break
        out['F'].append(structural_trade(b,A,S,side,f,o[f+1],cost=cost) if f else None)
        # G momentum acceleration: 3-bar velocity exceeds the breakout bar's
        g=None
        v0=abs(c[i]-c[i-3])/a if i>3 else 0
        for j in range(i+1,min(i+1+W,n-1)):
            if side*(c[j]-c[j-3])/a > max(v0,1.0): g=j; break
        out['G'].append(structural_trade(b,A,S,side,g,o[g+1],cost=cost) if g else None)
        # H second structural confirmation: trend still intact and a further BOS
        hh=None
        for j in range(i+1,min(i+1+W*3,n-1)):
            if side>0 and up[j] and bu[j]: hh=j; break
            if side<0 and dn[j] and bd[j]: hh=j; break
        out['H'].append(structural_trade(b,A,S,side,hh,o[hh+1],cost=cost) if hh else None)
        # I volatility-adaptive: wait for a pullback of 0.5 ATR from the extreme
        ii=None; ext=c[i]
        for j in range(i+1,min(i+1+W,n-1)):
            ext = max(ext,h[j]) if side>0 else min(ext,l[j])
            if side>0 and l[j]<=ext-0.5*a: ii=j; break
            if side<0 and h[j]>=ext+0.5*a: ii=j; break
        out['I'].append(structural_trade(b,A,S,side,ii,o[ii+1],cost=cost) if ii else None)
    return out, len(events)

if __name__=="__main__":
    b,A,S,D=load5("data/spot/BTCUSDT-1m.pkl")
    print(f"BTC 5m bars {len(b['c']):,}")
    res,nev=run_variants(b,A,S,D)
    print(f"BOS events (trend-aligned): {nev:,}\n")
    NAMES={'A':'immediate (next open)','B':'breakout close','C':'first continuation candle',
           'D':'retest of level','E':'retest + rejection','F':'new structural extreme',
           'G':'momentum acceleration','H':'second structural confirmation',
           'I':'0.5 ATR pullback (adaptive)'}
    print(f"{'variant':<32}{'fill%':>7}{'n':>7}{'win%':>7}{'EV/trade':>10}"
          f"{'EV/opp':>9}{'medMFE':>8}{'medMAE':>8}{'MFE/MAE':>9}{'PF':>7}{'maxR':>7}")
    def boot(R,it=3000):
        rg=np.random.default_rng(0)
        return tuple(np.percentile([rg.choice(R,len(R)).mean() for _ in range(it)],[2.5,97.5]))
    for k in "ACDEFGHI":
        tr=[x for x in res[k] if x]
        if len(tr)<50: print(f"{NAMES[k]:<32} too few"); continue
        R=np.array([t[0] for t in tr]); MFE=np.array([t[2] for t in tr]); MAE=np.array([t[3] for t in tr])
        w=R>0; pf=R[w].sum()/max(-R[~w].sum(),1e-9)
        lo,hi=boot(R)
        flag="  <<<" if lo>0 else ""
        print(f"{NAMES[k]:<32}{len(tr)/len(res[k]):>7.0%}{len(tr):>7}{w.mean():>7.1%}"
              f"{R.mean():>+10.3f}{R.sum()/len(res[k]):>+9.3f}{np.median(MFE):>8.2f}"
              f"{np.median(MAE):>8.2f}{np.median(MFE)/max(np.median(MAE),1e-9):>9.2f}"
              f"{pf:>7.2f}{R.max():>7.1f}{flag}")
    pickle.dump(res,open("/tmp/p3_entry.pkl","wb"))
