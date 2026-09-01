# Behavioural Library — Conditional Market Behaviour

**1 September 2026 · 938,247 base observations · 5 assets · 2 eras · 4 information classes**

*Layer 1 (observation) + Layer 2 (behaviour). No entries, stops, targets, sizing or policy — Layer 3 is out of scope by instruction.*

---

## The headline

My previous phase concluded that directional observations did not replicate. **That conclusion was too narrow, and this phase overturns part of it.**

The error was measuring direction as a **mean shift**. Measured as **P(up) — the frequency of a positive forward move — direction replicates strongly**: 6 of 10 sweep-tree branches hold their sign and effect size across all six era-asset cells.

But the frequency gain is almost exactly cancelled by a payoff loss, and that too replicates. Both halves of that statement are new.

---

## Baseline (938,247 bars, 4h forward, ATR units)

| | |
|---|---|
| mean **+0.092** · P(up) **51.4%** · P(+1 ATR before −1 ATR) **49.1%** | |
| MFE **2.87** · MAE **2.96** · range **6.81** · P(\|move\|>2 ATR) **58.3%** | |
| sd **6.04** · skew **+0.53** · kurtosis **22.2** · MAE-first **50.7%** | |
| median bars to ±0.5 ATR **2** · to ±1 ATR **5** | |

Two facts worth carrying: **P(+0.5 ATR before −0.5 ATR) is 46.7%, below half** — adverse excursion arrives first more often than not. And kurtosis of 22 means every mean in this document is a fragile statistic.

---

## BL-01 — Liquidity sweep shifts the FREQUENCY of direction ✅ REPLICATED

**Observation.** Price pokes beyond a 15m liquidity pool and closes back inside.

**Effect on P(up), 4h forward:**

| branch | BTC early | BTC late | ETH | SOL | XRP | DOGE | verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| sweep **low** (raw) | +6.7% | +5.2% | +5.3% | +4.2% | +6.1% | +4.0% | **REPLICATED** |
| low → reclaim, no displacement | +5.8% | +4.0% | +5.0% | +2.7% | +4.4% | +3.8% | **REPLICATED** |
| **low → acceptance + displacement** | — | **+7.8%** | **+7.6%** | **+5.3%** | **+10.0%** | **+13.1%** | **REPLICATED** |
| sweep **high** (raw) | −5.8% | −3.2% | −3.7% | −1.7% | −4.4% | −1.3% | **REPLICATED** |
| high → reclaim, no displacement | −4.9% | −3.6% | −2.7% | −1.5% | −5.3% | −0.5% | **REPLICATED** |
| **high → acceptance + displacement** | **−7.8%** | **−4.0%** | **−4.2%** | **−5.4%** | **−9.2%** | **−3.4%** | **REPLICATED** |

**Interpretation.** A swept low is followed by a positive 4-hour close more often than baseline; a swept high, less often. The effect is largest when the sweep resolves into **acceptance with displacement** — up to +13.1 pp.

**What it does NOT mean.** It does not mean the *expected return* improves. See BL-05.

---

## BL-02 — Acceptance + displacement HALVES time to resolution ✅ REPLICATED

| branch | BTC early | BTC late | ETH | SOL | XRP | DOGE |
|---|---:|---:|---:|---:|---:|---:|
| low → acceptance + displacement | — | **0.50** | **0.50** | **0.50** | **0.50** | **0.50** |
| high → acceptance + displacement | **0.50** | **0.50** | **0.50** | **0.50** | **0.50** | **0.50** |
| every other branch | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |

*(median bars to a ±0.5 ATR touch, ratio to baseline)*

**Interpretation.** When a sweep resolves into acceptance *and* the move displaces, the market reaches a ±0.5 ATR outcome in **half the usual time** — 1 bar instead of 2 — in every cell tested. No other branch moves this number at all.

**Use.** Timing and patience: how long to wait before the thesis is stale.
**Do NOT interpret as** a direction signal. It says *when*, not *which way*.

---

## BL-03 — Sweeps and reclaims precede QUIETER conditions ✅ REPLICATED

Forward 4h range, ratio to baseline:

| branch | BTC early | BTC late | ETH | SOL | XRP | DOGE | verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| sweep low (raw) | 0.883 | 0.882 | 0.870 | 0.893 | 0.918 | 0.875 | **REPLICATED** |
| low → reclaim + displacement | 0.805 | 0.856 | 0.828 | 0.882 | 0.886 | 0.898 | **REPLICATED** |
| low → reclaim, no displacement | 0.861 | 0.860 | 0.845 | 0.876 | 0.900 | 0.858 | **REPLICATED** |
| high → reclaim + displacement | 0.867 | 0.908 | 0.886 | 0.931 | 0.913 | 0.910 | **REPLICATED** |
| high → reclaim, no displacement | 0.898 | 0.880 | 0.870 | 0.911 | 0.906 | 0.906 | **REPLICATED** |

