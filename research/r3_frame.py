#!/usr/bin/env python3
"""R-3 framing -- what an asymmetric barrier grid can and cannot produce.

P0/T3 established that BTC 5m is a driftless random walk to within 0.8pp.
For a martingale, the optional stopping theorem fixes the first-passage
probability EXACTLY, for any barrier pair:

        P(target T before stop S) = S / (S + T)

and therefore the gross expectancy of EVERY cell in the grid is exactly zero:

        EV = P*T - (1-P)*S = S*T/(S+T) - T*S/(S+T) = 0

So searching the (stop x target x horizon) surface for a favourable cell is
searching for something that cannot exist in the null. The grid is not where an
edge lives. What the grid DOES determine is how large a conditional deviation
must be to pay for itself.

Writing P = S/(S+T) + d  (d = the edge, in probability points):

        EV       = d * (S + T) - cost
        REQUIRED d > cost / (S + T)

This is the R-3 hurdle. Note it depends only on the SPAN S+T, not on the ratio.
"""
import numpy as np

C = {"maker/maker": 0.030, "maker/taker": 0.0663, "taker/taker": 0.1026}  # % round trip

STOPS   = [0.05,0.10,0.15,0.20,0.30,0.40,0.50,0.75,1.00]
TARGETS = [0.10,0.15,0.20,0.30,0.40,0.50,0.75,1.00,1.50]

print("R-3 HURDLE -- probability points of deviation from the martingale that a")
print("cell must achieve, just to break even.  d > cost/(S+T)\n")
for lbl, c in C.items():
    print(f"  === {lbl}  (round trip {c:.4f}% of notional) ===")
    hdr = "stop / target"
    print(f"  {hdr:<14}" + "".join(f"{t:>8.2f}%" for t in TARGETS))
    for s in STOPS:
        row = f"  {s:>6.2f}%{'':<7}"
        for t in TARGETS:
            d = c/(s+t)*100
            mark = "*" if d <= 2.0 else ("!" if d > 5.0 else " ")
            row += f"{d:>7.1f}{mark}"
        print(row)
    print()
print("  * = hurdle <= 2.0 pp (within reach of a real conditional effect)")
print("  ! = hurdle > 5.0 pp (larger than any conditional effect measured in this project)\n")

print("Measured conditional deviations available to us, for reference:")
print("   bucket lifts (R-0)            1 - 4 pp")
print("   microstructure events (R-1)   0.049-0.060 ATR = 0.007-0.009% of price")
print("                                 -> as a probability deviation this is tiny\n")

print("Consequence: only the wide-span corner of the grid is even reachable.")
print("A 0.05% stop / 0.10% target needs a 44 pp deviation under maker/taker.")
print("A 1.00% stop / 1.50% target needs 2.7 pp.")
