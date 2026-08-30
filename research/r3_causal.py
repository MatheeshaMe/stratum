#!/usr/bin/env python3
"""R-3 final -- momentum candidate with C6 fixed (trailing threshold) plus the
full validation battery. Everything here is causal: the decision to trade at t
uses only data before t.
"""
import sys, os, pickle, itertools, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import situations as S

BPS=1/1e4; MAKER=1.5; TAKER=4.5; HALF=0.63; HMAX=120; WIN=8640   # 30d trailing

def block_ci(x, block=288, iters=1000, seed=0):
    rng=np.random.default_rng(seed); n=len(x)
    if n<block*3: return (np.nan,np.nan)
    nb=int(np.ceil(n/block)); m=np.empty(iters)
    for k in range(iters):
        st=rng.integers(0,n,nb)
        s=np.concatenate([np.take(x,np.arange(i,i+block),mode='wrap') for i in st])[:n]
        m[k]=s.mean()
    return np.percentile(m,2.5),np.percentile(m,97.5)

def trail_q(x, q, win=WIN, step=288):
    """Trailing empirical quantile using ONLY past data. Refreshed daily."""
    out=np.full(len(x), np.nan)
    for a in range(win, len(x), step):
        w=x[a-win:a]; w=w[np.isfinite(w)]
        if len(w)<1000: continue
        out[a:a+step]=np.nanquantile(w,q)
    return out

def path(rows, ent, fill, side, stop, target, spread=1.0, delay=0):
    H,L,C = path.H, path.L, path.C
    off=np.arange(1+delay,HMAX+1); idx=ent[:,None]+off[None,:]; px=fill[:,None]
    rh=np.maximum.accumulate(H[idx],1)/px; rl=np.minimum.accumulate(L[idx],1)/px
    if side>0: up,dn,ul,dl=rh,rl,1+target,1-stop
    else:      up,dn,ul,dl=rl,rh,1-target,1+stop
    uh=(up>=ul) if side>0 else (up<=ul); dh=(dn<=dl) if side>0 else (dn>=dl)
    N=10**6
    ut=np.where(uh.any(1),uh.argmax(1),N); dt=np.where(dh.any(1),dh.argmax(1),N)
    w=(ut<N)&(ut<dt); l=(dt<N)&~w
    end=C[np.minimum(ent+HMAX,len(C)-1)]
    g=np.where(w,target,np.where(l,-stop,side*(end/fill-1)))
    hs=HALF*spread
    return g-(TAKER+hs)*BPS-np.where(w,MAKER*BPS,(TAKER+hs)*BPS), w, l

