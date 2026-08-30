#!/usr/bin/env python3
"""R-3 final evaluation of the momentum candidate with C5 fixed.

Exit cost is derived from the REALISED outcome mix, per cell, not assumed:
    target hit   -> passive limit exit   (maker)
    stop hit     -> taker
    unresolved   -> taker at the horizon
A momentum entry cannot rest passively (price is running away), so entry is
always taker.

Also adds the spread-widening sensitivity that a fixed-bps model hides: the
candidate's entire effect lives in the high-volatility tercile, which is exactly
where the real spread is widest.
"""
import sys, os, pickle, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import situations as S, r3_paths as P

BPS=1/1e4; MAKER=1.5; TAKER=4.5; HALFSPREAD=0.63

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
    rows=pickle.load(open("data/explore_r1.pkl","rb"))
    b=S.agg(rows,5); st=S.situations(b); n5=len(b['c'])
    entry=b['i1m'][(b['i1m']>60)&(b['i1m']<len(rows)-P.HMAX-2)]
    idx5=np.where(np.isin(b['i1m'],entry))[0]
    c=b['c']; atrp=st['A']/c
    def ret(k):
        r=np.concatenate([[np.nan]*k,(c[k:]-c[:-k])/c[:-k]])
        return r/np.where(atrp==0,np.nan,atrp)
    FP={s:P.first_passage(rows,entry,side=s) for s in (+1,-1)}
    MO={s:P.markout(rows,entry,120) for s in (+1,-1)}

    def evaluate(side, mask, s, t, spread_mult=1.0):
        tp,sl=FP[side]; si=list(P.STOPS).index(s/100); ti=list(P.TARGETS).index(t/100)
        w,l,u,_=P.score_cell(tp,sl,MO[side],si,ti,120,side,s/100,t/100,0.0)
        gross=np.where(w,t/100,np.where(l,-s/100,side*MO[side]))
        hs=HALFSPREAD*spread_mult
        entry_c=(TAKER+hs)*BPS                       # momentum entry must cross
        exit_c=np.where(w, MAKER*BPS, (TAKER+hs)*BPS)  # only the target rests
        net=gross-entry_c-exit_c
        return net[mask], w[mask].mean(), l[mask].mean(), u[mask].mean()

    print("R-3 FINAL -- momentum candidate, exit cost from the realised outcome mix (C5)\n")
    print(f"{'lookback/decile':<18}{'stop/tgt':<12}{'n':>8}{'P(tgt)':>8}{'P(stop)':>8}"
          f"{'P(unres)':>9}{'exit bps':>10}{'EV %':>10}{'  95% CI':>22}")
    rows_out=[]
    for k,dq in ((3,0.05),(6,0.05),(6,0.10),(12,0.10)):
        rk=ret(k)[idx5]
        l_,h_=np.nanquantile(rk,dq),np.nanquantile(rk,1-dq)
        ml=np.isfinite(rk)&(rk>=h_); ms=np.isfinite(rk)&(rk<=l_)
        for s,t in ((0.50,0.75),(1.00,1.00)):
            rl,wl,ll,ul=evaluate(+1,ml,s,t); rs,ws,ls,us=evaluate(-1,ms,s,t)
            comb=np.concatenate([rl,rs]); lo,hi=block_ci(comb)
            pw=(wl+ws)/2; ex=(pw*MAKER+(1-pw)*(TAKER+HALFSPREAD))
            flag="  <<<" if lo>0 else ""
            print(f"{f'{k*5}m / {int(dq*100)}%':<18}{f'{s}/{t}':<12}{len(comb):>8,}"
                  f"{pw:>8.1%}{(ll+ls)/2:>8.1%}{(ul+us)/2:>9.1%}{ex:>10.2f}"
                  f"{comb.mean()*100:>+10.4f}   [{lo*100:+.4f},{hi*100:+.4f}]{flag}")
            rows_out.append((k,dq,s,t,comb.mean()))

    print("\nSPREAD SENSITIVITY -- the effect lives in the high-vol tercile, where the")
    print("real spread is widest. Fixed-bps cost models hide this.")
    rk=ret(6)[idx5]; l_,h_=np.nanquantile(rk,0.10),np.nanquantile(rk,0.90)
    ml=np.isfinite(rk)&(rk>=h_); ms=np.isfinite(rk)&(rk<=l_)
    print(f"  {'spread assumption':<34}{'EV %':>10}{'  95% CI':>22}")
    for mult,lbl in ((1.0,"1x measured (0.63 bps half)"),
                     (2.0,"2x  (high-vol widening)"),
                     (3.0,"3x  (stressed book)")):
        rl,_,_,_=evaluate(+1,ml,0.50,0.75,mult); rs,_,_,_=evaluate(-1,ms,0.50,0.75,mult)
        comb=np.concatenate([rl,rs]); lo,hi=block_ci(comb)
        print(f"  {lbl:<34}{comb.mean()*100:>+10.4f}   [{lo*100:+.4f},{hi*100:+.4f}]")

    print("\nOPPORTUNITY FREQUENCY vs the stated objective (0-3 per day)")
    days=len(entry)/288
    for dq in (0.10,0.05,0.01,0.002):
        rk=ret(6)[idx5]; l_,h_=np.nanquantile(rk,dq),np.nanquantile(rk,1-dq)
        ml=np.isfinite(rk)&(rk>=h_); ms=np.isfinite(rk)&(rk<=l_)
        rl,_,_,_=evaluate(+1,ml,0.50,0.75); rs,_,_,_=evaluate(-1,ms,0.50,0.75)
        comb=np.concatenate([rl,rs]); lo,hi=block_ci(comb)
        print(f"  decile {dq*100:>5.1f}%  {len(comb)/days:>6.1f} trades/day  "
              f"EV {comb.mean()*100:>+8.4f}%  CI [{lo*100:+.4f},{hi*100:+.4f}]")

if __name__=="__main__":
    main()
