# Stratum

**Product specification · v3.0 · 28 August 2026**
*Supersedes v1.1. Every claim in §0 was measured on 377,000 BTC 5-minute situations before this document was written.*

A **calibrated situation meter** for Hyperliquid perps.

The operator reads charts by eye. Stratum turns that language into functions, finds historical cousins of the current *situation*, and prints what happened next as frequencies — **against the base rate**, with honest sample sizes and a hard expiry on the wait.

> Engineering spec, not investment advice. Frequencies are not forecasts. Live trading can lose the entire account.

---

## 0. What I measured before rewriting this

v1.1 assumed the analog engine would find situations where the odds change. I built it — situation vector, B1–B6 buckets, triple-barrier outcomes resolved on 1m bars — and ran it over **1.88M BTC 1m bars / 377k 5m situations across two disjoint periods** (2023-01→2024-12 and 2025-01→2026-07).

### 0.1 Situations barely move the odds

Base rate, ±2 ATR barriers, 1-hour horizon: **up-first ≈ 34%, down-first ≈ 34%, still-inside ≈ 31%.**

| Bucket | LONG lift IS | LONG lift OOS | Stable? |
|---|---:|---:|---|
| B1 underside_retest | −0.7% | −2.4% | yes |
| B2 failed_high | −2.1% | −3.6% | yes |
| B3 range_low_hold | −0.8% | −1.6% | yes |
| B4 range_mid | +0.7% | +0.9% | yes |
| B5 stretch_into_shelf | −2.0% | +3.7% | **flips** |
| B6 accept_break | **+2.1%** | **+4.9%** | yes |

Ten of twelve bucket/side combinations keep their sign across periods — the buckets are **real structure**. But the effect sizes are **1–4 percentage points on a 34% base rate.** That does not pay a cost of 5–10% of R.

### 0.2 The buckets don't mean what they look like

**B2 "failed high" does not predict down.** Short lift: −0.2% (IS), −0.4% (OOS) — nothing. What B2 actually predicts is **chop**: still-inside 33.2%/37.8% vs a 31.0%/33.8% base, and the slowest resolution of any bucket (median 36–40 bars vs 30–31 for B6).

The operator's highest-conviction pattern is, measurably, *the one most likely to go nowhere*. That is worth more than any signal in this document.

### 0.3 The process is memoryless — this is the headline

Conditional on a situation being **still unresolved at bar k**, what eventually happens:

| Still open at bar | n | eventually up | eventually down | never resolves |
|---:|---:|---:|---:|---:|
| 0 | 209,728 | 46.9% | 47.0% | 6.1% |
| 3 | 204,296 | 46.8% | 47.0% | 6.2% |
| 6 | 195,999 | 46.7% | 46.8% | 6.5% |
| 12 | 176,181 | 46.5% | 46.3% | 7.2% |
| 18 | 156,683 | 46.2% | 45.7% | 8.1% |

*(OOS shown; IS is identical to within 0.4pp.)*

**Waiting changes nothing about direction.** A situation eighteen bars old carries exactly as much information as one bar old. There is no coiling, no building, no "about to go."

### 0.4 A properly-validated ML model finds nothing — and that is the useful part

Gradient boosting on 21 situation features, **purged and embargoed forward CV**, uniqueness-weighted to correct for overlapping labels, isotonic-calibrated:

| Period / side | n | base rate | **AUC** | Brier skill vs base rate |
|---|---:|---:|---:|---:|
| IS LONG | 8,721 | 28.0% | 0.504 | −0.08% |
| IS SHORT | 8,721 | 30.6% | 0.519 | −0.36% |
| OOS LONG | 18,878 | 27.6% | 0.554 | +0.49% |
| OOS SHORT | 18,878 | 27.4% | 0.555 | +0.15% |

**AUC 0.50–0.55. Brier skill ≈ 0.** Every probability threshold produces negative EV after cost.

But the calibration is **excellent** — where the model says 44.4%, the outcome is 44.4%; where it says 36.0%, the outcome is 37.0%, monotone across all ten deciles.