def main():
    rows=pickle.load(open("data/explore_r1.pkl","rb"))
    b=S.agg(rows,5); st=S.situations(b)
    O=np.array([r[1] for r in rows]); path.H=np.array([r[2] for r in rows])
    path.L=np.array([r[3] for r in rows]); path.C=np.array([r[4] for r in rows])
    # C7: signal is the CLOSE of 5m bar k -> last 1m bar of that 5m bar
    _end=b['i1m'][1:]-1
    _ok=(_end>60)&(_end<len(rows)-HMAX-5)
    ent5=_end[_ok]
    idx5=np.arange(len(b['c'])-1)[_ok]
    c=b['c']; atrp=st['A']/c
    r6=np.concatenate([[np.nan]*6,(c[6:]-c[:-6])/c[:-6]])/np.where(atrp==0,np.nan,atrp)
    r6s=r6[idx5]; days=len(ent5)/288
    S_,T_=0.005,0.0075
    print("R-3 CAUSAL -- trailing 30d threshold (C6 fixed), fill at open[i+1]\n")
    print(f"{'tail':<10}{'trades/day':>12}{'n':>8}{'P(tgt)':>8}{'EV %':>10}"
          f"{'  95% CI':>22}{'  1stH':>9}{'2ndH':>9}")
    keep={}
    for q,lbl in ((0.05,"5%"),(0.01,"1%"),(0.002,"0.2%")):
        thi=trail_q(r6s,1-q); tlo=trail_q(r6s,q)
        mL=np.isfinite(r6s)&np.isfinite(thi)&(r6s>=thi)
        mS=np.isfinite(r6s)&np.isfinite(tlo)&(r6s<=tlo)
        eL=ent5[mL]; eS=ent5[mS]
        rl,wl,_=path(rows,eL,O[eL+1],+1,S_,T_); rs,ws,_=path(rows,eS,O[eS+1],-1,S_,T_)
        comb=np.concatenate([rl,rs]); lo,hi=block_ci(comb)
        pos=np.concatenate([np.where(mL)[0],np.where(mS)[0]]); half=len(idx5)//2
        h1=comb[pos<half]; h2=comb[pos>=half]
        flag="  <<<" if lo>0 else ""
        print(f"{lbl:<10}{len(comb)/days:>12.2f}{len(comb):>8,}"
              f"{(wl.mean()+ws.mean())/2:>8.1%}{comb.mean()*100:>+10.4f}"
              f"   [{lo*100:+.4f},{hi*100:+.4f}]{h1.mean()*100:>+9.4f}"
              f"{h2.mean()*100:>+9.4f}{flag}")
        keep[lbl]=(comb,pos,mL,mS,eL,eS)

    comb,pos,mL,mS,eL,eS = keep["1%"]
    print(f"\nREGIME (1% tail, causal)")
    volp=np.full(len(c),np.nan)
    for i in range(2016,len(c)): volp[i]=(atrp[i-2016:i]<atrp[i]).mean()
    vp=volp[idx5]; hour=((b['t']//3600000)%24)[idx5]
    allm=mL|mS
    for lbl,sel in (("vol low",vp<0.33),("vol mid",(vp>=0.33)&(vp<0.67)),
                    ("vol high",vp>=0.67),("US 13-21z",np.isin(hour,range(13,21))),
                    ("Asia 0-8z",np.isin(hour,range(0,8)))):
        mm=allm&np.isfinite(vp)&sel
        eLl=ent5[mL&sel&np.isfinite(vp)]; eSs=ent5[mS&sel&np.isfinite(vp)]
        if len(eLl)+len(eSs)<400: continue
        rl,_,_=path(rows,eLl,O[eLl+1],+1,S_,T_); rs,_,_=path(rows,eSs,O[eSs+1],-1,S_,T_)
        cc=np.concatenate([rl,rs]); lo,hi=block_ci(cc)
        print(f"  {lbl:<12}n={len(cc):>6,}  EV {cc.mean()*100:>+8.4f}%  "
              f"CI [{lo*100:+.4f},{hi*100:+.4f}]")

    print(f"\nCONCENTRATION (1% tail): are these trades a few episodes?")
    ts=b['t'][idx5]; sel=np.where(mL|mS)[0]
    dayk=(ts[sel]//86400000)
    import collections
    cnt=collections.Counter(dayk); top5=sum(v for _,v in cnt.most_common(5))
    print(f"  {len(sel):,} trades on {len(cnt):,} distinct days; "
          f"top-5 days hold {top5/len(sel):.1%}")

    print(f"\nTRADE PROFILE (1% tail, causal, open[i+1] fill)")
    eq=np.cumsum(comb); pk=np.maximum.accumulate(eq); dd=pk-eq
    ls=[len(list(g)) for k,g in itertools.groupby(comb>0) if not k]
    print(f"  EV/trade {comb.mean()*100:+.4f}%  sd {comb.std()*100:.4f}%  "
          f"Sharpe/trade {comb.mean()/comb.std():.4f}")
    print(f"  cum {eq[-1]*100:+.1f}% over {len(comb):,} trades  maxDD {dd.max()*100:.1f}%  "
          f"longest losing streak {max(ls) if ls else 0}")
    t=comb.mean()/(comb.std()/np.sqrt(len(comb)))
    print(f"  t-stat {t:.2f} (naive, ignores overlap)")

if __name__=="__main__":
    main()
