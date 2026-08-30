# R-3: Monetizing Market-Structure Recognition

**30 August 2026 · 5 assets · 35,356 structural entries · 9 years + the sealed 2020–2022 window opened once**

---

## 15. FINAL VERDICT: **PROMISING BUT UNPROVEN**

The frozen hypothesis **failed** its pre-registered test on the sealed window — 2 of 4 criteria. I am not rescuing it.

But the failure is informative rather than flat. The point estimate was **positive** on the sealed data (+0.118 R/trade, PF 1.296, positive in all three years), it was positive in discovery (+0.063 R), and a post-hoc control shows the **long side beats matched random longs at p = 0.048**. What it cannot do is clear a confidence interval, work on the short side, or survive any of the four enhancements this phase was built to test.

Every one of those enhancements failed, and several failed in the opposite direction from the hypothesis:

| Phase | Hypothesis | Result |
|---|---|---|
| 3 | Better entry timing monetizes the structure | **9 variants, all negative.** MFE/MAE stays 0.93–1.08 regardless of entry |
| 4–6 | A path model finds the big winners | AUC rises with target size (0.52 → 0.62) but **Brier skill ≈ 0** |
| 7 | Ranking by P(peak ≥ 3R) is tradeable | **Selecting harder makes it worse:** −0.108 → −0.158 → −0.210 |
| 8 | Trade management rescues expectancy | Partials, pyramids, caps — none turns it positive |
| 11 | Derivatives distinguish good breakouts | All four OI×price regimes negative, three significantly |
| 19 | ML > structural rules > indicators | **C is worst.** ML made it significantly worse: −0.224 |
| 13 | The sealed trending regimes rescue it | **FAIL** on pre-registered criteria |

---

## 20. The most important experiment, answered

> *"Once the market enters a genuine directional state, is there a measurable window where the future distribution becomes asymmetric enough to profitably capture the move?"*

**Measurably asymmetric: barely, and only on the long side. Profitably: not demonstrated.**

The precise finding — and it is sharper than "markets are random" — is that **structural information is almost entirely magnitude information, and it survives every attempt to extract direction from it.**

| entry variant | fill rate | n | win% | EV/trade | med MFE | med MAE | **MFE/MAE** |
|---|---:|---:|---:|---:|---:|---:|---:|
| immediate (next open) | 98% | 8,653 | 27.5% | −0.165 | 0.71 | 0.73 | **0.98** |
| first continuation candle | 45% | 3,930 | 28.1% | −0.136 | 0.67 | 0.65 | **1.03** |
| retest of level | 86% | 7,611 | 26.0% | −0.190 | 0.71 | 0.77 | **0.93** |
| retest + rejection | 74% | 6,559 | 27.0% | −0.172 | 0.69 | 0.70 | **0.99** |
| new structural extreme | 92% | 8,139 | 25.1% | −0.135 | 0.66 | 0.61 | **1.08** |
| momentum acceleration | 69% | 6,124 | 28.2% | −0.159 | 0.65 | 0.66 | **0.99** |
| second structural confirmation | 56% | 4,974 | 27.5% | −0.173 | 0.71 | 0.72 | **0.98** |
| 0.5 ATR pullback (adaptive) | 97% | 8,578 | 27.3% | −0.166 | 0.70 | 0.71 | **0.98** |

**I expected the retest entry to break this.** Buying lower should mechanically shrink MAE. It does the opposite — MFE/MAE falls to 0.93, the worst of the nine — because a retest is itself evidence of weakness, and the structural stop does not move closer in proportion. My own hypothesis, falsified cleanly.

---

## 1–2. Market representation (Phases 1–2, preserved and extended)

`research/struct/zigzag.py`, unchanged from the prior phase. **Confirmed-only and causal**: a pivot at bar *i* is written into state at its `confirm_bar`, never its `pivot_bar` (median lag 5 bars at θ = 3.0). Violating exactly this rule produced a phantom 3,153,883× equity curve earlier in this project.

**Structure**: HH/HL vs LH/LL from confirmed pivot sequences; last and previous swing highs/lows; swing magnitude in ATR; pivot count; distance to structural level.
**Impulse**: completed leg size in ATR (`imp_atr`); leg direction; leg start index and price.
**Pullback**: `pb_frac` — retracement of the current impulse as a fraction.
**Breakout**: BOS = close beyond the last confirmed swing, rising edge only.
**Efficiency**: |net move over 60 bars| / total path length. Dimensionless, no smoothing lag, and the only trend measure that did anything.

Swing scale calibration (BTC 5m):