> The model cannot tell you *which* moments are good. It can tell you *accurately* that none of them are. **That is a product.**

### 0.5 Wait-vs-click, as expected value per opportunity

Not per trade — per *opportunity*, so a policy isn't flattered by its own selectivity. Waiting that never triggers earns zero.

| Situation | EV click | trigger rate | EV\|triggered | **EV wait** | better |
|---|---:|---:|---:|---:|---|
| B2 SHORT, close-back trigger (IS) | −0.054 | 62% | +0.071 | **+0.044** | wait |
| B2 SHORT, close-back trigger (OOS) | −0.123 | 66% | −0.203 | −0.134 | click |
| B1 SHORT, close-back (IS / OOS) | −0.035 / −0.101 | 65% / 64% | −0.039 / −0.072 | **−0.026 / −0.046** | wait |
| **B6 LONG, close-back (IS / OOS)** | −0.251 / +0.060 | **14% / 13%** | **+0.389 / +0.071** | **+0.056 / +0.009** | wait / — |
| B3 LONG, momentum (IS / OOS) | −0.045 / −0.059 | 50% / 52% | −0.081 / −0.096 | −0.041 / −0.050 | wait |

**Waiting beat clicking in 13 of 20 comparisons** — and where it won, it won because *the trigger often never fired and no trade was taken*. Not trading is worth exactly 0, which beats a negative expectation.

**Only one cell is positive in both periods: B6 accept_break LONG with a selective close-back trigger** — and note its trigger rate is 13–14%, versus 62–66% for the triggers the operator currently uses. Selectivity is doing the work, not pattern recognition. n is small (23 / 53 trades). It is a hypothesis, not an edge.

### 0.6 What this means for the product

Your question was: *"When should I take the entry, according to past behaviours?"*

The measured answer is:

> **Almost never, and the situation cannot tell you which times are the exceptions.**

That sounds like a dead end. It is the opposite. Your stated pain is:

> *"I was waiting too long to take an entry, maybe it's not a good time, but this is the right time."*

That sentence contains a belief — that a right time exists and is identifiable in the moment. §0.3 shows the process is memoryless and §0.4 shows a calibrated model cannot separate the moments. **The anxiety is caused by a false premise, and the product's job is to retire the premise with a number, in real time.**

So Stratum v3 is **not** a signal generator. It is three instruments:

| Instrument | Answers | Kills |
|---|---|---|
| **Specialness Meter** | "Is this moment different from the base rate?" | *"Am I missing it?"* |
| **Wait Clock** | "How long until this resolves, and when is it dead?" | *"Waiting feels like prison"* |
| **Cost Lens** | "What does this trade need to be worth to survive fees?" | *"A 0.2% scalp is fine"* |

v1.1's structure — situation vector, buckets, analog reports, written triggers, one-page doctrine — was correct and is kept almost intact. What changes is the **claim**: from *"cousins will tell you what happens next"* to *"cousins will tell you, honestly, that this moment is ordinary — and here is when to stop waiting."*

---

## 1. Problem (restated)

The operator sees real situations: a lost shelf tested from below, a diverged RSI, a 1m lift stalling into the underside, a swept range low.

The painful question — *"will it go to the next purple line?"* — has no answer. v1.1 already knew this and replaced it with a better question. v3 sharpens it again:

> **How different is this moment from an average moment, how long before I know, and what does it cost me to find out?**

Three failure modes, each now measurable:

| Failure | Feels like | What it actually is | Instrument |
|---|---|---|---|
| Clicking with no cousins | decisive | gambling on a 34% base rate | Specialness Meter |
| Waiting with no expiry | disciplined | an open-ended stall, since §0.3 says nothing accrues | Wait Clock |
| Taking a 0.2% scalp | active | donating 30%+ of R to fees | Cost Lens |

---

## 2. Product thesis

