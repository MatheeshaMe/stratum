# Stratum — Edge Report

**Research phase 1 · 28 August 2026**
BTC-USDC perpetuals, Hyperliquid. ~300 hypotheses tested across 3.4M 1-minute bars.

---

## VERDICT: **B** — interesting market structure, no economically exploitable directional edge

One effect was confirmed and replicates strongly. It is **not** directional and,
at this account's fee tier, **not monetizable on perps**. No hypothesis reached
the bar to spend the sealed holdout, which remains unopened.

Per the mission's Principle 3 and §31: I am not manufacturing an option A.

---

## 1. What was established

### 1.1 The null is now exact

BTC 5m is a **driftless random walk** with respect to barrier-crossing. With a
long horizon so the vertical barrier does not bind:

| Target | P(win \| resolved) measured | Random-walk theory 1/(1+rr) | diff |
|---|---:|---:|---:|
| 1.0R | 0.494 | 0.500 | −0.6pp |
| 1.5R | 0.394 | 0.400 | −0.6pp |
| 2.0R | 0.326 | 0.333 | −0.8pp |

Consistently *below* theory (ties resolve to the stop). This is the control
against which every claim in this project is now measured.

### 1.2 The whole problem reduces to one inequality

Given the null above, with `s` = stop as a fraction of price, `c` = round-trip
cost in bps, `rr` = target/stop:

```
cost_R        = (c/1e4)/s
breakeven p*  = (1 + cost_R)/(1 + rr)
random-walk p0= 1/(1 + rr)
REQUIRED LIFT = p* - p0 = cost_R/(1 + rr)
```

**"Is there an edge?" becomes: can conditioning move P(win) by more than
`cost_R/(1+rr)` percentage points?**

| Execution | 0.6% stop | 1.0% | 2.0% | 3.0% |
|---|---:|---:|---:|---:|
| taker in / taker out | 6.84pp | 4.10pp | 2.05pp | 1.37pp |
| maker in / taker out | 4.42pp | 2.65pp | **1.33pp** | **0.88pp** |
| maker in / maker out | 2.00pp | 1.20pp | **0.60pp** | **0.40pp** |

*(target = 1.5R)*

Measured bucket lifts are +1 to +4pp. **So the question was genuinely open** —
a 2–4pp structural lift, executed maker-only on a 2% stop, would clear a
1.33pp hurdle. That is why P2 swept exactly that corner.

### 1.3 It does not clear

240 cells of (bucket × stop-width × target × side), each with a circular
block-bootstrap CI:

**Zero cells have a 95% CI above zero.**

The apparent positive gross R at wide stops was diagnosed and explained:

- BTC drifted **−22.3%/yr** over EXPLORE, so SHORT gross is positive and LONG
  negative, summing to ≈0 — the signature of drift, not edge.
- The residual asymmetry is the vertical-barrier markout, which skews as the
  target moves further away.

### 1.4 B6 accept_break — killed, with a mechanism

B6 was the strongest surviving hypothesis entering this phase. Excess over the
unconditional same-side baseline:

| Config | LONG excess | SHORT excess | 95% CI (LONG) |
|---|---:|---:|---|
| k=14, rr=1.5 | **+0.058R** | **−0.070R** | [−0.050, +0.165] |
| k=14, rr=3.0 | +0.062R | −0.072R | [−0.079, +0.203] |

LONG and SHORT excesses are **mirror images**. That is the signature of a
directional bias, not structure: B6 is a momentum proxy that happens to be long.
It also **inverts with horizon** — best bucket at 2 ATR barriers, worst at 14–20
ATR — consistent with brief continuation followed by reversion. Every CI spans
zero. **B6 is rejected.**

### 1.5 Waiting adds nothing

Conditional on a state being unresolved at bar *k*, the eventual direction:

| unresolved at bar | n | up | down |
|---:|---:|---:|---:|
| 0 | 209,728 | 46.9% | 47.0% |
| 6 | 195,999 | 46.7% | 46.8% |
| 18 | 156,683 | 46.2% | 45.7% |

The process is **memoryless**. Nothing coils; nothing builds.

---

## 2. The one confirmed effect

**Direction is unpredictable. Magnitude is strongly predictable. Both replicate.**

Same state vector, same purged/embargoed CV, same uniqueness weights:

| Target | EXPLORE 2025-26 | VALIDATE 2023-24 |
|---|---:|---:|
| (a) direction — sign of forward move | AUC **0.489** | AUC **0.510** |
| (c) resolution — will it reach ±7 ATR | AUC **0.775** | AUC **0.760** |
| (b) magnitude — forward range in ATR | R² **0.309** | R² **0.275** |

