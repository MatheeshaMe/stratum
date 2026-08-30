# Bitcoin +3% Event Behaviour — Empirical Study

**30 August 2026 · BTCUSDT spot 1-minute · 3,125,444 bars · 2017-08-17 → 2026-07-31**

---

## Data and discipline

| | |
|---|---|
| Instrument | Binance BTCUSDT **spot**, 1-minute klines, checksum-verified |
| Coverage | 2017-08-17 → 2026-07-31, **3,125,444 bars** (~8.9 years of data across 9 calendar years) |
| Excluded | **2020-01 → 2022-12** — reserved sealed holdout from prior Stratum phases, deliberately not opened |
| Discovery | 2017-08 → 2019-12 |
| Validation | 2023-01 → 2026-07 |
| Gaps | 22 non-contiguous joins; every lookback and forward window is checked for contiguity and dropped if it spans one |

**On the excluded window.** 2020–2022 contains the COVID crash, the 2021 bull run and the 2022 bear — regimes I would rather have. It is held out under a standing instruction from earlier phases. The cost is that "bull / bear / sideways" segmentation here rests on 2017–2019 and 2023–2026 only. If you would rather spend that holdout on this descriptive question than on a future strategy test, say so and I will re-run everything with it included; it is a one-time decision.

---

## A. Executive conclusion — the ten findings that matter

**1. The definition dominates the result. Most "+3% events" are not events.**
Under a 1-hour close-to-close definition there are **1,977 raw threshold crossings** but only **298 independent events** once you require 24 hours of separation. 85% of naive crossings are the same move counted repeatedly. Any statistic computed on raw crossings is measuring autocorrelation, not events.

**2. A +3% BTC move is a rebound, not a breakout.** This is the strongest and most counter-intuitive result in the study. Measured *before the move begins*, against 20,000 random reference points:

| | before a +3% (1h) move | random baseline | Cohen *d* |
|---|---:|---:|---:|
| prior 1h return | **−1.06%** | +0.005% | **−1.30** |
| prior 24h return | **−2.22%** | +0.25% | −0.54 |
| distance below 24h high | **−5.40%** | −2.12% | −1.40 |
| RSI(14) | **42.2** | 50.2 | −0.69 |
| above the 200-EMA | **39.8%** | 52.7% | −0.26 |
| ATR as % of price | **0.278%** | 0.100% | **+1.62** |

Every trailing return window — 5m, 15m, 30m, 1h, 4h, 12h, 24h — is **negative** before a +3% up-move. The move typically starts from local weakness, below the 200-EMA, well off the 24-hour high, in roughly **2.8× normal volatility**.

**3. That finding cannot be used to forecast, and the reason is the most important methodological point here.** §B measures **P(state | event)**. Trading requires **P(event | state)**. High volatility with price falling is *common*; a +3% hour is *rare*. Reversing the conditional without the base rate is the classic error, and §E does the reverse test properly.

**4. Volatility is by far the strongest predictor of a +3% move — and it predicts both tails equally.** Conditioning on ATR in the top 5%: **P(+3% up in 60m) / P(−3% down in 60m) = 0.99** (discovery) and **1.01** (validation). It is a near-perfect coin flip on direction with a hugely elevated chance of *some* large move. Volatility forecasts **magnitude**, not **direction** — the fifth independent confirmation of this in the Stratum project.

**5. The apparent directional signals were an artifact of overlapping windows, and I had to correct my own analysis.** A first pass showed spectacular asymmetries (`ret_1h ≥ p95` → P(+3%) = 40.0% vs P(−3%) = 7.4%). The forward label was a *trailing*-window condition evaluated forward, sharing up to **59 of 60 minutes** with the conditioning window. Corrected to a forward-only label, that ratio collapsed from **5.38× to 0.97×**. Full detail in §I and `research/CORRECTIONS.md` §C8.

**6. After +3%, forward returns are statistically indistinguishable from the unconditional baseline** at almost every horizon from 5 minutes to 7 days. For the 1-hour event class, none of the 12 horizons has an excess-return CI excluding zero.

