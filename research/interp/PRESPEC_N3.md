# N-3 pre-specification — decomposing the BL-05 compensation

Written before any conditional decomposition was computed.

## The exact accounting identity

For any condition *c* against baseline *b*, with p = P(up), u = mean|up, d = mean|down:

```
mean = p·u + (1−p)·d

Δmean = FREQ + PAYOFF + INTERACTION          (exact, no residual)

FREQ        = Δp · (u_b − d_b)               frequency moved, payoffs held at baseline
PAYOFF      = p_b·Δu + (1−p_b)·Δd            payoffs moved, frequency held at baseline
INTERACTION = Δp · (Δu − Δd)
```

**Compensation ratio** `κ = −PAYOFF / FREQ`, defined only where FREQ > 0.

- κ ≈ 1 → full compensation (BL-05's ordinary case)
- κ < 1 → the frequency gain partly survives
- κ > 1 → payoff deteriorates faster than frequency improves

## Type classification (§15), fixed in advance

| type | rule |
|---|---|
| **A** ordinary compensation | FREQ > 0 and κ ≥ 0.75 |
| **B** compensation partly breaks | FREQ > 0 and 0.25 ≤ κ < 0.75 |
| **C** compensation breaks | FREQ > 0 and κ < 0.25 |
| **D** joint asymmetry | Type C **and** Δu ≥ 0 **and** Δ\|d\| ≤ 0 (upside preserved, downside constrained) |

## Replication gate

A compensation break is REPLICATED only if, in **all six** era-asset cells
(BTC-early, BTC-late, ETH, SOL, XRP, DOGE):

1. FREQ > 0 (the frequency effect exists at all)
2. κ stays in the same band (A/B/C)
3. n ≥ 300 per cell
4. The pooled κ 95% block-bootstrap CI excludes 1.0

Failing 2–4 but passing 1 is recorded as **OBSERVED, NOT REPLICATED**.

## Staged testing (§19) — pre-specified, not brute force

| stage | dimension | cells |
|---|---|---|
| N3-1 | baseline decomposition, sweep low and sweep high | 2 |
| N3-2 | post-sweep sequence branch | 10 |
| N3-3 | location (4h range position, 3 bands) | 6 |
| N3-4 | approach mode (fast / slow / compressed / expanding) | 8 |
| N3-5 | volatility regime (3 bands) | 6 |
| N3-6 | displacement strength (data-derived quartiles) | 8 |
| N3-7 | volume regime (3 bands) | 6 |
| N3-8 | HTF structure agreement | 6 |

≈52 conditional cells × 6 replication cells. Expected false discoveries reported.

## Out of scope

No entries, stops, targets, R:R, sizing, costs, or PnL. Conclusion F ("no robust
compensation break exists") is an acceptable and fully reportable outcome.
