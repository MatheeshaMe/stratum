# Supply & Demand Zones — Mechanism Test

**30 August 2026 · 5 assets · 14,918 BTC 5m zones · 38,440 touch events · 2017–2026**

---

## Why this was worth testing separately

Every level-based test in this project used **clustered swing levels with `min_touches >= 2`**. That is support/resistance — and it *systematically excluded the case supply/demand theory says is the good one*.

The two theories make **opposite predictions about touch count**, which makes this a discriminating experiment rather than a descriptive one:

| | prediction about repeated touches |
|---|---|
| **Support/resistance** | Repeated holds **confirm** the level. Later touches are no weaker. |
| **Supply/demand** | Resting orders are **consumed**. First touch is strongest; the zone dies. |

So this phase tested three mechanistic predictions, not a pattern:

- **P1 — Freshness decay.** reaction(1st) > reaction(2nd) > reaction(3rd+)
- **P2 — Impulse strength proxies order size.** Bigger departure ⇒ more unfilled remainder ⇒ stronger reaction
- **P3 — Origin beats repetition.** A never-touched zone should work on its *first* visit — something S/R has no reason to predict

---

## Results, one line each

| Prediction | Verdict |
|---|---|
| **P1 freshness decay** | ✅ **CONFIRMED.** Ratio falls 1.005 → 0.865 across touches 1→6+, slope −0.0305/touch. Touch 6+ CI excludes 1.0. |
| **P2 impulse strength** | ❌ **FALSIFIED.** Impulse ≥3 ATR: 0.982. ≥4 ATR: 0.969. Top decile: 0.980. All at or *below* the random-band baseline of 0.983. |
| **P3 origin beats repetition** | ❌ **FALSIFIED.** A fresh zone scores **1.005**; a **random price band** scores **1.020**. The fresh zone is not better than nothing. |
| **Liquidity sweep compound** | ❌ **FALSIFIED AND INVERTED.** 0.880, CI [0.803, 0.996] — *significantly worse* than baseline. |
| **Trend alignment** | ✅ Only significant quality factor: 1.065, CI [1.014, 1.123] vs 0.983 baseline. But this is not a zone property. |
| **Economic edge** | ❌ **+0.005 R**, CI [−0.069, +0.080] after correcting a fill-model bug that had shown +0.179. |

**P1 is confirmed but useless.** Decay is real — later touches get progressively worse than random. But since the *first* touch is already indistinguishable from a random band, what the decay describes is a level going from "nothing" to "actively bad," not from "good" to "used up."

---

## 1. Freshness decay (the discriminating test)

Forward 48 bars (4h), MFE/MAE in ATR. Two controls, because "zones react" is meaningless without them.

| population | n | med MFE | med MAE | **MFE/MAE** | 95% CI | med net |
|---|---:|---:|---:|---:|---|---:|
| **CONTROL** random band | 14,918 | 2.96 | 2.90 | **1.020** | [0.988, 1.052] | +0.027 |
| **CONTROL** base, no impulse | 12,733 | 2.77 | 2.81 | **0.985** | [0.950, 1.015] | −0.041 |
| ZONE touch #1 | 14,440 | 3.05 | 3.03 | **1.005** | [0.969, 1.039] | +0.130 |
| ZONE touch #2 | 8,873 | 3.01 | 2.91 | 1.033 | [0.990, 1.083] | +0.276 |
| ZONE touch #3 | 5,549 | 3.02 | 3.04 | 0.995 | [0.943, 1.056] | +0.254 |
| ZONE touch #4 | 3,510 | 3.00 | 3.19 | 0.939 | [0.875, 1.001] | +0.106 |
| ZONE touch #5 | 2,207 | 3.00 | 3.23 | 0.930 | [0.857, 1.009] | +0.166 |
| **ZONE touch #6+** | 3,861 | 2.95 | 3.41 | **0.865** | **[0.816, 0.926]** | +0.206 |

Slope across touch #1→#6+: **−0.0305 per touch.** The decay the mechanism predicts is there, and support/resistance logic — which predicts flat or rising — is the theory that gets falsified by this table.

**But read the first two rows before celebrating.** A random price band scores 1.020; a fresh zone scores 1.005. The mechanism's central claim — that unfilled orders make the origin special — does not survive its own control.

---

## 2. Quality factors (first touches only, baseline 0.983)