1. A **level** is an area where balance can change. Not a wall.
2. A **wick** is not a break. A **close** plus a failed reclaim is a break.
3. A **situation** is structure, location, regime, stretch and volume in **ATR units**, never dollars.
4. **The null hypothesis is that this moment is ordinary.** Every report states the base rate first and the situation's lift second. A table without a base rate is a lie by omission.
5. **Effect size before significance.** With 377k bars, a 0.4pp lift is "statistically significant" and economically worthless. Report lift in percentage points *and* in R after cost.
6. **Calibration over accuracy.** A model that says 40% and is right 40% of the time is useful. A model that says 70% and is right 55% is dangerous.
7. **Not trading is a measured outcome worth exactly 0**, and 0 beats most alternatives (§0.5).
8. Code does not invent strategy. Analogs advise; they never click.

---

## 3. Goals

- Label every 5m close with a situation vector and a primary bucket.
- Retrieve cousins and report forward outcomes **as lift over base rate**, with block-bootstrap intervals that respect overlapping windows.
- Serve a live **Specialness Meter**, **Wait Clock**, and **Cost Lens**.
- Compare click / wait / pass as **EV per opportunity**, net of cost.
- Maintain a calibrated probability model whose job is to be honest, not confident.
- Paper, then armed-live, under a hard micro-account risk table.
- Every threshold in TOML. Search ranges. Never auto-promote.

## 4. Non-goals

Everything in v1.1 §4, plus:

- **Any claim that the model predicts direction.** AUC is 0.50–0.55. Do not build UI that implies otherwise.
- Neural sequence models (LSTM/Transformer) on this data at this sample size. A gradient booster with a proper CV scheme already reaches the ceiling; a bigger model will only overfit more expensively.
- Reinforcement learning for entry timing. §0.3 shows the state is memoryless — there is no policy to learn.
- Chasing the B5 bucket, whose lift flips sign across periods.

---

## 5. Users and context

| Field | Value |
|---|---|
| Operator | Discretionary reader moving toward systematic rules |
| Venue | Hyperliquid L1 perps, USDC collateral |
| Language | Rust core, Python research harness, TOML config, Markdown reports |
| Account | ~$15 isolated, $1,000 as a stage not a quota |
| Identity TF | **5m** (situation), 1m execution, 1h/1d filters |
| Universe | **BTC only** until buckets are frozen |

---

## 6. Cost lens (promoted from a footnote to a first-class surface)

Hyperliquid, verified 2026-08-28: taker **4.5 bps**, maker **1.5 bps**, BTC half-spread **0.63 bps**.

Cost as a fraction of 1R, by stop width:

| Execution | RT bps | 0.4% stop | 0.6% | 0.8% | 1.0% | 1.5% | 2.0% |
|---|---:|---:|---:|---:|---:|---:|---:|
| taker in / taker out | 10.2 | **25.5%** | 17.0% | 12.7% | 10.2% | 6.8% | 5.1% |
| **maker in / taker out** | 6.6 | 16.5% | 11.0% | 8.2% | 6.6% | 4.4% | 3.3% |
| maker in / maker out | 3.0 | 7.5% | 5.0% | 3.8% | 3.0% | 2.0% | 1.5% |

> **COST-1** No trade with a stop narrower than **0.60% of price**. The OMS rejects the signal; it never widens the stop.
> **COST-2** Post-only entry is the default. A signal that must cross the spread is a signal you skip.
> **COST-3** Cost appears inside R in every report, reason string and journal card. A gross number never appears without its net.
> **COST-4** No level band, touch tolerance or trigger tighter than **25 bps** — three times the measured p95 cross-venue wick difference (8 bps). Anything tighter fits one venue's tape noise.

BTC 5m ATR is **0.146% of price** (measured). A 0.6% stop is therefore ~4 ATR on 5m. **A 5m-identity situation with a viable stop is a multi-hour trade.** This is not a contradiction in the spec; it is the geometry of the instrument.

---

## 7. Feature and level specification

Unchanged from v1.1 §9 in substance — ATR(14) Wilder, EMA 20/50 with slope and ATR-extension, RSI(14) and Stoch RSI with confirmed-swing divergence only, volume SMA/z/ratio, clustered swings with `cluster_atr` merge and TTL expiry, the five level events, four location candles gated on `at_level`.

