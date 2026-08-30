#!/usr/bin/env python3
"""E1 -- translating account return into BTC movement, and the invariance that
governs this entire question.

At leverage L, an account return A requires a BTC move  m = A / L.
Both the payoff AND the cost scale by L:

    account P&L  =  L * (m_realised - c)        c = round-trip cost in price terms

so the ratio that decides expectancy is

    cost / target  =  c / m  =  c*L / A

Leverage cancels out of the EXPECTANCY. It scales gain, loss, cost and variance
by exactly the same factor. What leverage changes is the BTC move you need,
and therefore how much of that move your fixed cost consumes.

Higher leverage does not make +3% easier. It makes the required move smaller,
which makes the cost a LARGER fraction of it.
"""
import numpy as np

TAKER, MAKER, HALFSPREAD = 4.5, 1.5, 0.63          # bps
SCEN = {
  "maker in / maker out (optimistic)":  MAKER + MAKER,
  "maker in / taker out (mixed)":       MAKER + TAKER + HALFSPREAD,
  "taker in / taker out (realistic)":  (TAKER + HALFSPREAD)*2,
}
LEV = [1,2,5,10,20,40]
ACCT = [1,2,3,5]

print("1. BTC PRICE MOVE REQUIRED FOR A GIVEN ACCOUNT RETURN\n")
print(f"  {'leverage':<10}" + "".join(f"{f'+{a}% acct':>12}" for a in ACCT))
for L in LEV:
    print(f"  {L:>4}x{'':<5}" + "".join(f"{a/L:>11.3f}%" for a in ACCT))

print("\n\n2. COST AS A FRACTION OF THE TARGET  (this is the whole problem)\n")
for lbl, c_bps in SCEN.items():
    c = c_bps/100.0                                  # bps -> %
    print(f"  === {lbl}: {c_bps:.2f} bps round trip = {c:.4f}% of notional ===")
    print(f"  {'leverage':<10}{'BTC move for +3%':>18}" +
          "".join(f"{f'+{a}% acct':>12}" for a in ACCT))
    for L in LEV:
        m3 = 3.0/L
        row = f"  {L:>4}x{'':<5}{m3:>17.3f}%"
        for a in ACCT:
            m = a/L
            row += f"{c/m:>11.1%}"
        print(row)
    print()

print("3. FUNDING, on top of the above (Hyperliquid funds hourly)\n")
print(f"  {'hold time':<12}{'typical (0.00125%/h)':>24}{'elevated (0.01%/h)':>22}"
      f"{'extreme (0.05%/h)':>21}")
for h,lab in ((0.5,"30 min"),(1,"1 hour"),(4,"4 hours"),(12,"12 hours"),(24,"1 day")):
    print(f"  {lab:<12}{0.00125*h:>23.4f}%{0.01*h:>21.4f}%{0.05*h:>20.4f}%")
print("  (funding is paid on NOTIONAL, so it scales with leverage exactly like the target)")

print("\n\n4. THE BREAKEVEN WIN RATE, by leverage and risk:reward\n")
print("  Assuming a symmetric setup: target = rr x stop, stop chosen so that")
print("  a WIN returns +3% on the account.\n")
c = SCEN["maker in / taker out (mixed)"]/100.0
print(f"  {'leverage':<10}{'BTC target':>12}{'BTC stop (1:1)':>16}"
      + "".join(f"{f'BE win% @1:{r}':>16}" for r in (1,1.5,2,3)))
for L in LEV:
    t = 3.0/L
    row = f"  {L:>4}x{'':<5}{t:>11.3f}%{t:>15.3f}%"
    for rr in (1,1.5,2,3):
        s = t/rr                                   # stop implied by the r:r
        cost_R = c/s
        p = (1+cost_R)/(1+rr)
        row += f"{p:>15.1%}"
    print(row)
print("\n  Gross breakeven (zero cost) would be 50.0% / 40.0% / 33.3% / 25.0%.")
print("  The gap between those and the numbers above is what cost takes.")