**7. Continuation and reversal are close to symmetric.** 24 hours after a 1h +3% event: a further **+3% occurs 48.6%** of the time, a **−3% occurs 49.3%** of the time.

**8. Retracement is the modal outcome.** **46.9%** of 1h +3% moves trade back to their own pre-move starting price within 24 hours; **73.5%** do within 7 days.

**9. Only two structural conditions show a directional skew that replicates in both eras** — being near the 24-hour high (up-skewed, ratio 1.38× / 2.26×) and depressed RSI/MFI (down-skewed, 0.60× / 0.26×). Both are momentum-shaped: strength begets up-moves, weakness begets down-moves. Neither is large.

**10. Nothing here is tradeable as-is.** The one segment with a striking result (Asia session, +1.60% mean 24h forward return) rests on **n = 71** with 9 segments tested. It is a hypothesis, not a finding.

---

## B. BEFORE the +3% move

Measured at **T_ref = T0 − W**, strictly before the move begins, versus 20,000 random reference points.

### 1-hour event class (n = 294)

| feature | event mean | baseline | difference | Cohen *d* | 95% CI on difference |
|---|---:|---:|---:|---:|---|
| prior 5m return | −0.502% | +0.001% | −0.502 | **−1.94** | [−0.624, −0.394] |
| prior 15m return | −0.707% | +0.001% | −0.708 | **−1.68** | [−0.889, −0.534] |
| ATR % of price | +0.278% | +0.100% | +0.178 | **+1.62** | [+0.150, +0.209] |
| prior 30m return | −0.838% | +0.006% | −0.844 | −1.48 | [−1.051, −0.634] |
| distance from 24h high | −5.404% | −2.118% | −3.285 | −1.40 | [−3.872, −2.717] |
| prior 1h return | −1.057% | +0.005% | −1.062 | −1.30 | [−1.356, −0.776] |
| distance from 7d high | −11.745% | −5.515% | −6.230 | −1.19 | [−7.278, −5.244] |
| distance from 9h-EMA | −1.434% | +0.022% | −1.457 | −1.16 | [−1.810, −1.120] |
| 24h range % | +9.120% | +4.710% | +4.410 | +1.10 | [+3.680, +5.176] |
| prior 4h return | −1.465% | +0.036% | −1.501 | −0.76 | [−1.928, −1.096] |
| volume vs 24h average | +1.705× | +1.031× | +0.675 | +0.70 | [+0.482, +0.890] |
| RSI(14) | 42.24 | 50.22 | −7.98 | −0.69 | [−9.755, −6.234] |
| prior 24h return | −2.223% | +0.249% | −2.472 | −0.54 | [−3.234, −1.714] |
| distance from 200h-EMA | −2.491% | +0.573% | −3.064 | −0.51 | [−4.142, −2.086] |
| MFI(14) | 42.78 | 49.95 | −7.17 | −0.37 | [−9.653, −4.667] |
| 30-day trailing return (regime) | +9.59% | +7.25% | +2.34 | +0.08 | [−2.592, +7.439] (n.s.) |

### What is and is not a precursor

**Strongly associated:** elevated volatility (ATR ≈ 2.8× baseline), recent weakness across *every* trailing window, depressed RSI/MFI, position well below recent highs, elevated 24-hour range, elevated volume.

**Not associated:** the broad market regime. 30-day trailing return shows **d = +0.08**, CI spanning zero. **+3% hours are not a bull-market phenomenon.** They are a volatility phenomenon.

**Falsified:** the intuition that +3% moves emerge from quiet consolidation and breakout. `pre_compression` (24h range ÷ ATR) is **lower** before events (41.8 vs 68.0, d = −0.26) — the market is already *expanded*, not coiled. And only 45.9% of 1h events break the prior 24-hour high at all.

The 24-hour class shows the same signs with volume and RSI more prominent (vol_ratio d = +1.12, RSI d = −1.01) and price-distance terms weaker.

---

## C. DURING the move