| θ (×ATR) | pivots | one per | confirm lag | median leg |
|---:|---:|---:|---:|---:|
| 1.0 | 358,103 | 0.1h | 1 bar | 1.8 ATR |
| 2.0 | 96,171 | 0.5h | 2 bars | 3.3 ATR |
| **3.0** | **40,881** | **1.3h** | **5 bars** | **5.1 ATR** |
| 5.0 | 14,503 | 3.6h | 16 bars | 8.5 ATR |

---

## 5. The path model (Phases 4–6)

Meta-labelling: the structural rule is the primary model; ML decides which of its signals to take. Target is the **trade outcome** — did this entry reach +*k* R before the structural stop — not next-candle direction. Purged, embargoed forward CV, pooled across 5 assets (35,356 entries).

| target | base rate | AUC (GBM) | AUC (logistic) | Brier skill |
|---|---:|---:|---:|---:|
| P(peak ≥ 0.5R) | 60.6% | 0.5248 | 0.5299 | −0.07% |
| P(peak ≥ 1.0R) | 40.0% | 0.5446 | 0.5484 | +0.28% |
| P(peak ≥ 2.0R) | 20.2% | 0.5595 | 0.5727 | +0.04% |
| P(peak ≥ 3.0R) | 11.2% | 0.5894 | 0.6048 | +0.69% |
| P(peak ≥ 5.0R) | 4.2% | 0.6245 | 0.6336 | −0.14% |

Two things worth noting. **AUC rises with target size** — the model is better at spotting which trades become large than which become marginally profitable, exactly as a trend thesis would predict. And **logistic regression matches or beats gradient boosting at every level**. The relationship is essentially linear; no model complexity is justified.

**Brier skill is ≈ 0 everywhere.** The model ranks but does not add calibrated probability, which is the first sign that the ranking will not pay.

### It does not pay — and it inverts

| rank by | slice | n | win% | EV R | 95% CI | PF |
|---|---|---:|---:|---:|---|---:|
| — | all entries | 29,464 | 29.4% | −0.108 | [−0.129, −0.084] | 0.80 |
| P(peak≥3R) | top 50% | 14,732 | 28.0% | −0.109 | [−0.147, −0.067] | 0.82 |
| P(peak≥3R) | top 20% | 5,893 | 26.1% | −0.135 | [−0.202, −0.059] | 0.80 |
| P(peak≥3R) | top 10% | 2,947 | 25.6% | −0.158 | [−0.249, −0.041] | 0.77 |
| P(peak≥3R) | **top 5%** | 1,474 | 25.7% | **−0.210** | [−0.297, −0.122] | 0.70 |

**The model that best identifies big winners produces the worst trades.** Win rate *falls* as selection tightens (29.4% → 25.7%). It finds setups with a fatter right tail *and* a higher failure rate, and the tail does not compensate. 20 rank×slice cells tested; 0 with a CI above zero.

---

## 7. Exit and trade management (Phases 7–8)

The unbounded trailing structural exit is the correct instrument and it works — individual trades reached **+161.9 R** in the pooled sample, p90 of the peak distribution is 3.17 R. The tail is real and measurable.

| management (top-10% P(peak≥3R) slice) | EV R | 95% CI | win% | PF |
|---|---:|---|---:|---:|
| baseline: full trail to structural stop | −0.158 | [−0.249, −0.041] | 25.6% | 0.77 |
| take 50% at +1R, trail remainder | −0.144 | [−0.200, −0.078] | 39.4% | 0.75 |
| take 33% at +1R, trail remainder | −0.149 | [−0.217, −0.066] | 33.8% | 0.75 |
| take 50% at +2R, trail remainder | −0.165 | [−0.229, −0.095] | 29.3% | 0.76 |
| hard cap at +3R (tail deliberately removed) | −0.161 | [−0.215, −0.108] | 26.4% | 0.77 |
| hard cap at +5R | −0.195 | [−0.253, −0.135] | 25.7% | 0.72 |

Partials raise the win rate by 14 points and cut variance; they do not create expectancy. Hard caps confirm the tail matters — removing it costs money — but not enough to matter.

---

## 9. What ML actually contributes (Phase 19)

| baseline | n | win% | EV R | 95% CI | PF |
|---|---:|---:|---:|---|---:|
| **A** EMA 9/20 cross | 6,554 | 30.9% | −0.075 | [−0.122, −0.025] | 0.87 |
| **B** trend + BOS (structural) | 3,695 | 27.7% | −0.147 | [−0.204, −0.087] | 0.75 |
| **B2** + efficiency > 0.35 | 446 | 36.8% | **+0.063** | [−0.075, +0.220] | 1.15 |
| **C** + ML path model (top 20%) | 892 | 25.8% | **−0.224** | [−0.349, −0.081] | 0.69 |

