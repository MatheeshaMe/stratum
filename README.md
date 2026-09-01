# Stratum

A cost-governed confluence engine for **BTC-USDC perps on Hyperliquid**.

**Read [`EDGE_REPORT.md`](EDGE_REPORT.md), [`R1_REPORT.md`](R1_REPORT.md), then [`R3_REPORT.md`](R3_REPORT.md).**

Verdict after **~1,650 hypotheses**: no tradeable edge found.

- **R-0** situations/ML — direction unpredictable (AUC 0.50–0.55); magnitude is (AUC 0.77)
- **R-1** microstructure — a real contrarian flow effect, 7× too small to pay its costs
- **R-3** intraday paths — 810-cell barrier surface nets **−cost in every cell**

**Do not trade.**

Descriptive studies:
- [`BTC_PLUS3PCT_STUDY.md`](BTC_PLUS3PCT_STUDY.md) — what BTC does before, during and after a +3% move
- [`ACCOUNT_3PCT_STUDY.md`](ACCOUNT_3PCT_STUDY.md) — can leverage deliver +3% account return per trade? (no: breakeven needs 48.1% wins, market offers 32.7%)
- [`STRUCTURE_STUDY.md`](STRUCTURE_STUDY.md) — automated market-structure recognition across 5 assets (recognition works, AUC 0.635 on breakout acceptance; capture does not)
- [`BEHAVIORAL_LIBRARY.md`](BEHAVIORAL_LIBRARY.md) — validated map of conditional market behaviour. **Directional info DOES replicate as P(up) (6 of 10 branches, all 6 era-asset cells)** — the prior phase's mean-shift measurement missed it. Payoff moves the other way by an offsetting amount
- [`INTERPRETATION_ENGINE.md`](INTERPRETATION_ENGINE.md) — market interpretation layer, not a strategy. Measures distributional divergence: **magnitude/timing information replicates across 6 era-asset cells; directional does not (1 of 9)**
- [`ADAPTIVE_POLICY.md`](ADAPTIVE_POLICY.md) — state→action policy with dynamic stops/targets. Policy loses to WAIT out of sample; two more execution bugs (C11, C12) found. Contains the efficiency identity: available R:R is offset by hit rate to within 0.4%
- [`TRADER_SYSTEM.md`](TRADER_SYSTEM.md) — reconstructing the discretionary S&D trader. Ablation kills the context hierarchy; zone + HTF alignment + trailing structural exit survives at +0.314R but fails its pre-registered held-out test. Pine Script in [`pine/`](pine/)
- [`ZONES_STUDY.md`](ZONES_STUDY.md) — supply/demand zone mechanism test (freshness decay confirmed; impulse strength, fresh-zone advantage and liquidity sweeps all falsified; DO NOT BUILD)
- [`R3_ENGINE_REPORT.md`](R3_ENGINE_REPORT.md) — **sealed 2020-2022 window opened and spent.** Frozen hypothesis FAILED pre-registered criteria (+0.118R, CI spans zero, long-side only). Verdict: PROMISING BUT UNPROVEN

The sealed 2020–2022 holdout remains unopened.

Then `STRATUM.md` (execution/risk architecture) and
`Stratum_Product_Specification-v3.md` (the situation-meter product).

```
STRATUM.md              the specification
config/strategy.toml    live knobs (hot-reloaded; paper and live read only this)
config/search.toml      sweep ranges (search never writes strategy.toml)
research/               reference backtest harness + reproduction of §0
scripts/fetch_binance.py  free deep history, no API key
data/                   parquet bars, sqlite signals (gitignored)
```

## Status

| Gate | Meaning | State |
|---|---|---|
| 0 | Recorder running, history ingested, harness reproduces §0 | not started |
| 1 | Computed levels match the operator's eye | not started |
| 2 | Harness correctly rejects the known-bad v1 template | **reproduced in Python** |
| 3 | A hypothesis clears all §13.3 kill criteria | **NOT PASSED — see EDGE_REPORT.md** |
| 4 | 14 clean paper days, expectancy matches backtest | not started |

## Quick start

```bash
python3 scripts/fetch_binance.py --from 2023-01 --to 2026-08 --out data/bars/venue=binance
python3 research/reproduce.py
```

## The one rule

No live order module until Gate 3 passes. The account is not the deadline;
the edge is.