This is a large, stable effect: from the state at time *t* you can say with real
confidence **how far** price will travel, and with none at all **which way**.

### Why it is not monetizable here

Volatility predictability pays through instruments this venue and account cannot
access:

| Route | Blocked by |
|---|---|
| Options / straddles | Not offered on Hyperliquid perps |
| Maker-rebate capture in quiet regimes | HL maker fee is **paid** (1.5bps), not a rebate, at every tier |
| Filtering out non-resolving trades | Filtering a zero-EV trade yields zero-EV. **Principle 3**: a filter cannot manufacture edge |
| Volatility-scaled sizing | Improves risk-adjusted return *given* an edge; there is none to scale |

**It has genuine product value, not trading value** — it is exactly the engine
for the v3 Specialness Meter and Wait Clock ("this state will not resolve; stop
watching it"), and it is the right basis for barrier placement *if* a
directional edge is ever found.

---

## 3. Honest accounting

```
distinct hypotheses / cells tested        ~300
expected false discoveries at a = 0.05     ~15
observed cells with 95% CI above zero        0
```

**Fewer significant results than chance alone would produce.** This is the
strongest form the null can take.

### Two bugs found in my own research, both of which had inflated results

| ID | Bug | Impact | Status |
|---|---|---|---|
| **C1** | Symmetric barriers scored against an asymmetric 1.5:1 payoff | Base rate appeared **44%** vs true **28%** | fixed, re-run |
| **C2** | Trades unresolved at the vertical barrier charged as full −1R stop-outs | Created **17 phantom cells** flagged "clears hurdle"; all vanished on correction | fixed, re-run |

C2 surfaced only because a cell reported `lift > hurdle` *and* `netEV < 0`
simultaneously — two statements that cannot both be true. Full detail in
`research/CORRECTIONS.md`.

### The verification wall

Sample size to distinguish an edge from zero at 95% confidence:

| True edge | EV/trade | trades needed | at 1 trade/day |
|---|---:|---:|---:|
| +2pp lift | +0.017R | 21,088 | **58 years** |
| +3pp | +0.042R | 3,476 | **9.5 years** |
| +5pp | +0.092R | 732 | **2.0 years** |
| +8pp | +0.167R | 224 | 0.6 years |

**Any edge small enough to be plausible here is too small to verify from live
trading.** This is decisive for risk architecture: parameter uncertainty will
always dominate, so sizing must be a small fraction of Kelly, and edge-decay
monitoring cannot work on trade counts — it must watch the conditional
distribution directly.

---

## 4. Strongest remaining hypotheses

Ranked by expected information gain per unit of effort. None has been tested.

**R-1 — Cross-venue / microstructure state (highest value).**
Everything tested so far uses OHLCV alone. Untested and free: order-book
imbalance, `oi_delta`, funding vs cross-venue funding, HL-vs-Binance basis,
liquidation prints. These are the inputs that carry *positioning*, which OHLCV
cannot see. This is the largest unexplored volume in the state space.

**R-2 — Longer horizons.** Everything here is intraday (≤ 8h). The cost hurdle
falls as `1/s`, so at multi-day horizons with 5–8% stops the hurdle is
0.1–0.3pp. Crypto momentum at weekly horizons is a documented effect. Test it
with funding charged.

**R-3 — Conditional volatility as a tradeable object.** H-010 is real and
strong. If Hyperliquid ever lists options, or if a venue offering them is
acceptable, this is the effect to trade — it is far more robust than anything
directional found here.

**R-4 — Execution alpha.** Not a signal: the measured 6.6 → 3.0 bps improvement
from maker-only exit is larger than every conditional lift measured. If a
directional edge is ever found, this is worth more than improving the signal.

**Explicitly closed:** additional OHLCV indicators, deeper ML on the current
feature set, B5, B6, entry-timing variants, and any further parameter search on
the tested surface. These are exhausted.

---

## 5. Recommendation

**Do not trade.** No hypothesis has positive expected value after realistic cost
with a confidence interval excluding zero, in any period, at any barrier width,
under any execution assumption tested.

The sealed 2020–2022 holdout **remains unopened**. That is deliberate: it is
worth one honest test, and nothing here has earned it. Spend it on R-1 or R-2,
once, after those hypotheses are fully specified and frozen.

The research machine now works: it has a validated null, an exact cost hurdle,
leak-proof validation, a registry, and it has already caught and corrected two
of its own errors. **That machine is the deliverable of this phase.** It found no
edge, which — per §31 — is a successful research outcome.

*The account is not the deadline. The edge is.*
