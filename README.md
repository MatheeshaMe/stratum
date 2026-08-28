# Stratum

A cost-governed confluence engine for **BTC-USDC perps on Hyperliquid**.

**Read [`EDGE_REPORT.md`](EDGE_REPORT.md) first.** Verdict after ~300 hypotheses
across 3.4M bars: interesting market structure, **no economically exploitable
directional edge**. Do not trade.

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
