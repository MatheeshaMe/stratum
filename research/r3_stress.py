#!/usr/bin/env python3
"""R-3 stress tests on the surviving candidate, before freezing.

  1  STOP SLIPPAGE. Stops fill during a reversal, often violently. The base
     model charges taker + half-spread; this charges explicit extra slippage.
  2  PARAMETER STABILITY. A broad plateau or nothing. Perturb lookback,
     tail depth, stop, target, horizon.
  3  LEVERAGE / RISK translation for the stated ~2% objective.
"""
import sys, os, pickle, itertools, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import situations as S
from r3_causal import trail_q, block_ci, path, BPS, MAKER, TAKER, HALF, HMAX

def setup():
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
    return rows,b,st,O,ent5,idx5,c,atrp

def signal(c, atrp, idx5, k, q):
    r=np.concatenate([[np.nan]*k,(c[k:]-c[:-k])/c[:-k]])/np.where(atrp==0,np.nan,atrp)
    rs=r[idx5]
    thi=trail_q(rs,1-q); tlo=trail_q(rs,q)
    return (np.isfinite(rs)&np.isfinite(thi)&(rs>=thi),
            np.isfinite(rs)&np.isfinite(tlo)&(rs<=tlo))

def evaluate(rows,O,ent5,mL,mS,stop,tgt,slip_bps=0.0,spread=1.0,delay=0):
    eL=ent5[mL]; eS=ent5[mS]
    rl,wl,ll=path(rows,eL,O[eL+1],+1,stop,tgt,spread=spread,delay=delay)
    rs,ws,ls=path(rows,eS,O[eS+1],-1,stop,tgt,spread=spread,delay=delay)
    # extra slippage charged only on stop exits
    rl=rl-np.where(ll, slip_bps*BPS, 0.0); rs=rs-np.where(ls, slip_bps*BPS, 0.0)
    return np.concatenate([rl,rs])

def main():
    rows,b,st,O,ent5,idx5,c,atrp=setup()
    days=len(ent5)/288
    K,Q,ST,TG = 6,0.01,0.005,0.0075
    mL,mS=signal(c,atrp,idx5,K,Q)

    print("1  STOP SLIPPAGE STRESS (1% tail, fill open[i+1])")
    print(f"  {'extra slippage on stop exits':<34}{'EV %':>10}{'  95% CI':>22}")
    for sl in (0,2,5,10,20,40):
        comb=evaluate(rows,O,ent5,mL,mS,ST,TG,slip_bps=sl)
        lo,hi=block_ci(comb)
        flag="  <<<" if lo>0 else ""
        print(f"  {f'+{sl} bps':<34}{comb.mean()*100:>+10.4f}   [{lo*100:+.4f},{hi*100:+.4f}]{flag}")

    print("\n2  PARAMETER STABILITY -- plateau or nothing (EV %, causal, open[i+1])")
    print(f"  {'lookback':<10}" + "".join(f"{f'q={q*100:g}%':>11}" for q in (0.02,0.01,0.005,0.002)))
    for k in (3,6,12,18):
        row=f"  {k*5:>4}m{'':<5}"
        for q in (0.02,0.01,0.005,0.002):
            a,bb=signal(c,atrp,idx5,k,q)
            comb=evaluate(rows,O,ent5,a,bb,ST,TG)
            row+=f"{comb.mean()*100:>+11.4f}"
        print(row)
    print(f"\n  {'stop/target grid at 30m/1%':<20}" +
          "".join(f"{f'tgt {t*100:g}%':>12}" for t in (0.005,0.0075,0.01,0.015)))
    for s in (0.003,0.005,0.0075,0.010):
        row=f"  stop {s*100:>4.2f}%{'':<7}"
        for t in (0.005,0.0075,0.01,0.015):
            comb=evaluate(rows,O,ent5,mL,mS,s,t)
            row+=f"{comb.mean()*100:>+12.4f}"
        print(row)

    print("\n3  LEVERAGE / RISK TRANSLATION for the ~2% objective")
    comb=evaluate(rows,O,ent5,mL,mS,ST,TG)
    ev=comb.mean(); sd=comb.std()
    print(f"  per-trade on NOTIONAL: EV {ev*100:+.4f}%  sd {sd*100:.4f}%  "
          f"{len(comb)/days:.2f} trades/day")
    print(f"  {'leverage':>9}{'win=+':>9}{'loss=-':>9}{'EV/trade':>10}{'EV/day':>9}"
          f"{'maxDD':>9}{'liq dist':>10}  note")
    for lev in (1,2,2.67,4,6,10):
        win=TG*lev*100; loss=ST*lev*100; evm=ev*lev*100
        eq=np.cumsum(comb*lev); pk=np.maximum.accumulate(eq); dd=(pk-eq).max()*100
        liq=100/lev*0.5      # rough: maintenance ~half of initial at max leverage
        note=""
        if ST*lev > 0.4*(liq/100): note="stop too close to liquidation"
        if dd>50: note="drawdown unacceptable"
        print(f"  {lev:>9.2f}{win:>9.2f}%{loss:>9.2f}%{evm:>+10.4f}%"
              f"{evm*len(comb)/days:>+9.3f}%{dd:>9.1f}%{liq:>9.1f}%  {note}")
    print("\n  A winning trade returns ~2% on margin at ~2.7x leverage, which keeps")
    print("  the 0.5% stop far from liquidation. Leverage is an OUTPUT of the")
    print("  barrier geometry here, not a dial turned to reach the target.")

if __name__=="__main__":
    main()