| window | n | median max drawdown during | median impulses | fraction of move in final 20% of window | volume vs normal | broke 24h high |
|---|---:|---:|---:|---:|---:|---:|
| 5m | 87 | −0.03% | 2 | 0.00 | **8.64×** | 32.2% |
| 15m | 156 | −0.38% | 4 | 0.34 | 3.84× | 38.5% |
| 1h | 294 | −0.70% | 15 | 0.41 | 2.04× | 45.9% |
| 4h | 489 | −1.09% | 61 | 0.45 | 1.34× | 50.5% |
| 24h | 646 | −2.37% | 359 | 0.44 | 1.07× | 62.4% |

**Reading.** Fast events are near-vertical: a 5-minute +3% has essentially no drawdown, two impulses, and **8.6× normal volume**. As the window lengthens the move becomes a multi-impulse grind with proportionally more internal drawdown and less volume anomaly. The "fraction in final 20%" sits at 0.41–0.45 for all windows ≥ 15m — meaning roughly **40–45% of the entire move happens in the last fifth of the window**. These are back-loaded, accelerating moves.

**Fewer than half of 1-hour +3% moves make a new 24-hour high.** Consistent with §B: they are climbing out of a hole, not breaking out of one.

---

## D. AFTER the +3% move

### 1-hour event class (n = 294). Excess is versus 40,000 random-time forward returns.

| horizon | n | mean | median | sd | P(up) | p25 | p75 | p90 | baseline mean | excess | 95% CI on excess |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 5m | 294 | +0.031 | −0.103 | 0.853 | 44.2% | −0.38 | +0.29 | +0.97 | +0.001 | +0.030 | [−0.064, +0.126] |
| 15m | 294 | +0.017 | −0.155 | 1.153 | 42.9% | −0.61 | +0.46 | +1.44 | +0.001 | +0.016 | [−0.106, +0.146] |
| 30m | 294 | +0.089 | −0.109 | 1.569 | 47.3% | −0.72 | +0.63 | +1.74 | +0.003 | +0.086 | [−0.070, +0.240] |
| 1h | 294 | +0.047 | −0.142 | 2.024 | 45.2% | −0.85 | +0.77 | +1.66 | +0.004 | +0.043 | [−0.146, +0.238] |
| 2h | 294 | +0.196 | +0.135 | 2.431 | 53.1% | −0.89 | +0.93 | +2.60 | +0.012 | +0.184 | [−0.006, +0.381] |
| 4h | 294 | +0.206 | +0.084 | 2.616 | 52.4% | −1.16 | +1.48 | +2.97 | +0.021 | +0.186 | [−0.089, +0.449] |
| 8h | 293 | +0.106 | +0.195 | 3.299 | 52.6% | −1.80 | +1.81 | +4.15 | +0.048 | +0.059 | [−0.296, +0.420] |
| 12h | 293 | +0.090 | +0.026 | 4.069 | 50.5% | −2.19 | +2.21 | +4.49 | +0.078 | +0.012 | [−0.427, +0.399] |
| 24h | 288 | +0.532 | +0.304 | 5.326 | 53.1% | −2.12 | +3.34 | +6.62 | +0.153 | +0.380 | [−0.080, +0.860] |
| 48h | 282 | +0.346 | −0.120 | 6.705 | 48.9% | −3.12 | +3.91 | +8.85 | +0.297 | +0.049 | [−0.602, +0.728] |
| 72h | 277 | +0.650 | +0.149 | 8.115 | 50.5% | −3.38 | +5.35 | +9.89 | +0.447 | +0.203 | [−0.756, +1.234] |
| 7d | 260 | +0.685 | −0.126 | 11.080 | 49.2% | −6.22 | +6.05 | +15.21 | +1.053 | −0.367 | [−2.347, +1.759] |

**Not one horizon has an excess CI excluding zero.** Note also that at 5m–1h the **median is negative** while the mean is positive and P(up) is only 43–47%: a slight tendency to drift down immediately, with a fat right tail pulling the mean up.

