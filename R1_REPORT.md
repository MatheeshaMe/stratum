# Stratum R-1 — Microstructure & Positioning

**28 August 2026 · ~160 hypotheses · 1,334 days of order-book, open-interest, flow and funding data**

---

## VERDICT: **B** — information found, no tradeable edge

Microstructure contains **real, statistically detectable directional
information** that survives drift controls and split-half replication. It is
approximately **7× too small to pay its own transaction cost**.

The sealed 2020–2022 holdout **was not opened**. Nothing came close to
justifying it. The fetcher refuses that window in code.

---

## 1. The central question, answered directly

> *Does the missing directional information exist in microstructure that OHLCV cannot observe?*

**A little of it does. Not enough of it.**

| Horizon | AUC OHLCV | AUC micro-only | AUC both | **incremental** |
|---|---:|---:|---:|---:|
| 5 min | 0.5278 | 0.5154 | 0.5278 | **+0.0000** |
| 15 min | 0.5288 | 0.5123 | 0.5254 | −0.0034 |
| 30 min | 0.5214 | 0.5114 | 0.5207 | −0.0007 |
| 60 min | 0.5128 | 0.5056 | 0.5162 | +0.0034 |
| 180 min | 0.5217 | 0.5083 | 0.5178 | −0.0039 |

Microstructure adds **nothing** to a model that already sees OHLCV. It is not
that the variables are uninformative — micro-only reaches AUC 0.505–0.515, above
chance — it is that **price and volume already encode what the book and the
positioning series are saying.**

### The second question was the important one, and it fails harder

Resolution is strongly predictable (AUC ≈ 0.77), so the sharp test is: *within
states expected to move, does microstructure pick the direction?*

| Expected magnitude | n | AUC OHLCV | AUC +micro | delta |
|---|---:|---:|---:|---:|
| all states | 284,079 | 0.5332 | 0.5265 | **−0.0067** |
| bottom 50% (quiet) | 142,040 | 0.5338 | 0.5257 | −0.0082 |
| top 20% | 56,816 | 0.5324 | 0.5295 | −0.0028 |
| top 10% (biggest moves) | 28,408 | 0.5326 | 0.5299 | −0.0027 |

Adding microstructure makes direction prediction **worse in every magnitude
band**, including the largest moves.

---

## 2. What is real

Event-conditioned forward returns, with bootstrap block length set from the
**autocorrelation time of the conditioning variable** (see C3), a trailing-drift
control, and split-half replication:

| Event | 30m excess | 95% CI | de-trended | 1st half | 2nd half | verdict |
|---|---:|---|---:|---:|---:|---|
| **aggressive SELL flow (bottom 5%)** | **+0.049 ATR** | [+0.020, +0.076] | +0.046 | +0.032 | +0.068 | **survives everything** |
| **top traders max SHORT (bottom 5%)** | **+0.060 ATR** | [+0.006, +0.116] | +0.059 | +0.038 | +0.082 | **survives everything** |
| book imbalance shock down | −0.042 ATR | [−0.084, −0.003] | −0.037 | −0.068 | −0.011 | unstable in 2nd half |
| funding extreme low, 180m | −0.320 ATR | [−0.578, −0.045] | −0.218 | −0.307 | −0.319 | only **521 episodes**, grows with horizon |

The two survivors tell a **single coherent contrarian story**: aggressive market
buying and crowded speculative positioning are followed by mean reversion. The
univariate signs all agree — `taker_ls_ratio` AUC 0.489 (buying → down),
`new_longs` 0.489 (→ down), `long_liq` 0.511 (capitulation → up). This is
liquidity provision earning a premium for absorbing impatient flow. It is a real
market mechanism, not a curve fit.

**5 of 21 controlled cells significant against ~1.1 expected by chance.** The
information is there.

---

## 3. Why it cannot be traded

BTC 5m ATR = **15.22 bps** of price. Round-trip cost, maker-in/taker-out =
**6.63 bps**. Therefore an effect must exceed **0.436 ATR** to break even.

| Effect | ATR | bps | vs maker/maker | vs maker/taker | note |
|---|---:|---:|---:|---:|---|
| aggressive SELL flow, 30m | +0.049 | 0.75 | 0.25× | **0.11×** | survives all controls |
| top traders max SHORT, 30m | +0.060 | 0.91 | 0.30× | **0.14×** | survives all controls |
| book imb shock down, 30m | −0.042 | 0.64 | 0.21× | 0.10× | unstable |
| top traders max SHORT, 180m | +0.290 | 4.41 | 1.47× | 0.67× | CI spans zero |
| funding extreme low, 180m | −0.320 | 4.87 | 1.62× | 0.73× | 521 episodes, trend-like |

