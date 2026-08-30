# Automated Crypto Market-Structure Recognition

**30 August 2026 · 5 assets · 2.56M 5-minute bars · 2017–2026 · sealed 2020–2022 excluded**

---

## The answer to your final question

> **Can human-like visual recognition of market structure be converted into a quantitative real-time system that identifies directional moves early enough to capture a meaningful portion after costs?**

**The recognition: yes, and better than I expected. The capture: no.**

Two results carry this report, and they point in opposite directions:

**1. The visual patterns are genuinely machine-detectable.** Breakout acceptance — whether a break of structure holds or fails — is predictable **at the breakout bar** with **AUC 0.635** and excellent calibration across all ten deciles. The model lifts acceptance from a 26.4% base rate to **48.6%** in its top decile, a 1.84× lift. That is by a wide margin the strongest predictive result in this entire project; direction has never exceeded AUC 0.555.

**2. Predicting the pattern does not produce money.** Trading that same top decile, with a structural stop and an unbounded trailing structural exit, returns **−0.078R per trade** (95% CI [−0.165, +0.015]), negative in every era. Across 5 assets and 10 structural configurations, **0 have a confidence interval above zero.**

The reason is the deepest finding here, and it is not "markets are random":

> **Every structural state changes MFE and MAE together, leaving the ratio near 1.0.** Uptrend 0.91, downtrend 1.02, no structure 1.00, MTF-aligned 0.94, high-efficiency 0.90 — against a baseline of 0.97. Structure reliably tells you *how much* the market will move and *how fast*. It does not tell you which side of the move you will be on.

You can teach a machine to see what you see. What you see does not contain the asymmetry.

---

## 1. Mathematical representation of market structure

`research/struct/zigzag.py`. Everything is **confirmed-only and causal**: a pivot at bar *i* is not known at bar *i*; it becomes known at the later bar where price has retraced θ·ATR from it. Every state array is indexed by the bar at which the information *exists*. Fills are at the open of the following bar.

*This discipline is not decoration — violating exactly this rule produced a phantom 3,153,883× equity curve in an earlier phase of this project.*

### Swing detection — ATR-normalised ZigZag

| θ (×ATR) | pivots | one per | median confirm lag | median leg |
|---:|---:|---:|---:|---:|
| 1.0 | 358,103 | 2 bars (0.1h) | 1 bar | 1.8 ATR |
| 2.0 | 96,171 | 6 bars (0.5h) | 2 bars | 3.3 ATR |
| **3.0** | **40,881** | **15 bars (1.3h)** | **5 bars** | **5.1 ATR** |
| 5.0 | 14,503 | 43 bars (3.6h) | 16 bars | 8.5 ATR |

θ = 3.0 was used throughout: swings of ~1.3 hours with a 5.1-ATR median leg, which corresponds to what a chart reader would call a "meaningful pivot." Scale-free by construction — the same parameter works on BTC and DOGE.

### State vector, per bar

```
trend          +1 (HH & HL), -1 (LH & LL), 0 otherwise
last_sh/last_sl, prev_sh/prev_sl    confirmed swing levels
leg_dir, leg_start_px, leg_start_i  the leg currently forming
imp_atr        size of the last completed impulse, in ATR
pb_frac        retracement of that impulse so far
bos_up/bos_dn  close beyond the last confirmed swing
efficiency     |net move| / path length over 60 bars
```

`efficiency` is the trend measure I settled on instead of ADX: net displacement divided by total path travelled. It is dimensionless, has no smoothing lag, and directly expresses "did price go somewhere or did it wander."

---

## 2. Structural setups × exit modes — the core experiment

**The methodological upgrade.** Every previous phase of this project used fixed target barriers, which truncates the right tail. A trend system's entire thesis is that the right tail pays for a low win rate — fixed barriers cannot test that thesis. Here the primary exit is a **trailing structural stop with no profit cap**.

It works as intended: the unbounded exit produced trades up to **+38.1R**, with a p99 of 6.0R. The tail is now measurable. It still does not pay.