Three corrections:

**7.1 As-of semantics are mandatory.** A pivot at bar `i` is only knowable at `i+R`. The level store exposes `levels.as_of(ts)` and may return only levels confirmed at or before `ts`. A test asserts `as_of(t)` is identical computed forward-only versus rebuilt from full history, over 1,000 random `t`. This is where look-ahead enters and it is invisible until live trading finds it.

**7.2 Band floor.** `band = max(cluster_atr × ATR, 25bps × price)` per COST-4.

**7.3 Free features v1.1 omitted.** `n` (trade count) is in every HL and Binance candle. `avg_trade_size = v/n` separates size stepping in from retail chasing. Add `oi_delta` from `activeAssetCtx` and `funding_z` from `fundingHistory` — both free, both real positioning reads.

**7.4 Deferred.** The poor-man's volume-profile heatmap. Real liquidation prints are free (Coinalyze free tier; Hyperliquid fills via the Reservoir S3 archive). Approximating them from typical-price bins is strictly worse than using them.

---

## 8. Situations and analogs — done so they cannot lie

### 8.1 Situation vector

Taken at every 5m close. Prices appear only as ATR distances and ranks.

```
loc_res_atr      loc_sup_atr      side_of_broken    ema_regime
structure_5m     rsi_zone         rsi_div           vol_state
dist_up_atr      dist_dn_atr      atr_pct           atr_z
ext_atr          up_touches       dn_touches        hour_utc   dow
ret_1_atr        ret_6_atr        ret_36_atr        rng_ratio
vol_ratio        body_frac        wick_up_frac      wick_dn_frac
avg_trade_size_z oi_delta         funding_z
```

1m contributes `m1_lift_into_level`, `m1_macd_state`, `m1_vol_pop` on the same 5m snapshot. 1h/1d contribute `h1_regime`, `h1_loc_in_range`, `d1_regime` as **filters, not identity**.

> Never search 1m analogs as the identity of a situation. 1m twins are cheap and meaningless.

### 8.2 Buckets

B1–B6 exactly as v1.1 §12.2, priority B2 > B1 > B6 > B3 > B5 > B4. Measured status:

| ID | Name | Measured verdict |
|---|---|---|
| B1 | underside_retest | Stable, tiny lift. Slightly *bearish* for longs. |
| B2 | failed_high | **Predicts chop, not direction.** Slowest resolver. |
| B3 | range_low_hold | Stable, slightly negative both sides. |
| B4 | range_mid | Stable, mildly positive both sides — because it is closest to the base rate. |
| B5 | stretch_into_shelf | **Sign flips across periods. Do not trade it.** |
| B6 | accept_break | **The only directional bucket.** LONG +2.1%/+4.9%, fastest resolver, the one positive wait-vs-click cell. |

> **BUCKET-1** A bucket definition is frozen and written down **before** its outcome table is read. A bucket defined after seeing outcomes is overfitting with extra steps.
> **BUCKET-2** Any bucket whose lift flips sign across the two validation periods is marked `UNSTABLE` in the UI and cannot be armed.

### 8.3 Triple-barrier outcomes

From analog time `t`, upper `+rr × k × ATR`, lower `−k × ATR`, vertical at `H` bars. Resolved on **1m** bars; both barriers inside one 1m bar always resolves to **the loss**.

> **LABEL-1 — the label must match the payoff.** If the report pays 1.5R, the target barrier sits at 1.5 × the stop distance. A symmetric label scored against an asymmetric payoff manufactures a false edge. *(This bug was present in my first implementation and inflated the base rate from 28% to 44%. It is the single easiest way to fool yourself here.)*

Record: `hit_upper_first`, `hit_lower_first`, `still_inside`, `bars_to_first_touch`, `MFE_atr`, `MAE_atr`, and the net-of-cost R for click / wait / pass.

### 8.4 Statistical guardrails

