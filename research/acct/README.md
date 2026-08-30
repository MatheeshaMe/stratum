# research/acct — BTC 3%-per-trade account opportunity study

| File | Produces |
|---|---|
| `e1_leverage.py` | Account-return → BTC-move translation; cost-share and breakeven-win-rate tables |
| `e2_opportunity.py` | First-passage opportunity availability by leverage and time limit; net EV |
| `e3_vol_rr.py` | Volatility buckets, risk:reward structures, opportunity frequency, hourly |
| `e4_entry.py` | 94 entry conditions × 2 sides, three-way chronological split |
| `e6_compound.py` | $20 Monte Carlo on the measured distribution; required-edge inversion |

Report: `../../ACCOUNT_3PCT_STUDY.md`

## The identity this study rests on

At leverage `L`, account P&L = `L × (price_move − cost)`. Leverage scales gain,
loss, cost and variance by the same factor, so it cancels out of expectancy.
It only shrinks the move you need — which makes the fixed cost a **larger**
share of the target.

```
cost / target = c / (A / L) = c·L / A
```

Breakeven win rate at 10×, 1:2, maker-in/taker-out: **48.1%**.
Martingale-available win rate: **33.3%**. Measured: **32.7%**.