**Interpretation.** After a liquidity sweep — and especially after a reclaim — the following four hours travel **8–20% less** than an average four hours. Every cell, every asset, both eras.

**This is the opposite of the folk model**, which treats a sweep as the trigger for an expansion. Measured, a sweep is followed by *contraction*. The expansion, if it happened, was the sweep itself.

**Use.** Target realism and participation.
**Do NOT interpret as** "nothing will happen" — 0.87× of a 6.81 ATR baseline range is still 5.9 ATR.

---

## BL-04 — Location changes the MEANING of a reclaim ⚠️ OBSERVED, NOT REPLICATED

Same event, conditioned on 4h range position (BTC):

| `sweep low → reclaim` at | n | Δmean | Δskew |
|---|---:|---:|---:|
| discount (<0.33) | 1,995 | **+0.147** | **+1.01** |
| mid (0.33–0.67) | 1,422 | −0.068 | +0.15 |
| premium (>0.67) | 1,915 | **−0.224** | **−1.80** |

The sign of the mean effect **flips with location**, and the skew swings by 2.8 units across the same event. A location-blind test would report ≈0 and conclude "no information."

**Status: observed on BTC, not yet replicated across assets.** It is in the library as a hypothesis, not a finding — it is exactly the kind of result that has failed replication repeatedly in this project.

---

## BL-05 — The payoff-asymmetry offset ✅ REPLICATED (and it is the important one)

This is why BL-01 must not be read as an edge.

| population | n | P(up) | mean \| up | mean \| down | mean | skew |
|---|---:|---:|---:|---:|---:|---:|
| ALL BARS | 938,247 | 51.4% | **+3.856** | **−3.882** | +0.092 | +0.50 |
| sweep low (raw) | 6,606 | **57.2%** | **+3.033** | **−3.773** | +0.117 | +0.23 |
| low → reclaim, no disp | 3,974 | 56.2% | +2.983 | −3.706 | +0.051 | +0.63 |
| low → acceptance + disp | 619 | 59.3% | +3.633 | −4.426 | +0.352 | −0.42 |
| sweep high (raw) | 7,224 | **46.9%** | **+4.137** | **−3.216** | +0.234 | +1.79 |
| high → reclaim, no disp | 4,342 | 47.1% | +4.020 | −3.159 | +0.222 | +1.88 |
| high → acceptance + disp | 730 | 45.6% | +4.646 | −3.306 | +0.321 | +1.12 |

**Read the two mean columns.** After a swept low, price closes higher **5.8 pp more often** — and the average up-move **shrinks from +3.86 to +3.03 ATR** while the average down-move **deepens**. Frequency improves; payoff worsens. Net mean +0.117 vs a +0.092 baseline: essentially unchanged.

The mirror holds for swept highs: P(up) falls 4.5 pp, but the average up-move *grows* to +4.14 and the average down-move *shrinks* to −3.22.

**This is the same efficiency identity found in the previous phase, now visible at the distributional level.** Direction-frequency and payoff-size move in opposite directions by an almost exactly offsetting amount.

---

## BL-06 — Rejection candles carry no information at any location ✅ REPLICATED NULL

| location | n | ΔP(up) | Δmean | MFE ratio | range ratio | t½ ratio |
|---|---:|---:|---:|---:|---:|---:|
| discount | 48,050 | **+0.0%** | −0.072 | 0.98 | 0.99 | 1.00 |
| mid | 35,849 | **+0.1%** | −0.023 | 0.97 | 0.98 | 1.00 |
| premium | 53,395 | **+0.1%** | −0.014 | 0.98 | 0.99 | 1.00 |

n = 137,294. This is not an underpowered null; it is a well-measured zero. A long-wicked small-bodied candle changes nothing about direction, magnitude or timing — including at the locations where discretionary practice says it should matter most.

---

## BL-07 — Sweeps add information over structure + location ✅ (Stage E)

Does the event survive knowing HTF trend and range position already?