| first-touch cut | n | MFE/MAE | 95% CI | vs base |
|---|---:|---:|---|---:|
| ALL first touches | 14,438 | 1.005 | [0.969, 1.042] | +0.022 |
| impulse ≥ 3 ATR | 3,224 | 0.982 | [0.916, 1.062] | −0.001 |
| impulse ≥ 4 ATR | 1,028 | 0.969 | [0.848, 1.120] | −0.014 |
| impulse top decile | 1,444 | 0.980 | [0.877, 1.102] | −0.003 |
| FVG present | 4,434 | 0.988 | [0.929, 1.048] | +0.005 |
| FVG ≥ 0.5 ATR | 2,063 | 0.915 | [0.839, 0.997] | −0.068 |
| impulse body ratio ≥ 0.75 | 6,800 | 0.999 | [0.943, 1.055] | +0.016 |
| impulse volume ≥ 2× base | 7,572 | 0.988 | [0.948, 1.033] | +0.005 |
| tight base (<0.5 ATR) | 3,236 | 0.994 | [0.925, 1.075] | +0.011 |
| single-bar base | 12,874 | 0.998 | [0.961, 1.038] | +0.015 |
| **trend-aligned (continuation)** | 6,625 | **1.065** | **[1.014, 1.123]** | **+0.082** ✅ |
| counter-trend | 7,813 | 0.937 | [0.898, 0.983] | −0.046 |
| **LIQUIDITY SWEEP into zone** | 1,363 | **0.880** | **[0.803, 0.996]** | **−0.103** ❌ |
| rejection candle at touch | 2,600 | 0.960 | [0.877, 1.030] | −0.023 |
| sweep + rejection | 698 | 0.932 | [0.802, 1.127] | −0.051 |

### The two findings worth arguing about

**Impulse strength does nothing.** This is the load-bearing claim of the mechanism — a bigger, more one-sided departure should mean more unfilled remainder. Across four separate ways of measuring it (ATR displacement, body ratio, volume ratio, FVG), none produces a reaction above baseline. The strongest impulses are marginally *worse*. If unfilled institutional orders were driving zone reactions, this table would look completely different.

**The liquidity sweep is inverted.** The brief calls "price swept the liquidity below the old low, THEN reacted from my demand zone" a much higher-quality signal. Measured, it is the **worst cell in the table** — 0.880, significantly below a random band. A sweep into a zone is not a trap being sprung; on this data it is a level being broken with momentum behind it, and the subsequent path is worse, not better.

---

## 3. Economic test — and the bug that decided it

Zone trading has a genuine execution advantage my earlier phases could not use: **a limit rests at the proximal edge, so entry is a maker fill by construction.** Round trip falls from 10.26 bps (taker) to 6.63 bps. That is worth 0.19 R/trade at these stop distances — the single largest execution improvement found anywhere in this project.

**5-minute zones** are decisively negative regardless:

| configuration | n | win% | EV R | 95% CI | PF |
|---|---:|---:|---:|---|---:|
| first touch, all, 2R | 10,355 | 36.8% | −0.242 | [−0.269, −0.214] | 0.72 |
| first touch, trend-aligned, 2R | 4,722 | 38.8% | −0.184 | [−0.224, −0.141] | 0.78 |
| aligned, 2R, **taker** cost | 4,722 | 38.8% | −0.374 | [−0.415, −0.331] | 0.60 |
| aligned, 2.5 ATR trailing | 4,722 | 23.9% | −0.063 | [−0.156, +0.032] | 0.93 |

Cross-asset at 5m: ETH −0.179, SOL −0.115, XRP −0.135, DOGE −0.148. All CIs exclude zero.

### The 1-hour candidate, and C9

Moving to 1h zones produced the strongest result this project has ever generated:

```
POOLED 5 assets   n=2,158   win 31.6%   EV +0.179 R   CI [+0.100, +0.258]   PF 1.24
```

Both sides positive. Broad parameter plateau. And it survived three controls — including the one that mattered most, **Control C**: strip the impulse requirement, keep the base and the alignment, and EV falls from +0.179 to −0.032. Exactly what the mechanism predicts.

Then I found the bug.

> **C9 — the stop was not live on the entry bar.** The limit fills *during* bar `i`, but the stop scan began at `i+1`. On a 1h bar whose range is routinely 1–2 ATR, price can trade to the proximal edge, continue through a zone only ~0.9 ATR deep, and take out the stop **within the same bar**. Those trades were recorded as still open and credited with the later, better path — and they are precisely the worst trades, so the bias is one-directional.

| fill model | n | win% | EV R | 95% CI | PF |
|---|---:|---:|---:|---|---:|
| optimistic (stop from bar i+1) — **the bug** | 2,158 | 31.6% | **+0.179** | [+0.100, +0.258] | 1.24 |
| **correct (stop live on the entry bar)** | 2,158 | **27.2%** | **+0.005** | **[−0.069, +0.080]** | **1.01** |

Win rate fell 4.4 points. **Same-bar stop-outs were the entire edge.**

### Corrected result