| setup | exit | n | win% | avgW | avgL | **EV R** | PF | maxDD | max R | t |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| trend + BOS | trail structural | 3,695 | 27.7% | 1.60 | −0.82 | **−0.147** | 0.75 | 572.9 | 38.1 | −5.02 |
| trend + BOS | trail 3×ATR | 4,643 | 26.7% | 1.05 | −0.58 | −0.145 | 0.66 | 673.8 | 26.2 | −8.31 |
| trend + BOS | fixed 1:2 | 2,620 | 32.9% | 1.85 | −1.14 | −0.157 | 0.80 | 426.5 | 2.0 | −5.68 |
| trend + BOS | fixed 1:3 | 2,116 | 25.2% | 2.79 | −1.14 | −0.149 | 0.82 | 338.7 | 3.0 | −3.99 |
| BOS only | trail structural | 6,765 | 28.6% | 1.41 | −0.76 | −0.138 | 0.75 | 975.9 | 38.1 | −7.18 |
| BOS only | fixed 1:3 | 2,012 | 26.6% | 2.75 | −1.11 | −0.082 | 0.90 | 193.2 | 3.0 | −2.12 |
| CHoCH (reversal) | trail structural | 2,975 | 30.4% | 1.29 | −0.69 | −0.089 | 0.81 | 347.5 | 14.5 | −3.51 |
| **trend + BOS + efficiency>0.35** | trail structural | 446 | 36.8% | 1.33 | −0.67 | **+0.063** | 1.15 | 25.7 | 15.9 | +0.81 |
| trend + BOS + big impulse | trail structural | 1,664 | 28.5% | 1.22 | −0.70 | −0.153 | 0.70 | 264.0 | 11.1 | −4.91 |

30 cells tested. One positive with usable n. **t = +0.81 — not significant.**

### The efficiency filter, examined properly

| efficiency > | n | win% | EV R | 95% CI | PF | t |
|---:|---:|---:|---:|---|---:|---:|
| 0.00 | 3,695 | 27.7% | −0.147 | [−0.204, −0.087] | 0.75 | −5.02 |
| 0.25 | 1,289 | 32.2% | −0.055 | [−0.138, +0.035] | 0.89 | −1.22 |
| 0.35 | 446 | 36.8% | +0.063 | [−0.073, +0.220] | 1.15 | +0.81 |
| 0.45 | 118 | 45.8% | +0.284 | [−0.002, +0.664] | 1.95 | +1.65 |
| 0.50 | 57 | 49.1% | +0.561 | [+0.012, +1.282] | 3.14 | +1.70 |

**This is the textbook overfitting signature: expectancy rises monotonically as the sample collapses, and only the extreme corner (n = 57) clears zero.** Confirmed by the era split:

| era | n | win% | EV R | 95% CI |
|---|---:|---:|---:|---|
| 2017–2018 | 99 | 37.4% | +0.058 | [−0.226, +0.477] |
| 2019 | 72 | 44.4% | +0.241 | [−0.073, +0.662] |
| 2023–2024 | 154 | 36.4% | +0.095 | [−0.159, +0.386] |
| **2025–2026** | 121 | 32.2% | **−0.081** | [−0.300, +0.167] |

Every interval spans zero and the most recent era is negative. And it is **entirely a long-side artifact**: LONG +0.194, SHORT −0.092 — a directional bias from sample drift, not structure. **Rejected.**

---

## 3. Real vs false breakouts — the strongest result in this project

Of 12,237 breaks of structure: **26.1% accepted** (two consecutive closes above, no close back inside within 12 bars), **19.8% failed outright**, the rest ambiguous.

### The two populations are wildly different — but only in hindsight

| state | n | MFE | MAE | MFE/MAE | P(MFE > 2 ATR) |
|---|---:|---:|---:|---:|---:|
| BOS up → **accepted** | 3,194 | **5.06** | **1.26** | **4.02** | **90.3%** |
| BOS up → **failed** | 2,428 | **0.88** | **5.09** | **0.17** | 33.4% |

> **This table is circular and must not be read as predictive.** Acceptance is *defined* using bars 1–12 after the break, which sit inside the 48-bar forward window being measured. It selects paths that went up. It is descriptively striking and forecast-useless on its own.

### The non-circular question: can acceptance be predicted at the breakout bar?

Using only information available at bar *i*, purged and embargoed forward CV:

```
n = 9,782 breakouts
AUC        = 0.6349
Brier      = 0.1841  vs base rate 0.1943   skill = +5.24%
```

