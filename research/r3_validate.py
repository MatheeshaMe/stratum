#!/usr/bin/env python3
"""R-3 validation battery for the one surviving candidate: short-term momentum.

The candidate: after a 30m move in the top/bottom decile, trade in the SAME
direction with a wide barrier pair.

The obvious threat first. A momentum entry is taken at the close of a bar that
has just moved sharply in your direction. You cannot rest a passive limit there
and expect a fill -- price is running away from you. So the maker/taker cost
used in the search is almost certainly wrong for THIS state. The honest
assumption is TAKER ENTRY.

Battery:
  1  cost sensitivity, four execution scenarios
  2  split-half replication
  3  parameter stability (lookback and threshold)
  4  regime stability (volatility tercile, session)
  5  opportunity frequency and drawdown
"""
import sys, os, pickle, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import situations as S, r3_paths as P

BPS = 1/1e4
SCEN = {
 "maker in / maker out  (optimistic)": (1.5, 1.5, 0.0),
 "maker in / taker out  (search used)": (1.5, 4.5, 0.63),
 "TAKER in / maker out  (realistic)":  (4.5+0.63, 1.5, 0.0),
 "TAKER in / TAKER out  (conservative)":(4.5+0.63, 4.5, 0.63),
}
def cost_of(sc): a,b,c = SCEN[sc]; return (a+b+c)*BPS

def block_ci(x, block=288, iters=1200, seed=0):
    rng=np.random.default_rng(seed); n=len(x)
    if n<block*3: return (np.nan,np.nan)
    nb=int(np.ceil(n/block)); m=np.empty(iters)
    for k in range(iters):
        st=rng.integers(0,n,nb)
        s=np.concatenate([np.take(x,np.arange(i,i+block),mode='wrap') for i in st])[:n]
        m[k]=s.mean()
    return np.percentile(m,2.5),np.percentile(m,97.5)