| split | n | win% | EV R | 95% CI | PF |
|---|---:|---:|---:|---|---:|
| **POOLED all 5 assets** | 2,158 | 27.2% | **+0.005** | [−0.069, +0.080] | 1.01 |
| BTC | 554 | 27.3% | −0.021 | [−0.168, +0.130] | 0.97 |
| ETH | 520 | 28.7% | +0.067 | [−0.086, +0.220] | 1.09 |
| SOL | 319 | 25.1% | −0.056 | [−0.243, +0.132] | 0.93 |
| XRP | 428 | 25.7% | −0.048 | [−0.208, +0.119] | 0.94 |
| DOGE | 337 | 28.8% | +0.075 | [−0.114, +0.274] | 1.10 |
| LONG (demand) | 1,113 | 27.7% | +0.024 | [−0.081, +0.130] | 1.03 |
| SHORT (supply) | 1,045 | 26.7% | −0.016 | [−0.124, +0.093] | 0.98 |
| 2017–2019 | 557 | 26.8% | +0.002 | [−0.141, +0.146] | 1.00 |
| 2023–2024 | 904 | 26.8% | −0.019 | [−0.136, +0.096] | 0.98 |
| 2025–2026 | 697 | 28.1% | +0.037 | [−0.091, +0.170] | 1.05 |

Every cell spans zero. Total +9.8 R over 2,158 trades with a **92.9 R maximum drawdown** and a 29-trade losing streak — the equity curve is noise around flat.

The control differential also collapses. Control A entered at the bar **close**, so its stop could never trigger on the entry bar — it was never inflated. Only the zone leg was:

```
before C9:   REAL - CONTROL A = +0.247 R   CI [+0.158, +0.335]
after  C9:   REAL - CONTROL A = +0.073 R   CI [-0.010, +0.159]
```

Parameter plateau after the fix: 2R −0.027, 3R +0.005, 4R +0.022, 5R +0.030, impulse ≥3 ATR +0.080 — all spanning zero. Removing the trend filter gives −0.089 with a CI excluding zero.

---

## 4. What is actually true about zones

**Confirmed:**
1. Zones are algorithmically detectable — 14,918 on BTC 5m, one per 3.5 hours, balanced demand/supply, 30.6% containing a fair-value gap.
2. Freshness decay is real. Repeatedly-tested zones become progressively *worse than random*. This is genuine information about when to **stop** using a level.
3. Trend alignment is the only quality factor that clears its control (1.065 vs 0.983).
4. Zone trading earns a real maker-execution advantage worth ~0.19 R/trade.

**Falsified:**
1. Fresh zones do not react more than random price bands (1.005 vs 1.020).
2. Impulse strength — the mechanism's load-bearing claim — has no measurable effect across four separate proxies.
3. Fair-value gaps do not help; large ones (≥0.5 ATR) score 0.915, below baseline.
4. Base tightness does not help.
5. The liquidity-sweep-into-zone signal is significantly *worse* than baseline.
6. No configuration at any timeframe produces expectancy with a CI above zero.

**The honest interpretation.** The reaction pattern zones display is fully explained by "price bands are ordinary, and levels degrade with use." What is *not* present is any signature of unfilled institutional orders. If large resting orders were the mechanism, impulse size would predict reaction strength. Measured four ways, it does not.

---

## 5. Limitations

1. **The sealed 2020–2022 window was spent in the prior phase.** There is no clean holdout left. Validation here is cross-asset, cross-era and parameter perturbation only — weaker than a true out-of-sample test.
2. **Zone definition is one of many.** I used body-ratio for base detection, ATR-normalised impulse thresholds, and wick-to-wick boxes. Traders differ on body-to-body vs wick-to-wick; I did not sweep that choice.
3. **Spot data, perp execution.** Path structure transfers; wick-level triggers do not.
4. **Multiple testing.** ~80 tests this phase (8 freshness rows, 20 quality cuts, 25 economic configs, 20 perturbations, 4 controls). Expected false positives at α=0.05 ≈ 4. Observed with a CI above zero after C9: **0**.
5. **HTF zone counts are small** — 353 zones on 4h BTC. The 4h results carry little weight.

---

## 6. Verdict

**DO NOT BUILD.**

Supply/demand zones as specified are **not** a monetizable edge. The mechanism's specific, testable claims fail: origin does not beat repetition, impulse strength does not scale reaction, and the liquidity-sweep compound is inverted. The one prediction that holds — freshness decay — describes levels getting worse, not better.

What survives is worth keeping as **components**, not as a strategy: the freshness counter as a veto on stale levels, trend alignment as a direction filter, and the maker-execution advantage of limit entries at a marked level. All three would need a host strategy that already has positive expectancy.

### Bug count

This is the **ninth error found in my own research code across this project, and every one of them made results look better than they were.** C9 was the most expensive: it turned a dead result into the strongest candidate I have produced, complete with a plateau, cross-asset consistency, both sides working, and three passing controls. It survived everything except a check of whether the stop could be hit on the bar the order filled.

That asymmetry — nine bugs, nine of them flattering — is the single most reliable finding in this entire project.

---

*Code: `research/zones/`. Corrections: `research/CORRECTIONS.md` §C9. Prior phases: `EDGE_REPORT.md`, `R1_REPORT.md`, `R3_REPORT.md`, `BTC_PLUS3PCT_STUDY.md`, `ACCOUNT_3PCT_STUDY.md`, `STRUCTURE_STUDY.md`, `R3_ENGINE_REPORT.md`.*