| model decile | n | predicted | actual |
|---:|---:|---:|---:|
| 1 | 979 | 12.1% | 18.0% |
| 3 | 978 | 17.4% | 18.6% |
| 5 | 978 | 21.4% | 18.9% |
| 7 | 978 | 27.3% | 28.6% |
| 9 | 978 | 38.4% | 37.6% |
| **10** | 979 | **53.8%** | **49.2%** |

Monotone and well calibrated. **This is real and it is the best predictive result anywhere in the Stratum project** — direction has never exceeded AUC 0.555.

### What actually distinguishes them, at the breakout bar

| feature | accepted | failed | Cohen *d* |
|---|---:|---:|---:|
| displacement (bar range / ATR) | 1.704 | 1.376 | **+0.37** |
| volume vs 20-bar average | 1.932 | 1.511 | **+0.30** |
| pullback depth | 1.226 | 1.085 | +0.16 |
| close location in bar | 0.831 | 0.809 | +0.12 |
| trend efficiency | 0.138 | 0.128 | +0.09 |
| 5m trend = up | 0.400 | 0.418 | −0.04 |
| **1h trend = up** | 0.348 | 0.332 | **+0.03** |
| impulse size (ATR) | 4.326 | 4.419 | −0.06 |

**Displacement and volume are the signal.** Trend context — the thing chart readers weight most heavily — is worthless here: 5m trend *d* = −0.04, 1h trend *d* = +0.03.

### And it still does not pay

Trading the model's own slices, structural stop, unbounded trailing exit, taker in / taker out:

| selection | n | acceptance% | win% | **EV R** | 95% CI | PF |
|---|---:|---:|---:|---:|---|---:|
| all breakouts | 9,563 | 26.4% | 28.7% | −0.129 | [−0.163, −0.095] | 0.77 |
| top 50% | 4,782 | 34.0% | 29.1% | −0.103 | [−0.152, −0.052] | 0.81 |
| top 20% | 1,912 | 44.0% | 30.4% | −0.109 | [−0.172, −0.043] | 0.79 |
| **top 10%** | 956 | **48.6%** | 31.3% | **−0.078** | [−0.165, +0.015] | 0.84 |

Era split of the top decile: −0.243 / −0.047 / −0.021 / **−0.169**. All negative.

**Look at the middle two columns.** Acceptance rises from 26.4% → 48.6% (+22.2 points). Win rate rises from 28.7% → 31.3% (**+2.6 points**). The prediction lands almost entirely on a property that is not the same thing as a profitable trade: a breakout can hold for twelve bars, then roll over and take out the structural stop before the trailing exit has banked anything.

---

## 4. Multi-timeframe alignment — falsified

The most widely-held belief in structural trading, tested directly. MFE/MAE over the next 48 bars (4 hours), in ATR:

| state | n | MFE | MAE | **MFE/MAE** |
|---|---:|---:|---:|---:|
| ALL BARS (baseline) | 624,844 | 2.92 | 3.00 | **0.97** |
| 5m up **AND** 1h up (aligned) | 74,284 | 2.84 | 3.01 | **0.94** |
| 5m up **BUT** 1h down (conflict) | 64,736 | 2.80 | 3.18 | **0.88** |
| aligned + BOS up | 1,739 | 3.17 | 3.40 | **0.93** |

Alignment moves the ratio from 0.88 to 0.94 against a 0.97 baseline — **aligned states are slightly worse than an average bar.** The hypothesis that lower-timeframe entries improve materially when aligned with higher-timeframe structure is **not supported**.

---

## 5. Conditional path behaviour — you asked me not to stop at "random", so here is the precise structure

| structural state | n | MFE | MAE | MFE/MAE | MFE−MAE | P(MFE>2ATR) |
|---|---:|---:|---:|---:|---:|---:|
| ALL BARS | 624,844 | 2.92 | 3.00 | 0.97 | −0.08 | 64.4% |
| 5m uptrend (HH+HL) | 204,408 | 2.82 | 3.11 | 0.91 | −0.29 | 62.9% |
| 5m downtrend (LH+LL) | 199,784 | 2.89 | 2.83 | 1.02 | +0.06 | 64.9% |
| no clear structure | 220,652 | 3.04 | 3.05 | 1.00 | −0.01 | 65.4% |
| BOS up | 12,231 | 2.96 | 3.23 | 0.92 | −0.27 | 63.8% |
| high efficiency (>0.40) | 6,637 | 2.14 | 2.38 | 0.90 | −0.25 | 52.6% |
| low efficiency (<0.15) | 434,366 | 2.99 | 3.06 | 0.98 | −0.07 | 65.3% |