For the **24-hour** event class four horizons do reach significance (1h +0.086, 2h +0.123, 8h +0.183, 12h +0.226, all CIs above zero) — but that is 4 significant of 36 horizon-class cells tested, against ~1.8 expected by chance, and the effect sizes are ~0.1–0.2% before any cost.

### Continuation vs reversal — 1-hour class

| horizon | +1% | +2% | +3% | +5% | +10% | −1% | −2% | −3% | back to start price |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1h | 45.6% | 22.4% | 11.2% | 3.4% | 1.0% | 49.7% | 19.4% | 9.2% | 7.8% |
| 4h | 65.6% | 38.4% | 21.4% | 8.2% | 2.4% | 63.6% | 37.1% | 21.8% | 20.1% |
| 24h | 81.9% | 64.6% | 48.6% | 31.6% | 8.7% | 79.2% | 61.8% | 49.3% | **46.9%** |
| 48h | 87.6% | 73.4% | 57.8% | 39.4% | 16.7% | 87.2% | 73.0% | 59.6% | 57.1% |
| 7d | 94.6% | 82.7% | 72.3% | 57.7% | 35.8% | 91.9% | 83.8% | 76.5% | **73.5%** |

**The up and down columns are nearly identical at every horizon.** At 24h: +3% in 48.6% of cases, −3% in 49.3%. This is what a martingale with elevated volatility looks like.

### Normalised path — 24h event class (price = 100 at T0, n = 646)

| point | median | p10 | p25 | p75 | p90 | % above T0 |
|---|---:|---:|---:|---:|---:|---:|
| T−24h | 96.99 | 96.64 | 96.86 | 97.05 | 97.07 | 0.0% |
| T−12h | 97.95 | 95.99 | 96.90 | 99.16 | 100.35 | 13.3% |
| T−4h | 98.74 | 96.47 | 97.64 | 99.74 | 100.46 | 18.4% |
| T−1h | 99.36 | 97.58 | 98.56 | 99.94 | 100.38 | 21.8% |
| T−15m | 99.64 | 98.52 | 99.17 | 99.98 | 100.23 | 22.9% |
| **T0** | **100.00** | — | — | — | — | — |
| T+15m | 99.98 | 99.48 | 99.76 | 100.22 | 100.51 | 47.8% |
| T+1h | 99.98 | 99.12 | 99.61 | 100.41 | 101.19 | 47.4% |
| T+4h | 99.96 | 98.48 | 99.32 | 100.86 | 101.96 | 48.6% |
| T+24h | 99.93 | 96.05 | 98.19 | 101.94 | 105.15 | 49.1% |
| T+7d | 100.21 | 90.11 | 95.42 | 105.60 | 114.76 | 51.5% |

The pre-event path is a smooth monotone climb (96.99 → 100). The post-event path is **flat at the median and fans out symmetrically**: by T+7d the p10/p90 band is 90.1 / 114.8 around a median of 100.2. The event marks a **volatility regime**, not a direction.

---

## E. Conditional behaviour — P(event | state), the direction that matters

Forward-only label (C8-corrected): a +3% UP event is `max(High[i+1..i+60]) / Close[i] − 1 ≥ +3%`; DOWN is the mirror. Conditions are quantile cuts fixed on the **discovery** set.

Base rates: discovery **4.21%**, validation **0.454%**. (2017–2019 was ~9× more prone to 3% hours than 2023–2026. Lift multiples are therefore *not* comparable across eras — only within.)

### Volatility predicts magnitude, not direction

| condition | era | P(+3%) | P(−3%) | up/down ratio | 95% CI |
|---|---|---:|---:|---:|---|
| ATR ≥ p95 | discovery | 12.7% | 12.8% | **0.99** | — |
| ATR ≥ p95 | validation | 3.11% | 3.09% | **1.01** | — |
| ATR ≤ p05 | discovery | 0.09% | 0.30% | 0.30 | — |
| high ATR & high volume | validation | — | — | **0.76** | — |

