# Stratum hypothesis registry

Every hypothesis tested, with its pre-registered kill criteria and outcome.
Statuses: `IDEA` `TESTING` `PROMISING` `OOS VALIDATED` `PAPER` `LIVE` `REJECTED` `DECAYED`

## Data regime

| Set | Period | 1m bars | Use | Times inspected |
|---|---|---:|---|---|
| EXPLORE | 2025-01 → 2026-08 | 830,880 | all hypothesis generation | many |
| VALIDATE | 2023-01 → 2024-12 | 1,052,640 | sign-stability checks — **contaminated** by repeated inspection | many |
| R1-EXPLORE | 2023-01 → 2026-08 | 1,883,520 + microstructure | R-1 exploration | many |
| **SEALED** | **2020-01 → 2022-12** | **1,575,360** | **final holdout** | **0 — never opened** |

The sealed set was fetched at the start of this phase and has not been used.
Nothing reached the bar that would justify spending it.

## Pre-registered kill criteria (fixed before testing, not changed after)

```
minimum effect size        net EV > 0 after cost, 95% block-bootstrap CI above 0
minimum sample             n >= 150 trades in each period
cost model                 maker-in / taker-out + half-spread, sensitivity to taker/taker
temporal robustness        sign stable across EXPLORE and VALIDATE
parameter robustness       survives a contiguous region, not a single grid point
regime robustness          not confined to one volatility or drift regime
direction test             excess must not be a mirror image across LONG/SHORT (that is drift)
```

## Registry

| ID | Hypothesis | n tested | Result | Status |
|---|---|---:|---|---|
| H-001 | v1 T1: reject wick + weak second push, level fade | 519 / 436 | net −0.192R / −0.160R, t = −3.69 / −2.80 | **REJECTED** |
| H-002 | Rejection wick alone improves a level touch | 823 / 637 | Makes it *worse* in both periods, replicated | **REJECTED** |
| H-003 | Breakout continuation (6 configs) | 890–1088 | gross +0.01…+0.16R, sign never stable | **REJECTED** |
| H-004 | Wick + climax volume | 127 / 210 | +0.186R IS → +0.007R OOS. Best-of-25 selection noise | **REJECTED** |
| H-005 | Situation buckets B1–B6 shift direction odds | 377k bars | lifts +1…4pp, 10/12 signs stable, all economically < hurdle | **REJECTED** (as tradeable) |
| H-006 | Waiting for a trigger adds directional information | 377k bars | Process is memoryless: 46.9/47.0 at bar 0 → 46.2/45.7 at bar 18 | **REJECTED** |
| H-007 | Calibrated GBM on 21 features predicts direction | 8.7k / 18.9k | AUC 0.504–0.555, Brier skill ≈ 0, all thresholds negative EV | **REJECTED** |
| H-008 | B6 accept_break is a genuine structural edge | 13.5k | Excess over baseline +0.058R LONG / −0.070R SHORT — a **mirror image**, i.e. directional bias, not structure. CI spans zero at every (k, rr) | **REJECTED** |
| H-009 | Wide stops + maker execution make a small lift viable | 240 cells | Hurdle falls to 1.3pp as predicted, but no bucket excess survives; positive gross R traced to period drift + vertical-barrier markout | **REJECTED** |
| H-010 | Volatility / resolution is predictable from the state | 155k / 201k | **AUC 0.775 / 0.760; R² 0.309 / 0.275. Replicates.** | **CONFIRMED — not monetizable** |

### R-1 — microstructure and positioning (2026-08-28)

Exploratory data: Binance USD-M BTCUSDT `metrics` (5m OI, top-trader long/short
by account and by size, taker buy/sell volume ratio), `bookDepth` (cumulative
depth at ±1–5% of mid, 30s), `fundingRate`. Window **2023-01-01 → 2026-08-26**,
1,334 days. The fetcher refuses the sealed window in code, not policy.

| ID | Hypothesis | n | Result | Status |
|---|---|---:|---|---|
| H-011 | Microstructure adds directional information beyond OHLCV | 124,638 | AUC(OHLCV+micro) − AUC(OHLCV) = **+0.000, −0.003, −0.001, +0.003, −0.004** at 5/15/30/60/180min | **REJECTED** |
| H-012 | Within high-magnitude states, microstructure resolves direction | 356,275 | Micro makes it **worse** at every magnitude tercile (−0.003 to −0.008 AUC) | **REJECTED** |
| H-013 | magnitude × direction produces asymmetric payoff | 356,275 | OHLCV-only spread +8.5% / +0.190 ATR **beats** combined +7.4% / +0.112 ATR | **REJECTED** (C4) |
| H-014 | Aggressive-flow events predict reversal | 18,821 bars / 17,031 episodes | **+0.049 ATR at 30m, CI [+0.020,+0.076], survives detrending and both halves** | **CONFIRMED — 11% of cost hurdle** |
| H-015 | Extreme top-trader short positioning predicts reversal | 18,821 / 1,653 episodes | **+0.060 ATR at 30m, CI [+0.006,+0.116], survives all controls** | **CONFIRMED — 14% of cost hurdle** |
| H-016 | Book-imbalance shocks predict continuation | 18,835 / 8,239 | −0.042 ATR at 30m, but 2nd half only −0.011 | **REJECTED** (unstable) |
| H-017 | Funding extremes predict direction | 18,821 / **521 episodes** | −0.320 ATR at 180m but CI relies on few episodes, effect grows with horizon (trend-like), only partly survives detrending | **REJECTED** (insufficient independent episodes) |

**R-1 multiple-testing accounting**

```
tests run in R-1                        ~160
significant after corrected block CI       5 of 21 in the controlled set
expected by chance at a=0.05             ~1.1
survive detrending + split-half sign       2   (H-014, H-015)
economically sufficient                    0
```

**Cumulative across the project: ~460 hypotheses. Zero tradeable.**

## Multiple-testing accounting

```
distinct hypotheses / cells tested   ~300
expected false "discoveries" at a=0.05   ~15
observed cells with 95% CI above zero    0   (after correction C2)
```

**We found fewer significant results than chance alone would have produced.**
That is not a null result to be explained away; it is strong positive evidence
that no directional edge of exploitable size exists in the tested domain.

## Corrections

See `CORRECTIONS.md`. Two bugs found in Stratum's own research code, both of
which had inflated results, both fixed and re-run:

- **C1** label/payoff mismatch — base rate appeared 44% vs true 28%
- **C2** unresolved trades charged as full stop-outs — created 17 phantom
  "clears hurdle" cells that vanished on correction