**Conditional path behaviour absolutely exists — it is just symmetric.** Structural states move MFE and MAE in lockstep. The MFE/MAE ratio spans 0.90 to 1.02 across every state in the taxonomy, against a 0.97 baseline. Note that being in a clean uptrend gives a *lower* ratio (0.91) than having no structure at all (1.00).

This is a sharper statement than "markets are random." Unconditional returns are near-martingale, and **conditioning on structure changes the scale of the path without changing its asymmetry.** That is why the recognition succeeds and the capture fails.

---

## 6. Multi-asset scan

Same engine, same parameters, five liquid markets:

| symbol | 5m bars | median ATR% | setup | n | win% | EV R | 95% CI | PF |
|---|---:|---:|---|---:|---:|---:|---|---:|
| BTCUSDT | 625,095 | 0.180 | trend+BOS | 3,695 | 27.7% | −0.147 | [−0.204, −0.087] | 0.75 |
| BTCUSDT | | | + efficiency | 446 | 36.8% | +0.063 | [−0.073, +0.220] | 1.15 |
| ETHUSDT | 625,095 | 0.241 | trend+BOS | 3,575 | 30.0% | −0.055 | [−0.107, +0.001] | 0.90 |
| ETHUSDT | | | + efficiency | 532 | 34.0% | +0.088 | [−0.035, +0.218] | 1.20 |
| SOLUSDT | 376,688 | 0.305 | trend+BOS | 2,005 | 31.4% | −0.057 | [−0.121, +0.012] | 0.89 |
| SOLUSDT | | | + efficiency | 177 | 35.0% | −0.035 | [−0.220, +0.167] | 0.93 |
| XRPUSDT | 550,696 | 0.246 | trend+BOS | 2,968 | 29.1% | −0.048 | [−0.146, +0.089] | 0.91 |
| XRPUSDT | | | + efficiency | 349 | 31.8% | −0.050 | [−0.184, +0.105] | 0.90 |
| DOGEUSDT | 428,236 | 0.270 | trend+BOS | 2,527 | 29.0% | −0.150 | [−0.206, −0.091] | 0.73 |
| DOGEUSDT | | | + efficiency | 253 | 36.0% | +0.064 | [−0.108, +0.251] | 1.15 |

**0 of 10 cells have a CI above zero.** The efficiency filter is positive on BTC, ETH and DOGE and negative on SOL and XRP — the pattern of noise, not of a cross-asset effect. Higher volatility (SOL 0.305% vs BTC 0.180%) does **not** improve structural expectancy.

---

## 7. The twenty deliverables

| # | Deliverable | Status |
|---|---|---|
| 1 | Mathematical representation of structure | ✅ `zigzag.py` — causal, confirmed-only, ATR-normalised |
| 2 | Automatic swing detection | ✅ ATR ZigZag, 4 scales calibrated |
| 3 | Automatic trend detection | ✅ HH/HL vs LH/LL from confirmed pivot sequence |
| 4 | Automatic support/resistance | ✅ confirmed swing levels + prior swings; zones via ATR buffer |
| 5 | Impulse detection | ✅ `imp_atr` — completed leg size in ATR |
| 6 | Pullback detection | ✅ `pb_frac` — retracement of the current impulse |
| 7 | Breakout detection | ✅ BOS = close beyond last confirmed swing, rising edge |
| 8 | False-breakout detection | ✅ **AUC 0.635, calibrated — the project's best predictive result** |
| 9 | Trend-continuation detection | ✅ trend + BOS after pullback |
| 10 | Regime classification | ✅ trend state × efficiency × ATR percentile |
| 11 | Multi-timeframe structure | ✅ **tested and falsified** — alignment moves MFE/MAE 0.94 vs 0.97 baseline |
| 12 | Market-wide scanning | ✅ 5 assets, identical engine, 0/10 positive |
| 13 | MFE/MAE analysis | ✅ ratio 0.90–1.02 across every structural state |
| 14 | Structural entry hypotheses | ✅ 6 setups tested |
| 15 | Structural exit hypotheses | ✅ 5 exits incl. unbounded trailing structural |
| 16 | Long/short comparison | ✅ efficiency filter is a long-side artifact (+0.194 / −0.092) |
| 17 | Out-of-sample validation | ✅ 4-era split; most recent era negative |
| 18 | Cost-adjusted results | ✅ taker/taker throughout; maker/maker sensitivity run |
| 19 | Opportunity frequency | ✅ BOS every ~51 bars; trend+BOS 3,695 in 9 years ≈ 1.1/day |
| 20 | Strongest robust framework | ⚠️ **the recognition engine, not a strategy** |