The four ways this engine will lie to you, and the fix for each:

> **STAT-1 — Overlapping windows are not independent.** 84 analogs over a 36-bar horizon may carry the information of ~8 observations. Never use a binomial CI. Use a **circular block bootstrap with block length = horizon**. All intervals in this document were produced that way.
>
> **STAT-2 — Always report lift over base rate.** "38% hit upper" is meaningless without "base rate 34%". The headline number is the **lift** and its interval.
>
> **STAT-3 — Effect size, not just significance.** At n = 377k a 0.4pp lift has a tiny p-value and zero value. Every lift is printed alongside **R after cost** so the operator sees whether it pays.
>
> **STAT-4 — Regime concentration check.** Report what fraction of analogs come from the top 5 calendar days. If >30%, print `CONCENTRATED` and suppress the headline percentage — those cousins are one event, not many.

Retained from v1.1: if analog count < 30, print the count and **no clean headline percentage**. Always print `still_inside`; hiding chop is how tables lie.

### 8.5 Report shape

```
SITUATION   B1 underside_retest · bullish RSI div · 1m lift stalling
BTC 5m identity · barriers ±2.0 ATR · horizon 36 bars (3h)
Analogs 84   effective n ~9 (block bootstrap)   top-5-day concentration 18% OK

                     this situation      base rate        lift
  upper first             38%  (32)          34%         +4pp  [-3, +11]
  lower first             31%  (26)          34%         -3pp  [-9,  +4]
  still inside            31%  (26)          31%          0pp

  >> NOT DISTINGUISHABLE FROM AN ORDINARY MOMENT (lift CI spans zero)

WAIT CLOCK
  median time to resolve        31 bars (2h35m)
  still unresolved at bar 12    83%
  direction if unresolved at 12  46.4% up / 47.6% down  (unchanged from bar 0)
  >> EXPIRY: bar 6. Nothing accrues after that.

COST LENS
  stop 0.42% of price -> cost is 15.7% of 1R   >> BELOW COST-1 FLOOR, REJECT
  viable stop for this ATR: >= 0.60% (4.1 ATR)

POLICIES (EV per opportunity, net of cost)
  click now                       -0.035 R
  wait for 5m close back under    -0.026 R   (trigger fires 65% of the time)
  pass                             0.000 R   << best
```

**The `>> best: pass` line is the product.** It converts "waiting feels like prison" into a measured, bounded, correct decision.

---

## 9. The ML stack

Purpose: **estimate P(target before stop) honestly and say when it is indistinguishable from the base rate.** Not to find direction.

### 9.1 Architecture — meta-labelling, not prediction

```
   primary model  = the operator's written rules (buckets + triggers)
                    decides SIDE and generates candidates
        |
        v
   secondary model = calibrated GBM
                    decides TAKE / SKIP and SIZE, never side
```

The secondary model never overrides the operator's direction. It only answers *"of the trades this situation would generate, which are worth the fee?"* This is the only ML architecture appropriate when direction is unpredictable (AUC 0.52) but cost discrimination might not be.

### 9.2 Validation — non-negotiable

- **Purged, embargoed, forward-only CV.** Contiguous time folds. Training samples whose forward window overlaps the test fold are dropped; plus an embargo of `3 × horizon`. Without purging, overlapping labels leak the answer directly.
- **Uniqueness sample weights.** Weight each label by the average inverse concurrency over its forward window, so 5,000 overlapping bars do not count as 5,000 observations.
- **Isotonic calibration** on an inner fold. The deliverable is calibration, so calibrate.
- **Two disjoint periods.** 2023–24 and 2025–26. Sign and magnitude must both survive.

### 9.3 Metrics — and the pass bar

| Metric | Meaning | Pass bar |
|---|---|---|
| **AUC** | discrimination | > 0.58 in **both** periods |
| **Brier skill vs base rate** | is it better than a constant | > +2% in both |
| **Reliability curve** | is it honest | monotone, within ±3pp across all deciles |
| **EV per opportunity at threshold** | does it pay | > 0 after cost, in both |