**Ordering: B2 > A > B > C.** Two uncomfortable results. The naive EMA cross **beats** the structural rule it was supposed to be worse than. And **ML makes things significantly worse** — the only cell in this table whose CI excludes zero on the negative side is the machine-learning one.

Per your rule 8: ML is not used.

---

## 11. Derivatives at the breakout

Open-interest state at the structural break, BTC, 60.2% metrics coverage on the 5m grid:

| OI × price regime at breakout | n | win% | EV R | 95% CI | PF |
|---|---:|---:|---:|---|---:|
| price UP + OI UP (new longs) | 922 | 28.3% | −0.139 | [−0.257, −0.017] | 0.77 |
| price UP + OI DOWN (short covering) | 729 | 28.3% | −0.233 | [−0.331, −0.131] | 0.62 |
| price DN + OI UP (new shorts) | 788 | 25.9% | −0.224 | [−0.319, −0.119] | 0.64 |
| price DN + OI DOWN (long liquidation) | 754 | 27.7% | −0.227 | [−0.322, −0.127] | 0.63 |

All negative, three significantly. The four-quadrant OI framework carries no tradeable information at structural breakouts. Consistent with the R-1 finding that microstructure adds nothing directional.

---

## 10 & 13. Out-of-sample: the sealed window

The hypothesis was frozen in `research/struct/FROZEN_HYPOTHESIS.md` **before any 2020–2022 data was loaded into a structural test**, with pre-registered pass criteria. The fetcher for the sealed window is a separate one-time script.

**Regime**: 2020-01-01 → 2022-12-31. BTC 7,180 → 68,734 → 16,542. +32.1%/yr, 77.3% max drawdown. The COVID crash, the 2021 bull run and the 2022 bear — the strongest trending regimes in crypto history, and precisely what a trend system should feast on.

### Result

```
n                214
win rate         39.3%
EV per trade     +0.1180 R
95% CI           [-0.0730, +0.3239]
profit factor    1.296
total R          +25.2
max drawdown     13.1 R
median hold      76 bars (6.3h)
largest winner   11.5 R

LONG   n=112   EV +0.2642 R
SHORT  n=102   EV -0.0426 R
```

| pre-registered criterion | outcome |
|---|---|
| 1. EV > 0 with 95% CI excluding zero | **FAIL** |
| 2. n ≥ 150 | PASS |
| 3. profit factor > 1.0 | PASS |
| 4. sign holds for both LONG and SHORT | **FAIL** |

**VERDICT: FAIL.**

By year: 2020 +0.051 R, 2021 +0.088 R, 2022 +0.191 R — positive in all three, every CI spanning zero. Unfiltered baseline on the same window: −0.099 R, CI [−0.172, −0.023], PF 0.824. The efficiency filter is doing real work, on 12% of signals.

### Post-hoc control (declared as post-hoc)

The long-side result is concentrated in a window where BTC rose 857% peak-to-entry, so I ran a control: random long entries with the **same holding-period and risk distributions**, same costs, same window.

```
random LONG control (400 sims):  mean -0.0508 R   p50 -0.0454   p95 +0.2607
actual structural LONG:          +0.2642 R
fraction of controls that beat it: 4.8%

random SHORT control:            mean -0.0841 R
actual structural SHORT:         -0.0426 R
fraction of controls that beat it: 35.8%
```

**The long side beats matched random longs at p ≈ 0.048; the short side does not.** This is a real diagnostic and I am reporting it — but it was run *after* seeing the result, on one window, after several hundred tests across this project. It is exactly the kind of analysis that rescues dead hypotheses, and it does not change the pre-registered verdict.

---

## 12–13. Opportunity frequency and account simulation

Trend + BOS + efficiency fires **446 times in 9 years on BTC** (≈1 every 7 days), median hold 6.3 hours.

$20 start, 200 trades (≈3–4 years at the observed rate), resampled from the empirical R distribution:

**Sealed pool** (EV +0.118 R — the most favourable estimate available):

| risk/trade | median | p25 | p75 | p5 | p95 | median DD | P(ruin) |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2% | $29.08 | $22.38 | $38.30 | $15.72 | $58.79 | 23.5% | 0.00% |
| 5% | $39.05 | $21.08 | $74.86 | $9.07 | $203.35 | 50.8% | 0.04% |
| 10% | $36.07 | $11.27 | $120.31 | $2.31 | $760.64 | 79.1% | 8.86% |
| 20% | $5.28 | $0.62 | $47.08 | $0.03 | $1,303.28 | 98.1% | 59.28% |