def main():
    rows = pickle.load(open("data/explore_r1.pkl","rb"))
    b = S.agg(rows,5); st = S.situations(b); n5=len(b['c'])
    entry = b['i1m'][(b['i1m']>60)&(b['i1m']<len(rows)-P.HMAX-2)]
    idx5 = np.where(np.isin(b['i1m'], entry))[0]
    c=b['c']; A=st['A']; atrp=A/c

    def ret(k):
        r=np.concatenate([[np.nan]*k,(c[k:]-c[:-k])/c[:-k]])
        return r/np.where(atrp==0,np.nan,atrp)

    FP={}; MO={}
    for side in (+1,-1):
        FP[side]=P.first_passage(rows, entry, side=side)
        MO[side]=P.markout(rows, entry, 120)

    def ev(side, mask, s, t, cost):
        tp,sl=FP[side]; si=list(P.STOPS).index(s/100); ti=list(P.TARGETS).index(t/100)
        w,l,u,r=P.score_cell(tp,sl,MO[side],si,ti,120,side,s/100,t/100,cost)
        return r[mask], w[mask].mean(), u[mask].mean()

    S_, T_ = 0.50, 0.75
    r6 = ret(6)[idx5]
    lo,hi = np.nanquantile(r6,0.10), np.nanquantile(r6,0.90)
    mL = np.isfinite(r6)&(r6>=hi); mS = np.isfinite(r6)&(r6<=lo)

    print(f"CANDIDATE: 30m momentum decile, stop {S_}% / target {T_}%, horizon 120m")
    print(f"  LONG  n={mL.sum():,}   SHORT n={mS.sum():,}   "
          f"({(mL.sum()+mS.sum())/ (len(entry)/288):.2f} opportunities/day)\n")
    print("1  COST SENSITIVITY")
    print(f"  {'scenario':<38}{'RT bps':>8}{'LONG EV%':>11}{'SHORT EV%':>11}{'combined':>11}{'  95% CI combined':>22}")
    for sc in SCEN:
        cst=cost_of(sc)
        rl,_,_ = ev(+1,mL,S_,T_,cst); rs,_,_ = ev(-1,mS,S_,T_,cst)
        comb=np.concatenate([rl,rs])
        lo2,hi2=block_ci(comb)
        flag = "  <<<" if lo2>0 else ""
        print(f"  {sc:<38}{cst*1e4:>8.2f}{rl.mean()*100:>+11.4f}{rs.mean()*100:>+11.4f}"
              f"{comb.mean()*100:>+11.4f}   [{lo2*100:+.4f},{hi2*100:+.4f}]{flag}")

    cst = cost_of("TAKER in / maker out  (realistic)")
    print(f"\n2  SPLIT-HALF REPLICATION (realistic cost, taker in / maker out)")
    half=len(idx5)//2
    for lbl,sel in (("1st half",np.arange(len(idx5))<half),("2nd half",np.arange(len(idx5))>=half)):
        rl,_,_=ev(+1,mL&sel,S_,T_,cst); rs,_,_=ev(-1,mS&sel,S_,T_,cst)
        comb=np.concatenate([rl,rs]); l2,h2=block_ci(comb)
        print(f"  {lbl:<12}n={len(comb):>7,}  EV {comb.mean()*100:>+8.4f}%  "
              f"CI [{l2*100:+.4f},{h2*100:+.4f}]")

    print(f"\n3  PARAMETER STABILITY (realistic cost). Broad stable region or nothing.")
    print(f"  {'lookback':<12}{'decile':<10}" + "".join(f"{f'{s}/{t}':>11}" for s,t in
          [(0.40,0.50),(0.50,0.50),(0.50,0.75),(0.75,0.75),(1.00,1.00)]))
    for k in (3,6,12,24):
        rk=ret(k)[idx5]
        for dq in (0.05,0.10,0.20):
            l_,h_=np.nanquantile(rk,dq),np.nanquantile(rk,1-dq)
            ml=np.isfinite(rk)&(rk>=h_); ms=np.isfinite(rk)&(rk<=l_)
            row=f"  {k*5:>4}m{'':<7}{int(dq*100):>3}%{'':<6}"
            for s,t in [(0.40,0.50),(0.50,0.50),(0.50,0.75),(0.75,0.75),(1.00,1.00)]:
                rl,_,_=ev(+1,ml,s,t,cst); rs,_,_=ev(-1,ms,s,t,cst)
                row+=f"{np.concatenate([rl,rs]).mean()*100:>+11.4f}"
            print(row)

    print(f"\n4  REGIME STABILITY (realistic cost, {S_}/{T_})")
    volp=np.full(n5,np.nan)
    for i in range(2016,n5): volp[i]=(atrp[i-2016:i]<atrp[i]).mean()
    vp=volp[idx5]; hour=((b['t']//3600000)%24)[idx5]
    REG=[("vol tercile low",np.isfinite(vp)&(vp<0.33)),
         ("vol tercile mid",np.isfinite(vp)&(vp>=0.33)&(vp<0.67)),
         ("vol tercile high",np.isfinite(vp)&(vp>=0.67)),
         ("US 13-21z",np.isin(hour,range(13,21))),
         ("Asia 0-8z",np.isin(hour,range(0,8)))]
    for lbl,sel in REG:
        rl,_,_=ev(+1,mL&sel,S_,T_,cst); rs,_,_=ev(-1,mS&sel,S_,T_,cst)
        comb=np.concatenate([rl,rs]); l2,h2=block_ci(comb)
        print(f"  {lbl:<18}n={len(comb):>7,}  EV {comb.mean()*100:>+8.4f}%  "
              f"CI [{l2*100:+.4f},{h2*100:+.4f}]")

    print(f"\n5  TRADE PROFILE (realistic cost)")
    rl,wl,ul=ev(+1,mL,S_,T_,cst); rs,ws,us=ev(-1,mS,S_,T_,cst)
    comb=np.concatenate([rl,rs])
    eq=np.cumsum(comb); pk=np.maximum.accumulate(eq); dd=(pk-eq)
    import itertools
    losses=[len(list(g)) for k,g in itertools.groupby(comb>0) if not k]
    print(f"  P(target first) LONG {wl:.1%}  SHORT {ws:.1%}   unresolved {ul:.1%}/{us:.1%}")
    print(f"  EV/trade {comb.mean()*100:+.4f}%   sd {comb.std()*100:.4f}%")
    print(f"  total {eq[-1]*100:+.1f}% over {len(comb):,} trades; max DD {dd.max()*100:.1f}%")
    print(f"  longest losing streak {max(losses) if losses else 0}")

if __name__ == "__main__":
    main()
