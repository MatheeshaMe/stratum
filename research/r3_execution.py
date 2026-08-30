#!/usr/bin/env python3
"""R-3 execution realism -- the test that decides the momentum candidate.

The candidate's EV grows monotonically as the entry trigger gets more extreme:
+0.013% at the 5% tail, +0.085% at the 1% tail, +0.157% at the 0.2% tail. That
is either a real selectivity effect or an artifact of pricing fills at a print
you could never have traded.

The signal is computed at the CLOSE of bar i. You cannot be filled at that
price: the order is sent after the bar closes, into a market that is by
construction moving fast. So this re-prices every entry at progressively more
honest fills:

    close[i]        the search's assumption -- impossible
    open[i+1]       best realistic case, zero latency
    close[i+1]      one minute of chase
    close[i+2]      two minutes of chase

Barriers are measured from the ACTUAL fill, not from the signal print.
"""
import sys, os, pickle, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import situations as S

BPS=1/1e4; MAKER=1.5; TAKER=4.5; HALF=0.63
HMAX=120

def block_ci(x, block=288, iters=1000, seed=0):
    rng=np.random.default_rng(seed); n=len(x)
    if n<block*3: return (np.nan,np.nan)
    nb=int(np.ceil(n/block)); m=np.empty(iters)
    for k in range(iters):
        st=rng.integers(0,n,nb)
        s=np.concatenate([np.take(x,np.arange(i,i+block),mode='wrap') for i in st])[:n]
        m[k]=s.mean()
    return np.percentile(m,2.5),np.percentile(m,97.5)

def run_from(rows, ent, fill_px, side, stop, target, spread_mult=1.0, delay=0):
    """First passage measured from the ACTUAL fill price."""
    H=run_from.H; L=run_from.L; C=run_from.C
    off=np.arange(1+delay, HMAX+1)
    idx=ent[:,None]+off[None,:]
    px=fill_px[:,None]
    rh=np.maximum.accumulate(H[idx],axis=1)/px
    rl=np.minimum.accumulate(L[idx],axis=1)/px
    if side>0: up,dn,ul,dl = rh,rl,1+target,1-stop
    else:      up,dn,ul,dl = rl,rh,1-target,1+stop
    uh = (up>=ul) if side>0 else (up<=ul)
    dh = (dn<=dl) if side>0 else (dn>=dl)
    NEV=10**6
    ut=np.where(uh.any(1), uh.argmax(1), NEV)
    dt=np.where(dh.any(1), dh.argmax(1), NEV)
    w=(ut<NEV)&(ut<dt); l=(dt<NEV)&~w; u=~w&~l
    end=C[np.minimum(ent+HMAX,len(C)-1)]
    gross=np.where(w,target,np.where(l,-stop,side*(end/fill_px-1)))
    hs=HALF*spread_mult
    ec=(TAKER+hs)*BPS
    xc=np.where(w,MAKER*BPS,(TAKER+hs)*BPS)
    return gross-ec-xc, w.mean(), u.mean()

def main():
    rows=pickle.load(open("data/explore_r1.pkl","rb"))
    b=S.agg(rows,5); st=S.situations(b)
    O=np.array([r[1] for r in rows]); H=np.array([r[2] for r in rows])
    L=np.array([r[3] for r in rows]); C=np.array([r[4] for r in rows])
    run_from.H=H; run_from.L=L; run_from.C=C
    # C7: signal is the CLOSE of 5m bar k -> last 1m bar of that 5m bar
    _end=b['i1m'][1:]-1
    _ok=(_end>60)&(_end<len(rows)-HMAX-5)
    ent5=_end[_ok]
    idx5=np.arange(len(b['c'])-1)[_ok]
    c=b['c']; atrp=st['A']/c
    r6=(np.concatenate([[np.nan]*6,(c[6:]-c[:-6])/c[:-6]])/np.where(atrp==0,np.nan,atrp))[idx5]
    days=len(ent5)/288
    S_,T_=0.005,0.0075

    FILLS=[("close[i]  (search assumption)", lambda e:C[e], 0),
           ("open[i+1] (zero-latency)",      lambda e:O[e+1], 0),
           ("close[i+1] (1 min chase)",      lambda e:C[e+1], 1),
           ("close[i+2] (2 min chase)",      lambda e:C[e+2], 2)]

    print("R-3 EXECUTION REALISM -- barriers measured from the actual fill\n")
    for dq,lbl in ((0.05,"5% tail"),(0.01,"1% tail"),(0.002,"0.2% tail")):
        lo_,hi_=np.nanquantile(r6,dq),np.nanquantile(r6,1-dq)
        mL=np.isfinite(r6)&(r6>=hi_); mS=np.isfinite(r6)&(r6<=lo_)
        nlt=(mL.sum()+mS.sum())/days
        print(f"  === {lbl}  ({nlt:.1f} trades/day) ===")
        print(f"  {'fill assumption':<32}{'P(tgt)':>8}{'EV %':>10}{'  95% CI':>22}")
        for flbl, fpx, dly in FILLS:
            eL=ent5[mL]; eS=ent5[mS]
            rl,wl,_=run_from(rows,eL,fpx(eL),+1,S_,T_,delay=dly)
            rs,ws,_=run_from(rows,eS,fpx(eS),-1,S_,T_,delay=dly)
            comb=np.concatenate([rl,rs]); lo2,hi2=block_ci(comb)
            flag="  <<<" if lo2>0 else ""
            print(f"  {flbl:<32}{(wl+ws)/2:>8.1%}{comb.mean()*100:>+10.4f}"
                  f"   [{lo2*100:+.4f},{hi2*100:+.4f}]{flag}")
        # spread stress at the honest fill
        eL=ent5[mL]; eS=ent5[mS]
        print(f"  {'spread stress @ open[i+1]':<32}")
        for mult in (1.0,2.0,4.0):
            rl,_,_=run_from(rows,eL,O[eL+1],+1,S_,T_,spread_mult=mult)
            rs,_,_=run_from(rows,eS,O[eS+1],-1,S_,T_,spread_mult=mult)
            comb=np.concatenate([rl,rs]); lo2,hi2=block_ci(comb)
            print(f"    {f'{mult:.0f}x spread':<30}{'':>8}{comb.mean()*100:>+10.4f}"
                  f"   [{lo2*100:+.4f},{hi2*100:+.4f}]")
        print()

if __name__=="__main__":
    main()