**Current status: AUC 0.504–0.555, Brier skill −0.36% to +0.49%, every threshold EV negative. The model FAILS the pass bar and is shipped as a calibration instrument only** — it displays "ordinary" and it is right to.

### 9.4 Techniques worth adding, with pre-registered kill criteria

| Technique | Question it answers | Kill if |
|---|---|---|
| **Conformal prediction** on MAE | "what stop covers 80% of cousins?" | empirical coverage misses nominal by >5pp |
| **Kaplan–Meier survival** on bars-to-touch | "when is this situation dead?" | curves for different buckets are within 2 bars of each other |
| **HMM regime states** (3–4 states) on ATR/return/volume | "does the base rate itself shift by regime?" | state-conditional base rates differ by <3pp |
| **Learned analog metric** (siamese / gradient-boosted proximity) | "better cousins than hand buckets?" | AUC gain over B1–B6 < 0.02 in both periods |
| **Quantile regression** on forward MFE | "what is a realistic target?" | pinball loss no better than the unconditional quantile |

> **ML-1** Any model that cannot beat "always predict the base rate" is reported to the operator **in those words**, on the live surface. Silence is how a dead model keeps its job.
> **ML-2** No model output is ever displayed as a direction, an arrow, or a colour without its base rate beside it.

---

## 10. Live surface

### 10.1 The three instruments

**Specialness Meter** — one number, updated each 5m close:

```
ORDINARY   lift CI spans zero          -> the moment is not special, act accordingly
NOTABLE    lift CI excludes zero, |lift| < 5pp  -> real but small; cost probably eats it
RARE       lift CI excludes zero, |lift| >= 5pp, n >= 30, not CONCENTRATED
UNSTABLE   bucket flips sign across periods     -> cannot be armed
THIN       n < 30                                -> count only, no percentage
```

Measured expectation: **the meter reads ORDINARY the overwhelming majority of the time.** That is the intended behaviour and it must not be tuned away.

**Wait Clock** — survival curve for the live bucket, with a hard expiry:

```
expiry_bars = the bar by which the marginal information gain is zero
```

Measured on BTC: **direction is unchanged from bar 0 to bar 18**, so the expiry is set by the *trigger* window, not by information accrual. Default `expiry_bars = 6`. When the clock hits zero the situation is marked DEAD and removed from the watchlist. **The operator is not allowed to keep staring at it.**

**Cost Lens** — live, before any click:

```
stop 0.42% -> 15.7% of R  REJECT (COST-1)
```

### 10.2 Written triggers (session rules, retained from v1.1 §13)

```
IF none of the written candles printed        -> flat is a completed session
IF one printed and I still did not click      -> fear, not discipline
IF none printed and I clicked anyway          -> gambling
IF the wait clock expired and I am still watching -> the situation is dead, close the tab
```

The fourth line is new and it is the one that addresses the operator's stated pain.

---

## 11. Where the edge could actually be

Direction is not predictable from the situation (§0.4). Four places measurement says are still open, ranked:

**11.1 Cost — proven, largest, already actionable.** Maker-only entry cuts round-trip from 10.2 to 6.6 bps; on a 1% stop that is 3.6pp of R recovered per trade, larger than any bucket lift measured. The referral code is a further permanent 4% off fees for five minutes of setup.

**11.2 Selectivity — proven, and the mechanism is not what you think.** §0.5: waiting won 13 of 20 comparisons, and it won by *not trading*. The B6 trigger that fires 13% of the time is the only positive cell; the triggers firing 62–66% are all negative. **Build triggers that fire rarely, then measure the fire rate as a first-class metric.**

**11.3 B6 accept_break LONG — one live hypothesis.** Positive EV per opportunity in both periods (+0.056 IS, +0.009 OOS), stable directional lift (+2.1% / +4.9%), fastest resolver. n is 23 / 53 trades. **Test it properly with `oi_delta` and `liq_cluster` conditioning before believing it.**