Volatility conditioning raises P(+3%) by up to **76× over base rate in validation** and leaves the direction a coin flip.

### The only conditions with a replicating directional skew

Of **46 conditions tested in both eras, 7 show a directional up/down skew whose CI excludes ±15% around 1.0 in both**:

| condition | discovery up/dn | validation up/dn | direction |
|---|---:|---:|---|
| MFI ≤ p05 | 0.48 | 0.23 | down |
| MFI ≤ p10 | 0.55 | 0.24 | down |
| RSI ≤ p05 | 0.60 | 0.26 | down |
| 24h range ≤ p10 | 0.60 | 0.35 | down |
| RSI ≤ p10 | 0.66 | 0.27 | down |
| prior 1h return ≤ p10 | 0.76 | 0.42 | down |
| **distance from 24h high ≥ p90** | **1.38** | **2.26** | **up** |

Six of seven are **downside** skews from weak/oversold states; only one — proximity to the 24-hour high — is an upside skew. Both patterns are momentum-shaped: **strength precedes up-moves, weakness precedes down-moves.**

Note this is the *opposite* of §B's profile, and both are correct. Conditional on a +3% move occurring, it usually started from weakness (§B). Conditional on being weak, a down-move is more likely than an up-move (§E). The resolution is the base rate: weakness is common, +3% hours are rare, and most weakness resolves downward.

---

## F. Event archetypes (1h class, rules fixed before inspection)

| archetype | n | share | median prior 24h | median max DD during | volume × | median fwd 4h | median fwd 24h | P(up 24h) | full retrace ≤7d |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| breakout to new 24h high | 133 | 45.2% | +1.47% | −0.52% | 2.49× | +0.38% | +0.48% | 53.4% | **65.4%** |
| recovery / V-bounce | 106 | 36.1% | **−7.94%** | −1.15% | 1.93× | −0.06% | +0.48% | 54.7% | **84.0%** |
| unclassified | 41 | 13.9% | −1.74% | −0.86% | 1.49× | −0.18% | −0.77% | 43.9% | 80.5% |
| grind (no pullback) | 13 | 4.4% | −1.74% | −0.37% | 1.29× | −0.42% | −1.03% | 38.5% | 92.3% |

Only two archetypes carry meaningful mass. They arrive at the same forward median (+0.48% at 24h) by different routes but differ sharply in durability: **65% of breakouts fully retrace within a week versus 84% of V-bounces.** The V-bounce is the more fragile of the two.

*A "short squeeze" and a "news spike" archetype could not be separated: without historical funding, open-interest and liquidation data for the spot series, they are not distinguishable from a vertical volume-spike move. I did not create categories the data cannot support.*

---

## G. Segmentation

| segment | n | median fwd 4h | median fwd 24h | P(up 24h) | P(further +3% ≤24h) | P(full retrace ≤7d) |
|---|---:|---:|---:|---:|---:|---:|
| **ALL** | 294 | +0.08% | +0.30% | 52.0% | 47.6% | 75.2% |
| above 200-EMA at T_ref | 117 | +0.14% | +0.24% | 50.4% | 45.3% | 71.8% |
| below 200-EMA at T_ref | 177 | +0.06% | +0.38% | 53.1% | 49.2% | 77.4% |
| bull regime (30d > +10%) | 109 | +0.25% | +0.74% | 54.1% | 49.5% | 76.1% |
| bear regime (30d < −10%) | 108 | +0.10% | +0.55% | 56.5% | 50.9% | 75.0% |
| sideways (\|30d\| ≤ 10%) | 65 | −0.15% | −0.63% | 44.6% | 38.5% | 70.8% |
| high vol (ATR > median) | 147 | −0.17% | +0.43% | 52.4% | 52.4% | **83.7%** |
| low vol (ATR ≤ median) | 147 | +0.25% | +0.25% | 51.7% | 42.9% | 66.7% |
| broke 24h high | 135 | +0.38% | +0.53% | 54.1% | 46.7% | 64.4% |
| did not break 24h high | 159 | −0.18% | +0.08% | 50.3% | 48.4% | **84.3%** |
| deep prior drawdown (<−5%) | 130 | −0.06% | +0.48% | 53.1% | 52.3% | 83.8% |
| **Asia 00–08 UTC** | 71 | +0.07% | **+1.68%** | **64.8%** | 62.0% | 74.6% |
| Europe 08–13 UTC | 55 | +0.12% | +0.34% | 52.7% | 43.6% | 70.9% |
| US 13–21 UTC | 125 | +0.25% | −0.08% | 48.0% | 43.2% | 78.4% |