| context | n | P(up) | + sweep low→reclaim | + sweep high→reclaim |
|---|---:|---:|---:|---:|
| HTF bullish + discount | 70,512 | 51.1% | **59.2%** (n=466) | **42.1%** (n=404) |
| HTF bullish + mid | 84,600 | 52.3% | 53.1% (n=456) | 48.1% (n=536) |
| HTF bullish + premium | 188,268 | 52.6% | **59.1%** (n=988) | 49.5% (n=1,354) |
| HTF bearish + discount | 148,655 | 50.3% | **55.9%** (n=950) | 48.2% (n=838) |
| HTF bearish + mid | 86,435 | 50.7% | 53.4% (n=541) | 45.2% (n=549) |
| HTF bearish + premium | 61,158 | 49.0% | 53.5% (n=368) | 48.0% (n=421) |

**The sweep is not redundant.** In all six contexts it moves P(up) by +2.7 to +8.1 pp (low sweep) or −2.6 to −9.0 pp (high sweep) beyond what structure and location already say. It also reduces MFE and range in every context — consistent with BL-03.

---

## The relationship graph (§23)

```
                    LIQUIDITY POOL
                          |
                    price pokes through
                          |
                       SWEEP  ──────────────► range contracts 8–20%   [BL-03]
                          |                    (replicated, all cells)
          ┌───────────────┴───────────────┐
          |                               |
      RECLAIM                        ACCEPTANCE
   (closes back inside)          (closes stay beyond)
          |                               |
   P(up) shifts 2.7–5.8pp          ┌──────┴──────┐
   toward the swept side           |             |
        [BL-01]               DISPLACEMENT   NO DISPLACEMENT
          |                        |             |
   mean effect flips          P(up) shifts   weaker,
   with LOCATION [BL-04]      4.0–13.1pp     not replicated
   (BTC only)                 AND time to
                              resolution HALVES
                              [BL-01, BL-02]
                                   |
                              but payoff per
                              outcome moves
                              the other way [BL-05]
```

---

## Accounting

```
Stage A  marginal effects, binary observations        ~100 tests
Stage B  sweep tree, 10 branches x 3 pool timeframes    30
Stage C  location x event, 7 events x 3 locations       21
Stage E  incremental over structure+location, 6 x 4     24
replication gate, 9 statistics x 10 branches            90
                                                     ~265 tests
expected false discoveries at a=0.05                  ~13
relationships passing the pre-registered gate            6
```

The gate — sign and effect size holding in **all six era-asset cells** — is far stricter than a p-value, which is why 6 survivors out of ~265 tests is meaningful rather than expected.

**No new bugs found this phase.** Second consecutive phase, after twelve. The invariants module was not exercised because nothing was traded.

---

## Limitations

1. **Forward window fixed at 4 hours.** Relationships operating over days are invisible here.
2. **BL-04 (location flips the sign) is BTC-only** and is explicitly not a finding.
3. **DOGE produces the largest effects** (+13.1 pp) and the least stable estimates — its kurtosis is extreme.
4. **The sweep tree uses 15m pools.** 1h and 4h pools produced the same signs with insufficient n.
5. **No transaction costs anywhere.** BL-05 makes clear that costs would matter decisively; nothing here is a trade.
6. **Discovery used all of BTC.** Replication is a chronological split plus four unseen assets — weaker than a sealed holdout, which was spent earlier in this project.
7. **P(up) at a 4-hour horizon is not P(profit).** A trading layer must re-derive its own outcome definition.

---

## What this changes for the eventual trading layer

**Directional information exists and replicates — as frequency, not as expected value.** Any future layer must decide which it needs. A system that wins more often but wins smaller is not automatically better, and BL-05 quantifies the trade precisely.

**The strongest single relationship is `sweep → acceptance → displacement`**: +7.6 to +13.1 pp on P(up) *and* half the time-to-resolution, replicated in every cell. It is also the rarest (n=619 on BTC).

**Two folk beliefs are falsified by well-powered nulls:** rejection candles carry nothing (n=137,294), and sweeps precede *contraction*, not expansion.

### What I would test next

**N-1 — Extend the horizon to 1–3 days.** Every relationship here resolves within 4 hours, and BL-03 says the immediate aftermath of a sweep is quiet. The interesting behaviour may begin after that window closes.

**N-2 — Replicate BL-04 across assets.** Location flipping the sign of an event's mean effect is the single most trader-like result in this document and the only one still unreplicated.

**N-3 — Decompose BL-05.** If frequency and payoff offset almost exactly, find the conditions where they *don't*. That is where a directional edge would have to live, and it is a much narrower search than the one this project has been running.

---

*Code: `research/interp/`. Pre-specification: `research/interp/PRESPEC_BEHAVIOR.md`. Corrections log (12 entries): `research/CORRECTIONS.md`.*
