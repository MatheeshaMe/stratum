#!/usr/bin/env python3
"""Second stop definition, declared as a POST-HOC attempt.

C11 showed the last-confirmed-pivot stop is the wrong invalidation for a sweep
reversal: the sweep's own extreme is not yet a confirmed pivot, so the level
used was stale. What a trader actually means by 'invalidated' here is:

    price accepts back beyond the extreme that was just swept.

So: stop = the sweep bar's high (short) / low (long) +/- buffer.

This is my SECOND stop specification for the same action, chosen after seeing
the first fail. That is a real degree of freedom and it is declared. The
holdout has not been consulted for this decision.
"""
import sys, os, pickle, numpy as np
sys.path.insert(0,'research/policy'); sys.path.insert(0,'research/btc3')
import engine as EN, events as E
from run_policy import prep, boot, ms, DISC, VALD, HELD

MK=EN.MAKER; TK=EN.TAKER; HF=EN.HALF; COST=(TK+HF)*2

def sweep_trades(b,ctx,lo,hi,buf=0.10,maxb=120,manage="target",entry_mode="next_open"):
    C,O,H,L=b['c'],b['o'],b['h'],b['l']; A=ctx['A']; n=len(C); out=[]
    for i in range(600,n-maxb-3):
        t=b['t'][i]
        if not (lo<=t<hi): continue
        for a in ("L_REV","S_REV"):
            trig=EN.action_trigger(a,b,ctx,i)
            if trig is None: continue
            side,_,_=trig
            ei,epx=(i+1,O[i+1]) if entry_mode=="next_open" else (i,C[i])
            # stop = beyond the swept extreme of bar i
            stop = (H[i]+buf*A[i]) if side<0 else (L[i]-buf*A[i])
            if side>0 and stop>=epx: continue
            if side<0 and stop<=epx: continue
            risk=abs(epx-stop)
            if risk<=0 or risk/epx<0.0015 or risk/epx>0.12: continue
            tgt=EN.next_liquidity(b,ctx,ei,side)
            if not np.isfinite(tgt): continue
            if side>0 and tgt<=epx: continue
            if side<0 and tgt>=epx: continue
            rr=abs(tgt-epx)/risk
            if rr<0.3 or rr>50: continue
            st=stop; res=None
            for j in range(ei,min(ei+1+maxb,n)):
                if j==ei:
                    if (L[j]<=st) if side>0 else (H[j]>=st):
                        res=(side*(st-epx)/risk-COST*epx/risk,0,"stop"); break
                    continue
                if manage=="trail":
                    lvl=ctx['S']['sl'][j] if side>0 else ctx['S']['sh'][j]
                    if np.isfinite(lvl):
                        cand=(lvl-0.25*A[j]) if side>0 else (lvl+0.25*A[j])
                        # C12: never move the stop to a level price has already
                        # passed -- it must stay beyond this bar's extreme.
                        if side>0 and cand<L[j]: st=max(st,cand)
                        if side<0 and cand>H[j]: st=min(st,cand)
                hs=(L[j]<=st) if side>0 else (H[j]>=st)
                ht=(H[j]>=tgt) if side>0 else (L[j]<=tgt)
                if hs: res=(side*(st-epx)/risk-COST*epx/risk,j-ei,"stop"); break
                if manage=="target" and ht:
                    res=(side*(tgt-epx)/risk-COST*epx/risk,j-ei,"target"); break
            if res is None:
                j=min(ei+maxb,n-1)
                res=(side*(C[j]-epx)/risk-COST*epx/risk,j-ei,"time")
            out.append((res[0],side,t,rr,res[1],1.0 if a=="S_REV" else 0.0))
    return np.array(out) if out else np.zeros((0,6))

def rep(lbl,R):
    if len(R)<25: print(f"  {lbl:<44}{len(R):>6}  too few"); return
    lo,hi=boot(R); w=R>0
    print(f"  {lbl:<44}{len(R):>6}{w.mean():>7.1%}{R.mean():>+9.3f}"
          f"   [{lo:+.3f},{hi:+.3f}]{R[w].sum()/max(-R[~w].sum(),1e-9):>7.2f}"
          f"{'  <<<' if lo>0 else ''}")

b,ctx=prep("data/spot/BTCUSDT-1m-full.pkl")
print("SWEEP-EXTREME STOP — BTC 1h, entry next open, target = next liquidity")
print(f"  {'window / side / management':<44}{'n':>6}{'win%':>7}{'EV R':>9}{'  95% CI':>22}{'PF':>7}")
for wl,W in (("discovery",DISC),("validation",VALD)):
    for mg in ("target","trail"):
        M=sweep_trades(b,ctx,*W,manage=mg)
        rep(f"{wl} both sides, {mg}",M[:,0])
        rep(f"{wl} S_REV only, {mg}",M[M[:,5]==1,0])
        rep(f"{wl} L_REV only, {mg}",M[M[:,5]==0,0])
    print()
print(f"  median R:R available (an OUTPUT, not an input): "
      f"{np.median(sweep_trades(b,ctx,*DISC)[:,3]):.2f}")