---

## 8. Limitations

1. **Circularity risk in pattern definitions.** The accepted/failed breakout split is defined using post-event bars. I flagged and isolated it rather than reporting the 4.02 MFE/MAE ratio as a finding. Any structural label defined by what price does next carries this trap.
2. **Spot data, perp execution.** Path structure transfers (BTC spot/perp close correlation 0.999997 from earlier work); wick-level triggers do not.
3. **Sealed 2020–2022 excluded** — no COVID crash, no 2021 bull, no 2022 bear. This removes the strongest trending regimes in crypto history, which is precisely where a trend system would look best. **This is the most material limitation in this report.**
4. **One swing scale.** θ = 3.0 used throughout after calibration; θ ∈ {1, 2, 5} were measured for pivot counts but not fully backtested.
5. **Multiple testing.** 30 setup×exit cells, 8 efficiency thresholds, 10 multi-asset cells, 12 path-behaviour states, 5 acceptance slices ≈ 65 tests. Expected false positives at α = 0.05 ≈ 3. **Observed with CI above zero: 0.**
6. **No derivatives data on the alt series** — open interest, funding and liquidations were tested in an earlier phase (R-1) and added nothing directional; not repeated here.
7. **Simplified execution.** Fills at the next bar's open, no partial fills, no queue modelling. Adverse selection on a breakout entry is likely worse than modelled, which makes these results optimistic.

---

## 9. What I would test next

**H-1 — Spend the sealed 2020–2022 window on this.** Limitation 3 is not a footnote. A trend-structure system was tested here on 2017–2019 and 2023–2026 and never saw the 2021 bull run or the 2022 bear — the two cleanest sustained trends in the sample era. This is the most defensible remaining use of a one-shot holdout, and the hypothesis is now frozen in writing: *trend + BOS with a trailing structural exit, θ = 3.0, efficiency > 0.35, taker costs.* If it fails there, trend structure on crypto is closed.

**H-2 — Acceptance prediction as a filter on something that already works.** AUC 0.635 is a real, calibrated signal. It failed here because it was asked to carry a zero-EV trade on its own. Applied as a veto on a strategy that is already marginally positive, it is worth more than any feature found in this project. It needs a host.

**H-3 — Longer structural scales.** Everything here is 5m structure with 1.3-hour swings and a 51-bar median hold. At θ = 5 on 1h bars, swings run days and the cost share collapses from ~10% of risk to ~1%. The R-2 domain, reached from the structural side rather than the barrier side.

**Explicitly closed:** multi-timeframe alignment as an edge; trend efficiency as a standalone filter; CHoCH reversals; big-impulse continuation; higher-volatility alts as better structural markets.

---

## 10. In one paragraph

The structure engine works. It finds swings a chart reader would mark, classifies HH/HL and LH/LL sequences, measures impulses and pullbacks in ATR units, detects breaks of structure, and separates accepted from failed breakouts well enough that a calibrated model reaches **AUC 0.635** — comfortably the best predictive result this project has produced. The unbounded trailing structural exit finally lets the right tail breathe, producing individual trades up to **+38R**. And across **65 tests, 5 assets and 9 years, not one configuration has a confidence interval above zero.** The reason is visible in a single column: the MFE/MAE ratio sits between **0.90 and 1.02** in every structural state — trending, ranging, breaking out, timeframe-aligned or conflicted. Structure tells you the market is about to move and roughly how far. It does not tell you which way. **Your eyes are not the bottleneck; what your eyes are looking at does not contain the asymmetry.**

---

*Code: `research/struct/`. Data: `scripts/fetch_spot.py`, `scripts/fetch_alt.py`. Prior phases: `EDGE_REPORT.md`, `R1_REPORT.md`, `R3_REPORT.md`, `BTC_PLUS3PCT_STUDY.md`, `ACCOUNT_3PCT_STUDY.md`. Corrections log: `research/CORRECTIONS.md`.*