**11.4 Horizon geometry — untested, cheap, promising.** Still-inside is 31% at 1h and 55% at 3h. The vertical barrier is the dominant loss mechanism, not the stop. Sweep barrier width × horizon on the surface `(k_atr, H)` and find where `still_inside` stops dominating. This is a two-hour experiment with the harness that already exists.

**Not open:** neural sequence models, RL entry timing, B5, and any additional confluence condition — measured lifts were negative or noise.

---

## 12. Execution, OMS and risk

Unchanged from v1.1 §15 in structure. Revised numbers:

| Equity | Risk/trade | Lev cap | Daily kill |
|---|---|---|---|
| $15–30 | **2%** ($0.30) | 10× | −10% |
| $30–60 | 2.5% | 10× | −10% |
| $60–120 | 3% | 10× | −8% |
| $120–300 | 3% | 5× | −8% |
| $300–700 | 2.5% | 5× | −6% |
| $700–1000 | 2% | 3× | −5% |

v1.1 specified 10% risk per trade. Monte Carlo over 20,000 paths: at 10% risk with a *genuine* 45%/1.5R edge, **P(ruin) = 38%**; at 5%, P(ruin) = 5.5%. With no edge (the current measured state) and 10% risk, **P(ruin) = 83%**.

- Size from risk, never from leverage: `notional = risk_$ / stop_pct`. Leverage is an output.
- `stop_pct ≤ 0.40 × liquidation_distance`. Assert at order construction.
- `notional ≥ $10` (Hyperliquid minimum; exact-close reduce-only is exempt). If the risk budget implies less, **skip** — do not widen the stop.
- Partial scale-out requires **both** legs ≥ $10.
- One net position. No hedge. No add to losers, enforced in code.
- Stop is placed in the same event-loop tick as the entry fill. A supervisor asserts this every second.
- **Rate budget:** Hyperliquid allows 1 request per 1 USDC traded, +10,000 initial buffer. At $60/day volume you earn 60 requests/day. Reserve 500; refuse non-flatten actions below it. A repricing loop that burns the buffer leaves you unable to *exit*.
- Agent/API wallet only — it can trade but cannot withdraw. Never the master key on the VPS. Run NTP; nonces are ms timestamps.
- ARM mode; `auto_live = false`.

---

## 13. Architecture

```
crates/
  stratum-data         HL WS+REST, Binance Vision loader, parquet store
  stratum-features     ATR EMA RSI Stoch vol swings clusters candles
  stratum-levels       as-of level store  (LEVEL-1 assertion lives here)
  stratum-situations   vector, bucket label, analog index
  stratum-outcomes     triple barrier, block bootstrap, base rates
  stratum-ml           calibrated GBM, purged CV, conformal, survival
  stratum-backtest     1m-resolved pessimistic fills, full cost
  stratum-search       purged walk-forward, lift tables
  stratum-oms          paper + live, cloids, rate budget, kill switches
  stratum-live         SDK signing, ARM, flatten-on-disconnect

apps/
  stratum-record   WS recorder -- ships first, runs forever
  stratum-analogs  the three instruments
  stratum-replay   stratum-sweep   stratum-paper   stratum-arm

research/            Python reference harness (this document's evidence)
  situations.py  analog_report.py  wait_vs_click.py  ml_model.py  wait_clock.py
```

`signal(feat, levels, params) -> Option<Signal>` is pure. No I/O in templates.

> **DATA-1** Never compute on an unclosed bar. The HL WS `candle` channel streams the forming bar on every update.
> **DATA-2** Hyperliquid `candleSnapshot` serves a **rolling ~5000 bars per interval** (1m → 3.5 days, 5m → 17 days, 1h → 208 days). Older windows return `[]`. Deep history comes from Binance Data Vision (free, no key, checksummed, 2019→); **start the recorder on day 1** or HL data is lost permanently.

---

## 14. Build plan

**Phase 0 — recorder and history (days 1–2).** Workspace, clippy/fmt, secret scan. `stratum-record` running. Binance 1m 2023→now via `scripts/fetch_binance.py`. HL rolling backfill. Referral code applied.

