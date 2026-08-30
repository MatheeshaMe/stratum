# research/

The evidence behind every claim in `Stratum_Product_Specification-v3.md` §0.
Python is the reference; the Rust engine must reproduce these tables to 1e-6
(Gate 2).

| File | Produces |
|---|---|
| `situations.py` | Situation vector, as-of level store, buckets B1–B6, triple-barrier labels |
| `analog_report.py` | Bucket lift over base rate, block-bootstrap CIs, IS/OOS sign stability |
| `wait_clock.py` | Survival curves; the memorylessness table |
| `ml_model.py` | Calibrated GBM, purged/embargoed CV, uniqueness weights, reliability curve |
| `wait_vs_click.py` | Click / wait / pass as EV per opportunity, net of cost |
| `run_all.py` | All of the above |

## Reproduce

```bash
python3 scripts/fetch_binance.py --from 2023-01 --to 2024-12 --out data/oos
python3 scripts/fetch_binance.py --from 2025-01 --to 2026-08 --out data/is
python3 research/run_all.py
```

## The four traps this harness is built to avoid

1. **Overlapping labels.** A 36-bar forward window means consecutive samples
   share ~97% of their outcome. Binomial CIs are meaningless. Everything uses
   a circular block bootstrap with block length = horizon, and the ML layer
   weights samples by inverse label concurrency.

2. **Leakage across CV folds.** `purged_folds()` drops training rows whose
   forward window overlaps the test fold, plus a `3 × horizon` embargo. Without
   this the AUC rises by roughly 0.1 for free — all of it fake. There is a test
   for this: a deliberately leaked feature must show AUC ≈ 1.0 unpurged and
   ≈ 0.5 purged.

3. **Label/payoff mismatch.** If the report pays 1.5R the target barrier must
   sit at 1.5 × the stop distance. Scoring a symmetric label against an
   asymmetric payoff inflated the base rate from 28% to 44% in the first pass
   of this harness. `triple_barrier(..., rr=)` exists for this reason.

4. **Significance mistaken for value.** At n = 377,000 a 0.4pp lift is
   "significant" and worthless. Lift is always reported in percentage points
   next to the cost in R.

## Known limitations

- Uses Binance BTCUSDT as the price proxy. Valid for structure (HL/Binance
  close correlation 0.999997) but **not** for wick triggers — 5m pivot
  agreement is only 70.6%, p95 wick difference 8 bps. Hence the 25 bps floor.
- Funding is not charged. Immaterial under ~6h holds; add before testing
  multi-day horizons.
- Level clusters rebuild every 4 bars for speed. Confirm the difference is
  immaterial before relying on it in Rust.

---

## Research phase 1 (edge discovery)

| File | Priority | Produces |
|---|---|---|
| `p0_validate.py` | P0 | Look-ahead, leakage, null-calibration and cost-identity tests. **Run this first; if it fails nothing downstream is trustworthy.** |
| `p1_hurdle.py` | P1 | The required-lift table: how many pp of conditional lift a given (execution, stop, target) demands |
| `p2_surface.py` | P2/P3 | bucket × stop × target × side surface with realised R and block-bootstrap CIs |
| `p2b_diagnose.py` | P2/P3 | Drift-vs-edge diagnostic (LONG/SHORT mirror test) |
| `p5_predictable.py` | P5 | Direction vs magnitude vs resolution predictability |

`HYPOTHESIS_REGISTRY.md` — every hypothesis, its pre-registered kill criteria, outcome.
`CORRECTIONS.md` — bugs found in this harness, their impact, and the fix.
`../EDGE_REPORT.md` — the verdict.

### Data regime

```
data/is/      EXPLORE   2025-01..2026-08   hypothesis generation
data/oos/     VALIDATE  2023-01..2024-12   sign stability (contaminated by repeated inspection)
data/sealed/  SEALED    2020-01..2022-12   NEVER OPENED -- one honest test remains
```

Do not open `data/sealed/` for exploratory work. It is worth exactly one test.

---

## R-1 (microstructure & positioning)

| File | Produces |
|---|---|
| `r1_features.py` | 38 microstructure features (OI, flow, positioning, book, carry). **All lagged one 5m bar.** |
| `r1_incremental.py` | AUC(OHLCV) vs AUC(micro) vs AUC(both) across 5 horizons; univariate AUCs |
| `r1_conditional.py` | Direction AUC by expected-magnitude band; magnitude × direction cells |
| `r1_events.py` | Event-conditioned forward distributions (simple, non-ML, quantile thresholds fixed in advance) |
| `r1_rigorous.py` | Same events with C3-corrected block bootstrap, drift control, split-half replication |
| `r1_economics.py` | C4 control (three models, identical rows) + ATR→bps→cost comparison |
| `../R1_REPORT.md` | The verdict |

Data: `scripts/fetch_microstructure.py` (Binance `metrics`, `bookDepth`, `fundingRate`).
The fetcher **refuses the sealed 2020–2022 window in code**:

```
$ python3 scripts/fetch_microstructure.py --from 2021-06-01 --to 2021-07-01
REFUSED: 2021-06-01 is inside the sealed holdout 2020-01-01..2022-12-31
```

Note: Binance stopped publishing `bookDepth` after 2026-01-13 (1105/1334 days
covered). Book features are NaN thereafter; HistGradientBoosting handles this
natively, and the A-vs-C comparison is run on identical rows so coverage cannot
bias it.

---

## R-3 (intraday path / barrier)

| File | Produces |
|---|---|
| `r3_frame.py` | The required-deviation table: `δ > cost/(S+T)` |
| `r3_paths.py` | First-passage engine, absolute-% barriers on 1m bars |
| `r3_surface.py` | 810-cell unconditional net-EV surface |
| `r3_states.py` | 16 states × reachable barrier cells |
| `r3_causal.py` | Trailing-threshold (C6) + C7-fixed entry indexing |
| `r3_stress.py` | Stop slippage, parameter plateau, leverage translation |
| `r3_portfolio.py` | Sequential one-position-at-a-time simulation |
| `../R3_REPORT.md` | The verdict |

**The C7 lesson.** `situations.agg()` returns `i1m` = index of the **first** 1m
bar of each 5m bar. A signal computed from the 5m **close** lives at
`i1m[k+1]-1`. Using `i1m[k]` as the entry index buys four minutes of the future.
Any new experiment on the 5m grid must use `i1m[k+1]-1` and fill at `i1m[k+1]`.
There is a diagnostic for this in `CORRECTIONS.md` §C7.
