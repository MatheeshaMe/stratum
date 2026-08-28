#!/usr/bin/env python3
"""P1 -- cost sensitivity, expressed as the HURDLE an edge must clear.

P0/T3 established the null exactly: BTC 5m is a driftless random walk, so for a
target at rr x stop the unconditional P(win|resolved) = 1/(1+rr), confirmed to
within 0.8pp at rr = 1.0, 1.5, 2.0.

That makes the whole project one inequality. With
    s  = stop distance as a fraction of price
    c  = round-trip cost in bps
    rr = target / stop
then
    cost_R          = (c/1e4)/s
    breakeven p*    = (1 + cost_R)/(1 + rr)
    random-walk p0  = 1/(1 + rr)
    REQUIRED LIFT   = p* - p0 = cost_R/(1 + rr)

So the entire question "is there an edge?" becomes:
    can conditioning move P(win) by more than cost_R/(1+rr) percentage points?

Measured bucket lifts to date: 1-4pp. This script says exactly which
(execution, stop, rr) combinations put that in reach.
"""
import numpy as np

STYLES = {                                   # round-trip bps
    "taker in / taker out":            4.5+0.63 + 4.5+0.63,
    "maker in / taker out":            1.5      + 4.5+0.63,
    "maker in / maker out":            1.5      + 1.5,
    "maker/taker + referral (-4%)":    1.5*0.96 + 4.5*0.96+0.63,
    "maker/maker + referral (-4%)":    1.5*0.96 + 1.5*0.96,
}
STOPS = [0.006, 0.008, 0.010, 0.015, 0.020, 0.030]
RRS   = [1.0, 1.5, 2.0, 3.0]

def required_lift(c_bps, s, rr):
    return (c_bps/1e4)/s/(1.0+rr)

print("P1  REQUIRED LIFT -- percentage points of P(win) that conditioning must add\n")
print("Reference: measured bucket lifts in Stratum to date are +1 to +4 pp.")
print("Cells at or under 2.0pp are within reach of a real structural effect.\n")
for rr in RRS:
    print(f"  target = {rr}R                    " + "".join(f"{s*100:>8.1f}%" for s in STOPS))
    print("  " + "-"*34 + "-"*(8*len(STOPS)))
    for name, c in STYLES.items():
        row = f"  {name:<32}"
        for s in STOPS:
            lp = required_lift(c, s, rr)*100
            mark = "*" if lp <= 2.0 else (" " if lp <= 4.0 else "!")
            row += f"{lp:>7.2f}{mark}"
        print(row)
    print()

print("  * = hurdle <= 2.0pp (plausible)      ! = hurdle > 4.0pp (implausible)\n")

# what does the SAME edge earn across the grid? fix a lift, show net EV per trade
print("\nP1b  NET EV PER TRADE for a fixed, realistic conditional lift\n")
for lift in (0.02, 0.03, 0.05):
    print(f"  conditional lift = +{lift*100:.0f}pp on P(win)")
    print(f"  {'execution':<32}" + "".join(f"{s*100:>8.1f}%" for s in STOPS))
    for name, c in STYLES.items():
        row = f"  {name:<32}"
        for s in STOPS:
            rr = 1.5
            p = 1.0/(1.0+rr) + lift
            ev = p*rr - (1-p)*1.0 - (c/1e4)/s
            row += f"{ev:>+8.3f}"
        print(row)
    print()

# how many trades to distinguish that EV from zero?
print("\nP1c  SAMPLE SIZE to detect the edge at 95% confidence (two-sided)\n")
print(f"  {'lift':>6}{'rr':>6}{'EV/trade':>10}{'sd(R)':>8}{'n for t=2':>12}{'at 1 trade/day':>18}")
for lift in (0.02, 0.03, 0.05, 0.08):
    rr = 1.5; p = 1.0/(1.0+rr) + lift
    ev = p*rr - (1-p)*1.0 - 0.033          # maker/taker, 2% stop
    sd = np.sqrt(p*(rr-ev)**2 + (1-p)*(-1-ev)**2)
    n = (2*sd/ev)**2 if ev > 0 else np.inf
    print(f"  {lift*100:>5.0f}p{rr:>6.1f}{ev:>+10.3f}{sd:>8.2f}"
          f"{n:>12,.0f}{n/365:>15,.1f} yr" if np.isfinite(n)
          else f"  {lift*100:>5.0f}p{rr:>6.1f}{ev:>+10.3f}{sd:>8.2f}{'never':>12}")