**Phase 1 — levels match the eye (days 3–5).** Features, swings, clusters, as-of store with the look-ahead assertion. Overlay on 10 operator-chosen sessions. **Gate 1: operator says "these lines are what I was looking at."** Do not proceed otherwise.

**Phase 2 — the three instruments (days 6–10).** Triple barrier with LABEL-1. Base rates. Block bootstrap. Buckets B1–B6, frozen before their tables are read. Specialness Meter, Wait Clock, Cost Lens. **Gate 2: the Rust engine reproduces §0's tables from `research/` to 1e-6.** A harness that cannot reproduce a known-null result cannot be trusted with a maybe-positive one.

**Phase 3 — ML layer (days 11–16).** Purged CV, uniqueness weights, isotonic calibration. Conformal MAE intervals. Survival curves. Report against §9.3's pass bar. **Gate 3: ship it as an instrument regardless of whether it passes — but arm nothing unless it does.**

**Phase 4 — hypothesis testing (days 17–22).** B6 accept_break with `oi_delta` / `liq_cluster`. The `(k_atr, H)` horizon sweep (§11.4). Selective-trigger design with fire rate as a first-class metric. **Gate 4: a policy with positive EV per opportunity, net of cost, in both periods, n ≥ 150.** If nothing clears it, **do not trade** — return to Phase 4.

**Phase 5 — paper (days 23–36).** Live WS, simulated fills, real risk engine, real rate accounting. **Gate 5: 14 consecutive days, zero rule breaches, paper EV within 1 SE of backtest.**

**Phase 6 — armed live.** ARM only, BTC only, one policy, half table risk for 20 trades.

---

## 15. Testing

Feature tests against fixtures. **Look-ahead assertion** on `levels.as_of(t)` over 1,000 random `t`. **LABEL-1 test**: an asymmetric-payoff report must fail loudly if handed a symmetric label. Golden-file replay with reason strings in git. Base-rate invariant: every analog table's bucket counts sum to the population. Block bootstrap reproducibility under a fixed seed. Purge/embargo test: a deliberately leaked feature must show as AUC ≈ 1.0 without purging and AUC ≈ 0.5 with it. OMS property tests: no add-to-loser, no third trade, duplicate cloid never doubles, stop within one tick of any fill, stale WS cancels then flattens, rate reserve never breached. Analog report with n < 30 refuses a headline percentage.

---

## 16. Risks

| Risk | Note |
|---|---|
| **No exploitable edge exists at this identity TF** | Currently the base case. §0. Gate 4 refuses to trade without proof. |
| Operator reads ORDINARY as "the tool is broken" | It is the correct reading of the tape. Document it in the UI copy. |
| Fees consume any edge found | COST-1/2/3. Largest measured lever. |
| Overlapping-label overconfidence | STAT-1 block bootstrap, uniqueness weights. |
| Bucket defined after seeing outcomes | BUCKET-1, enforced by freezing definitions in git before tables run. |
| Label/payoff mismatch | LABEL-1. Inflated a base rate from 28% to 44% in my first pass. |
| Regime concentration | STAT-4. |
| $15 book dies on one leveraged hold | 2% risk, exchange-side stop, event window. |
| Target arithmetic tempts leverage | Monte Carlo in §12 is the argument. Caps enforced in code. |

---

## 17. One-page doctrine

```
A level is an area, not a wall.
A wick is not a break.
A situation is structure in ATR units, not a price.
The null hypothesis is that this moment is ordinary.
Report lift over base rate, or do not report.
Overlapping windows are not independent observations.
The label must match the payoff.
Direction is not predictable; cost and selectivity are.
An expired situation is dead. Close the tab.
Not trading is worth exactly zero, and zero beats most alternatives.
Flat is a position.
Search never promotes itself.
```

---

*End of specification. Stratum v3.0 — 28 August 2026.*
*§0 was measured on 1.88M BTC 1m bars across two disjoint periods. The code is in `research/`. Re-run it before you trust it.*
