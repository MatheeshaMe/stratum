#!/usr/bin/env python3
"""E6 -- $20 account simulation on the EMPIRICALLY MEASURED trade distribution,
plus the inverse question: what edge would each milestone require?"""
import numpy as np

COST=0.0663           # % of notional, maker-in / taker-out
TGT, STP = 0.30, 0.15 # BTC %, = +3% / -1.5% account at 10x
LEV=10; RR=TGT/STP
# measured on 205,014 entries, 2017-2026 spot, 4h limit, 1:2 r:r
P_WIN_MEAS = 0.327    # LONG; SHORT 0.334
MART = STP/(STP+TGT)  # 0.3333

def sim(p_win, n_trades, n_paths=20000, start=20.0, lev=LEV, seed=0,
        risk_frac=1.0, ruin=2.0):
    rng=np.random.default_rng(seed)
    win_ret=(TGT-COST)*lev/100*risk_frac
    los_ret=(-STP-COST)*lev/100*risk_frac
    eq=np.full(n_paths,start)
    peak=eq.copy(); mdd=np.zeros(n_paths); alive=np.ones(n_paths,bool)
    for _ in range(n_trades):
        w=rng.random(n_paths)<p_win
        eq=np.where(alive, eq*(1+np.where(w,win_ret,los_ret)), eq)
        peak=np.maximum(peak,eq); mdd=np.maximum(mdd,(peak-eq)/peak)
        alive&= eq>ruin
    return eq, mdd, alive

print("PER-TRADE ARITHMETIC AT 10x, 1:2 (target 0.30% BTC, stop 0.15% BTC)\n")
wr=(TGT-COST)*LEV; lr=(STP+COST)*LEV
print(f"  a WIN  returns  ({TGT}% - {COST}%) x {LEV} = {wr:+.3f}% of account")
print(f"  a LOSS returns  ({STP}% + {COST}%) x {LEV} = {-lr:+.3f}% of account")
print(f"  martingale P(win) = {MART:.1%}   measured P(win) = {P_WIN_MEAS:.1%}")
be=lr/(wr+lr)
print(f"  BREAKEVEN P(win) = {be:.1%}   -> shortfall = {be-P_WIN_MEAS:+.1%} points\n")
print(f"  net EV/trade = {P_WIN_MEAS*wr-(1-P_WIN_MEAS)*lr:+.4f}% of account")

print(f"\n\nMILESTONES -- trades required at various win rates (net of cost)\n")
MILE=[(20,25),(25,50),(50,100),(100,500),(500,1000),(1000,10000)]
print(f"  {'from -> to':<16}{'multiple':>10}" + "".join(f"{f'p={p:.0%}':>12}" for p in
      (0.327,0.36,0.40,0.45,0.50)))
for a,b in MILE:
    row=f"  ${a:,} -> ${b:,}".ljust(16)+f"{b/a:>9.1f}x"
    for p in (0.327,0.36,0.40,0.45,0.50):
        g=p*np.log(1+wr/100)+(1-p)*np.log(1-lr/100)
        row+= f"{np.log(b/a)/g:>12,.0f}" if g>0 else f"{'never':>12}"
    print(row)
print(f"\n  'never' = negative log-growth; the account decays regardless of how long you trade.")
print(f"  Measured p = 32.7%. Breakeven p = {be:.1%}. Every measured cell is in the 'never' column.")

print(f"\n\nSIMULATION on the MEASURED distribution ($20 start, 10x, full size)\n")
for lbl,p in (("measured (32.7%)",0.327),("+2pp optimism",0.347),
              ("breakeven",be),("+3pp above breakeven",be+0.03)):
    for nt in (100,500):
        eq,mdd,alive=sim(p,nt)
        print(f"  {lbl:<22}{nt:>5} trades  median ${np.median(eq):>10,.2f}  "
              f"p5 ${np.percentile(eq,5):>8,.2f}  p95 ${np.percentile(eq,95):>10,.2f}  "
              f"survived {alive.mean():>5.1%}  medDD {np.median(mdd):>5.1%}")

print(f"\n\nWHAT WOULD BE REQUIRED -- the edge needed, versus what exists\n")
print(f"  {'scenario':<34}{'p(win) needed':>16}{'edge over martingale':>22}")
for lbl,tgt_mult,horizon in (("$20 -> $100 in 6 months",5,180),
                             ("$20 -> $1,000 in 1 year",50,365),
                             ("$20 -> $10,000 in 2 years",500,730)):
    for tpd,tlab in ((1,"1 trade/day"),(3,"3 trades/day")):
        nt=horizon*tpd
        need=np.log(tgt_mult)/nt
        lo,hi=0.0,1.0
        for _ in range(200):
            m=(lo+hi)/2
            g=m*np.log(1+wr/100)+(1-m)*np.log(1-lr/100)
            if g<need: lo=m
            else: hi=m
        print(f"  {lbl+', '+tlab:<34}{hi:>15.1%}{hi-MART:>21.1%}")
print(f"\n  For reference, the largest conditional edge measured anywhere in this")
print(f"  project is ~2-4 percentage points, and none of it replicated out of sample.")