### Significance on the notable segments (mean fwd 24h, bootstrap CI)

| segment | n | mean | 95% CI | 2017–19 | 2023–26 |
|---|---:|---:|---|---:|---:|
| ALL | 294 | +0.532 | [−0.076, +1.140] | 213 / +0.49 | 75 / +0.65 |
| **Asia 00–08 UTC** | 71 | **+1.600** | **[+0.294, +2.841]** | 55 / +1.37 | **16 / +2.39** |
| **broke 24h high** | 135 | **+0.817** | **[+0.077, +1.593]** | 89 / +0.98 | 44 / +0.49 |
| US 13–21 UTC | 125 | +0.209 | [−0.725, +1.127] | 81 / +0.21 | 41 / +0.21 |
| sideways | 65 | +0.108 | [−0.959, +1.198] | 41 / +0.31 | 24 / −0.23 |

P(up at 24h), Wilson CI: Asia **64.8%** [53.2%, 74.9%]; all events 53.1% [47.4%, 58.8%].

**2 of 9 segments significant against ~0.5 expected by chance.** The Asia-session effect keeps its sign in both eras but rests on **n = 71 overall and n = 16 in the recent era**. Treat it as the study's single most interesting untested hypothesis, not as a result.

---

## H. Event counts by definition

| window | method | raw crossings | ≥W apart | ≥24h apart | events/yr | median gap |
|---|---|---:|---:|---:|---:|---:|
| 5m | C2C | 234 | 212 | 88 | 9.8 | 9.0 d |
| 5m | L2H | 568 | 513 | 139 | 15.5 | 4.6 d |
| 15m | C2C | 631 | 416 | 160 | 17.9 | 3.2 d |
| 1h | **C2C** | 1,977 | 738 | **298** | 33.3 | 2.5 d |
| 1h | L2H | 2,894 | 1,234 | 400 | 44.7 | 2.0 d |
| 1h | O2H | 2,135 | 833 | 326 | 36.4 | 2.3 d |
| 4h | C2C | 4,584 | 920 | 494 | 55.2 | 2.0 d |
| 24h | C2C | 8,000 | 650 | 650 | 72.6 | 2.1 d |

**Which definition is cleanest?** **Close-to-close with a 24-hour separation rule.** It is unambiguous, causal, produces exactly one timestamp per event, and is symmetric (the identical rule defines a −3% event, which §E requires). Trailing-low-to-high (L2H) generates 35% more events by catching V-shaped recoveries measured from a local low, but the reference point is itself path-dependent, which makes the "before" analysis ambiguous. Open-to-high overlaps C2C 79% of the time and adds nothing.

**Overlap handling changes results materially**: on raw crossings the 1h class shows strong short-horizon serial correlation that is entirely an artifact of the same move being counted 6–7 times. All results above use the ≥24h-separated set.

---

## I. Limitations

**1. Overlap contamination — a bug I introduced and corrected mid-study (C8).** My first conditional analysis used a *trailing*-window forward label, sharing up to 59 of 60 minutes with the conditioning window. It produced spectacular directional asymmetries (`ret_1h ≥ p95` → up/down ratio 5.38×). Under the corrected forward-only label that ratio is **0.97×**. Anyone repeating this study should expect the same trap. Logged in `research/CORRECTIONS.md` §C8.

**2. The sealed 2020–2022 window is excluded**, removing the COVID crash, the 2021 bull and the 2022 bear. Regime segmentation is weaker for it, and "bull/bear" here means 2017–2019 and 2023–2026 only.