**Discovery pool** (EV +0.063 R): at 5% risk, median $20.70 — no growth. At 10%, median $9.75 with 28.9% ruin.

Even taking the sealed estimate at face value — an estimate whose CI spans zero — the aggressive configuration you asked for (10–20% risk) produces a median outcome of $36 or $5 against ruin probabilities of 9% and 59%. **The right tail is real (p95 of $760 at 10% risk), but the median trajectory does not compound.**

---

## 14. Failure modes — exactly where the information stops being monetizable

1. **Structure predicts magnitude, not direction.** MFE and MAE move together under every entry rule, every filter, every timeframe alignment. Ratio 0.93–1.08 across all nine entry variants.
2. **Better winner-detection is not better trade-selection.** The path model reliably ranks by peak-R potential (AUC 0.62 at 5R) and *loses more money* the harder you select on it, because the same features that predict a fat tail predict a fat failure rate.
3. **The short side does not work.** In both discovery and the sealed window, essentially all of the positive expectancy is long-side. That is drift capture, and it will invert in a bear regime.
4. **The filter that works, works by discarding 88% of signals.** Efficiency > 0.35 keeps 446 of 3,695. That is 1 trade per week, and n never becomes large enough to establish significance in any single regime.
5. **Costs.** At 10.26 bps taker round trip and a median risk of 1.40% of price, cost is ~7% of R per trade. The measured edge, where positive, is 6–12% of R. **The edge and the cost are the same size.**
6. **ML adds nothing here and actively subtracts.** Logistic ≈ GBM ≈ marginally above chance; the ML-selected slice is the worst cell in the baseline table.

---

## Accounting

```
Phase 3 entry variants                       9
Phase 4-6 path-model targets x 2 models     10
Phase 7 rank x slice cells                  20
Phase 8 management variants                  7
Phase 11 derivatives regimes                 4
Phase 19 baselines                           4
Phase 13 sealed (pre-registered)             1
prior structure phase                       65
------------------------------------------------
this phase                                 ~55
cumulative Stratum project              ~1,760 hypotheses
cells with CI above zero, this phase         0
```

The sealed window has now been **spent**. It cannot be used again.

---

## What I would do next, in order

**N-1 — Test the long-only structural system on a bear market with the filter frozen.** The single unresolved question is whether the long-side result is structure or beta. The sealed window could not answer it because BTC rose 857% inside it. The clean test is 2022 alone (already in-sample now) or a forward paper period. **Until that is answered, this is beta wearing a structure costume.**

**N-2 — Longer structural scales.** Everything here is θ = 3.0 on 5m — 1.3-hour swings, 6.3-hour holds, cost at 7% of R. At θ = 5 on 1h bars, swings run days and cost falls toward 1% of R. The measured edge would not have to grow; the cost would shrink beneath it. This is the one lever that has never been pulled and it is the same conclusion three prior phases reached from different directions.

**N-3 — Paper-trade B2 long-only, small, as a live out-of-sample.** 1 signal per week means ~50 trades a year. Two years of paper trading would produce a sample comparable to the sealed test, at zero risk, in a regime nobody has seen.

**Explicitly closed by this phase:** entry-timing optimisation, ML path models, derivatives conditioning at breakouts, trade-management variants, pyramiding, cross-asset ranking on this signal, and the short side of structural breakouts.

---

## In one paragraph

The structure engine sees what you see, the unbounded structural exit finally lets winners run to +161 R, and the path model genuinely ranks trades by how large they will get. None of it makes money. Nine entry variants leave MFE/MAE pinned between 0.93 and 1.08; selecting harder on predicted big-winners drives expectancy from −0.108 to −0.210; ML underperforms an EMA crossover; open interest adds nothing; and the frozen hypothesis, tested once on the strongest trending regimes in crypto history, returned **+0.118 R with a confidence interval spanning zero and all of its expectancy on the long side of an 857% rally**. The information is real and it is magnitude information. **It stops being monetizable at the point where you ask it which way to bet.**

---

*Code: `research/struct/`. Frozen hypothesis: `research/struct/FROZEN_HYPOTHESIS.md`. Prior phases: `EDGE_REPORT.md`, `R1_REPORT.md`, `R3_REPORT.md`, `BTC_PLUS3PCT_STUDY.md`, `ACCOUNT_3PCT_STUDY.md`, `STRUCTURE_STUDY.md`. Corrections: `research/CORRECTIONS.md`.*
