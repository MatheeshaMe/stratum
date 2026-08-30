# research/struct — market-structure recognition

| File | Purpose |
|---|---|
| `zigzag.py` | The engine: ATR ZigZag swings, trend state, impulse/pullback, BOS, efficiency. **Causal and confirmed-only.** |
| `backtest.py` | Structural backtest with UNBOUNDED trailing exits (the methodological fix) |
| `s1_setups.py` | 6 structural setups × 5 exit modes |
| `s2_efficiency.py` | Drill-down on the one positive cell: threshold sweep, eras, long/short, costs |
| `s3_breakout.py` | Real vs false breakouts, MTF alignment, conditional MFE/MAE by state |
| `s4_predict_accept.py` | Can acceptance be predicted at the breakout bar? (AUC 0.635) |
| `s5_tradeable.py` | Does that prediction pay? (no) |
| `s6_multiasset.py` | BTC / ETH / SOL / XRP / DOGE |

Report: `../../STRUCTURE_STUDY.md`

## Two traps this code is built to avoid

**Confirmation lag.** A pivot at bar `i` is not knowable at bar `i`. `zigzag()`
returns `(confirm_bar, pivot_bar, price, kind)` and `structure_state()` writes
each pivot's information starting at `confirm_bar`, never `pivot_bar`. Median
lag at θ=3.0 is 5 bars. Ignoring this manufactures enormous phantom edges.

**Definitional circularity.** "Accepted breakout" is defined using bars after
the break. Comparing accepted-vs-failed forward paths is therefore circular —
it selects paths that went up (MFE/MAE 4.02 vs 0.17). The only non-circular
question is whether acceptance is *predictable at the breakout bar*, which is
what `s4_predict_accept.py` measures.

## R-3 monetization phase

| File | Phase | Produces |
|---|---|---|
| `p3_entry.py` | 3 | 9 entry-timing variants, EV per opportunity |
| `p4_pathmodel.py` | 4–6 | Meta-labelled path model, P(peak ≥ kR), GBM vs logistic |
| `p7_trade.py` | 7–8, 18 | Rank×slice tradeability, management variants, splits |
| `p11_19_17.py` | 11, 19, 17 | Derivatives at breakout, A/B/C baselines, $20 simulation |
| `FROZEN_HYPOTHESIS.md` | 13 | The pre-registered spec, frozen before the sealed test |
| `p13_sealed.py` | 13 | **One-shot sealed 2020–2022 test** |
| `p13b_beta.py` | 13 | Post-hoc control: structure vs matched random longs |

**The sealed window is now spent.** `data/sealed_spot/` exists and 2020–2022 has
been used. It cannot serve as a holdout again.