**The largest effect that survives every statistical control is 14% of the
hurdle.** The two effects large enough to matter economically are precisely the
two that fail their own statistical controls — the classic pattern.

### Combination cannot close the gap

Per Q4, before running combination searches: the three controls-surviving effects
sum to **0.151 ATR even if perfectly independent and additive** — 35% of the
hurdle. Combination is arithmetically incapable of reaching 0.436 ATR, so
running that search would only add multiple-testing risk for no possible payoff.
Not tested, deliberately.

### Even the OHLCV baseline falls short

The best directional separation found anywhere in R-1 is the OHLCV-only model's
quintile spread within high-magnitude states: +0.190 ATR top-minus-bottom. As a
long-top/short-bottom strategy that is ≈0.095 ATR per leg = **1.45 bps against
6.63 bps of cost.**

---

## 4. Temporal decay (Q7)

The surviving effects are **short-lived**: strongest at 30 minutes, gone by 60.

| Event | 30m | 60m | 180m |
|---|---:|---:|---:|
| aggressive SELL flow | **+0.049*** | +0.044 (CI spans 0) | +0.007 |
| top traders max SHORT | **+0.060*** | +0.104 (CI spans 0) | +0.290 (CI spans 0) |
| book imb shock down | **−0.042*** | −0.048 (CI spans 0) | −0.054 |

Significance lives only at the 30-minute horizon. The longer-horizon point
estimates are larger but their intervals open up — consistent with slow
positioning variables tracking regime rather than predicting it. **The
information is short-lived, which means any attempt to exploit it would demand
fast execution and pay taker cost — 10.26 bps, making the shortfall worse, not
better.**

---

## 5. Corrections made during R-1

Per the "never silently change a result" rule. Both bugs were in my own tests
and both had **inflated** the apparent finding.

| ID | Bug | Impact | Fix |
|---|---|---|---|
| **C3** | Bootstrap block length set to the forward horizon (≤3h) while conditioning variables (`funding_z`, `toptrader_sum_ls_z`) persist for days | CIs far too narrow. Headline collapsed from "20 of 65 significant vs 3.2 expected" to **"5 of 21 vs 1.1"** once corrected | Block length from integrated autocorrelation time of the event indicator, floored at 1 day; episode counts reported alongside bar counts |
| **C4** | The magnitude×direction split reported a 7.5pp spread using the combined model, with **no OHLCV-only control** | The spread was entirely OHLCV. With the control added, **OHLCV alone scores +8.5% vs the combined model's +7.4%** — microstructure was subtracting | Split run three ways on identical rows |

C3 was caught by noticing that `funding_z` produced 18,821 "independent"
observations from what are really ~521 multi-day episodes.

---

## 6. Verdict and what remains

**B — information found, no tradeable edge.** Documented, not traded.

The contrarian flow/positioning effect is real, replicates, survives drift
controls, and has a sound economic mechanism. At 0.75–0.91 bps against a
6.63 bps cost floor, it is **not exploitable at this account's fee tier on this
venue**.

### What would change the answer

The effect is fixed; the cost is not. This becomes tradeable only if cost falls
by roughly an order of magnitude:

1. **Maker-rebate venue.** At a negative maker fee the sign of the inequality can
   flip. Hyperliquid pays maker fees at every tier; this is not available here.
2. **Capturing the flow rather than following it.** The effect *is* the premium
   for providing liquidity to impatient traders. Earning it means quoting both
   sides, not taking one — a market-making problem, with adverse selection and
   latency requirements far beyond this system's scope.
3. **Higher-frequency data.** `aggTrades` (tick-level, with the buyer-maker flag)
   was fetched but not used; it would sharpen the flow measure. It cannot change
   the arithmetic by 7×.

### Closed by this phase

Order-book imbalance and depth, OI level/delta/acceleration, funding level and
change, top-trader positioning, taker flow ratio, and all combinations thereof —
as **directional** predictors at 5m–180m horizons on BTC perps.

### Still open

**R-2, longer horizons.** The hurdle scales as `1/stop_width`. At multi-day
horizons with 5–8% stops the hurdle falls to 0.1–0.3pp. Nothing in this project
has tested beyond 8 hours, and crypto momentum at weekly horizons is a
documented effect. This is now the strongest remaining hypothesis and it is the
right use of the sealed holdout — **once frozen, tested once.**

---

*The purpose of Stratum is not to make us trade. It is to determine when trading is justified by evidence. It is not.*