**3. Base rates differ ~9× between eras** (4.21% vs 0.454%). Lift multiples are comparable *within* an era, never across. This is a real regime shift in BTC's volatility, not a data problem.

**4. P(state | event) ≠ P(event | state).** §B is descriptive only. It is the single easiest way to misread this study.

**5. Multiple testing.** ~46 conditions × 2 eras, ~36 horizon cells, 9 segments, 4 archetypes ≈ 190 tests. Expected false positives at α = 0.05 ≈ 9–10. Observed replicating directional conditions: 7. Observed significant segments: 2 vs ~0.5 expected. Anything reported as significant here should be read against that.

**6. Small samples in the fast classes.** 5m: n = 88. 15m: n = 160. Asia segment: n = 71 (16 post-2023).

**7. Spot data only.** No historical funding, open interest, or liquidation series for this instrument, so short-squeeze and news-spike archetypes could not be separated, and derivatives-based precursors are untested.

**8. Survivorship / venue.** Binance BTCUSDT only; 2017–2019 Binance was a smaller share of global volume, and its microstructure differs from today's.

**9. No cost or execution modelling.** This is a descriptive study. Every number is gross. The prior Stratum phases established that round-trip cost is 3.0–10.3 bps and that this exceeds every conditional effect measured so far.

**10. 22 data gaps.** Handled by dropping any window spanning one, but the 2020–2022 seam is a 1,578,241-minute discontinuity and no window crosses it.

---

## J. Trading implications — stated as testable hypotheses only

The data does **not** support "buy after +3%" or "short after +3%." Forward returns are indistinguishable from baseline, and continuation/reversal are symmetric to within 1 percentage point.

Three hypotheses worth formal testing, ranked:

**H-1 (strongest, but note it is a *magnitude* claim).** ATR percentile is a powerful conditioner of large-move probability — 76× lift at p95 in validation — with an up/down ratio of 1.01. **Testable use: a participation filter or a volatility-scaled barrier system, not a direction signal.** Consistent with the AUC 0.775 magnitude result from R-0.

**H-2 (the one replicating up-skew).** Proximity to the 24-hour high raises the up/down ratio to 1.38× (discovery) and 2.26× (validation). Small, momentum-shaped, and the only upside skew that replicated. Requires the full cost hurdle test.

**H-3 (weakest, most interesting).** Asia-session (00–08 UTC) +3% events show +1.60% mean 24h forward return and 64.8% P(up), sign-stable across eras. **n = 71.** This needs an independent sample before it means anything — the natural candidate is the sealed 2020–2022 window, and it would be a defensible use of a one-shot holdout because the hypothesis is now frozen in writing.

**Explicitly not supported:** buying breakouts after +3%, fading +3% moves, using RSI/MFI extremes for upside timing, or treating +3% as a bull-market signal (regime shows Cohen *d* = +0.08, n.s.).

---

## K. The typical +3% event, in one paragraph

A typical +3% BTC hour begins in a market running at **2.8× normal volatility**, after price has fallen across **every** trailing window from 5 minutes to 24 hours, sitting **5.4% below its 24-hour high** and **11.7% below its 7-day high**, with RSI near **42** and volume already **1.7× normal**. The move itself takes about **15 impulses**, carries a **−0.70%** internal drawdown, runs on **2× normal volume**, back-loads **41% of its gain into the final 20% of the window**, and **fails to make a new 24-hour high 54% of the time**. Immediately afterwards price does essentially nothing at the median, with a slight downward tilt (P(up) at 1h = **45.2%**). Over the following 24 hours a further **+3% occurs 48.6%** of the time and a **−3% occurs 49.3%** — a coin flip. And within 7 days, **73.5%** of these moves have traded all the way back to where they started.

*The +3% move is a volatility event wearing a directional costume.*

---

*Code: `research/btc3/`. Data: `scripts/fetch_spot.py` (free, no key, checksum-verified). Corrections log: `research/CORRECTIONS.md`.*
