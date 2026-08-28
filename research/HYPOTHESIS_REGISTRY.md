# Stratum hypothesis registry

Every hypothesis tested, with its pre-registered kill criteria and outcome.
Statuses: `IDEA` `TESTING` `PROMISING` `OOS VALIDATED` `PAPER` `LIVE` `REJECTED` `DECAYED`

## Data regime

| Set | Period | 1m bars | Use | Times inspected |
|---|---|---:|---|---|
| EXPLORE | 2025-01 → 2026-08 | 830,880 | all hypothesis generation | many |
| VALIDATE | 2023-01 → 2024-12 | 1,052,640 | sign-stability checks — **contaminated** by repeated inspection | many |
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
| H-010 | Volatility / resolution is predictable from the state | 155k / 201k | **AUC 0.775 / 0.760; R² 0.309 / 0.275. Replicates.** | **CONFIRMED — not monetizable (see below)** |

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
