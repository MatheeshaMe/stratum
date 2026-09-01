# research/interp — market interpretation engine

| File | Purpose |
|---|---|
| `observe.py` | Multi-timeframe representation: structure, liquidity, price action, sequences, approach, regime. 230 observations across 1m/5m/15m/1h/4h. |
| `divergence.py` | Which observations change the forward DISTRIBUTION — split into directional / magnitude / shape / timing |
| `validate.py` | Sign replication across BTC-early, BTC-late, ETH, SOL, XRP, DOGE |
| `market_read.py` | The §28 market read, every line tagged by information class |
| `invariants.py` | §27 mandatory correctness checks (would have caught C9–C12) |

Report: `../../INTERPRETATION_ENGINE.md`

## The central result

```
MAGNITUDE / TIMING  replicates across all 6 era-asset cells
DIRECTIONAL         1 of 9 observations holds its sign
```

Measure distributional divergence, not just mean shift. A conditional
distribution can differ in variance, tail and resolution speed with an identical
mean — and those differences replicate where the mean shift does not.

## The sequence finding

`sweep → acceptance` and `sweep → reclaim → displacement` have **opposite** mean
shifts (+0.49 vs −0.37, both significant on BTC). The sequence carries the
information; the bare sweep does not. But the sign is the opposite of the
standard teaching, and neither replicates across assets.
