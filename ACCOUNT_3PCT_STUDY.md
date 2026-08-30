# BTC 3%-Per-Trade Account Opportunity Study

**30 August 2026 · 3,125,444 spot 1-minute bars · 2017-08 → 2026-07 · 205,014 simulated entries**

---

## The direct answer to your final question

> **Can BTC realistically provide repeatable, statistically identifiable opportunities to target ~+3% account growth per successful trade?**

**The movement: yes, abundantly. The edge: no.**

BTC produces the *price movement* required for a +3% account trade constantly — at 10× leverage you need only a 0.30% move, and that is touched within an hour **43.1%** of the time and within four hours **68.0%** of the time. Movement is not the constraint.

What is missing is the **path asymmetry**. Across 205,014 entries spanning nine years, the probability of reaching the target before an equal-sized adverse move converges to **~50%** at every leverage, in every volatility regime, in every UTC hour, on both sides. Against a 1:2 structure the market offers a **33.3%** win rate where **48.1%** is needed to break even after fees.

**The shortfall is 15.4 percentage points. The largest conditional edge measured anywhere in this project is 2–4 points, and none of it replicated out of sample.**

I found no way to manufacture the difference, and I am not going to pretend otherwise.

---

## 1. Leverage translation — and why leverage cannot help

### BTC move required for a given account return

| leverage | +1% acct | +2% acct | **+3% acct** | +5% acct |
|---|---:|---:|---:|---:|
| 1× | 1.000% | 2.000% | **3.000%** | 5.000% |
| 2× | 0.500% | 1.000% | **1.500%** | 2.500% |
| 5× | 0.200% | 0.400% | **0.600%** | 1.000% |
| 10× | 0.100% | 0.200% | **0.300%** | 0.500% |
| 20× | 0.050% | 0.100% | **0.150%** | 0.250% |
| 40× | 0.025% | 0.050% | **0.075%** | 0.125% |

### The invariance that governs everything

At leverage *L*, account P&L = `L × (price move − cost)`. **Leverage multiplies the gain, the loss, the cost and the variance by exactly the same factor.** It therefore cancels out of expectancy entirely. What it *does* change is the size of the move you need — and since cost is fixed in price terms, a smaller required move means cost consumes a larger share of it.

**Cost as a fraction of the +3% target** (maker-in / taker-out, 6.63 bps round trip):

| leverage | BTC move needed | cost / target |
|---|---:|---:|
| 1× | 3.000% | 2.2% |
| 2× | 1.500% | 4.4% |
| 5× | 0.600% | **11.1%** |
| 10× | 0.300% | **22.1%** |
| 20× | 0.150% | **44.2%** |
| 40× | 0.075% | **88.4%** |

At taker/taker execution (10.26 bps) the 20× row is **68.4%** and 40× is **136.8%** — at 40× the fee alone exceeds the entire target before the trade begins.

**Higher leverage does not make +3% easier. It makes it strictly harder.**

### Breakeven win rate by leverage and risk:reward

| leverage | BTC target | 1:1 | 1:1.5 | 1:2 | 1:3 |
|---|---:|---:|---:|---:|---:|
| 1× | 3.000% | 51.1% | 41.3% | 34.8% | 26.7% |
| 2× | 1.500% | 52.2% | 42.7% | 36.3% | 28.3% |
| 5× | 0.600% | 55.5% | 46.6% | 40.7% | 33.3% |
| **10×** | **0.300%** | **61.1%** | **53.3%** | **48.1%** | **41.6%** |
| 20× | 0.150% | 72.1% | 66.5% | 62.8% | 58.1% |
| 40× | 0.075% | 94.2% | 93.0% | 92.3% | 91.3% |

*Gross breakeven with zero cost would be 50.0% / 40.0% / 33.3% / 25.0%. The gap is what fees take.*

### Funding, on top

Hyperliquid funds hourly. At typical rates (0.00125%/h) a 4-hour hold costs 0.005% of notional — negligible. At elevated rates (0.01%/h) it is 0.04%, comparable to half the fee. At extreme rates (0.05%/h) a 12-hour hold costs 0.60% of notional, which at 10× is 6% of the account. **Funding is irrelevant for short holds and decisive for long ones in stressed regimes.**

---

## 2. Opportunity availability — the movement is there

205,014 entries every 15 minutes. `P(hit)` ignores the adverse path; `P(1st)` requires the target before an equal adverse move.

### LONG

| leverage | BTC target | 5m P(hit)/P(1st) | 30m | 1h | 4h | 24h |
|---|---:|---:|---:|---:|---:|---:|
| 1× | 3.000% | 0.0% / 0.0% | 0.4% / 0.4% | 0.9% / 0.9% | 4.7% / 4.5% | 24.4% / **22.5%** |
| 2× | 1.500% | 0.3% / 0.2% | 2.2% / 2.1% | 4.6% / 4.4% | 15.9% / 14.6% | 48.9% / **40.3%** |
| 5× | 0.600% | 2.4% / 2.3% | 12.4% / 11.4% | 20.7% / 18.5% | 45.4% / 36.6% | 76.9% / **49.3%** |
| 10× | 0.300% | 8.9% / 8.2% | 30.7% / 26.3% | 43.1% / 35.0% | 68.0% / 46.7% | 88.4% / **49.6%** |
| 20× | 0.150% | 23.7% / 20.5% | 54.2% / 41.0% | 65.8% / 45.7% | 83.1% / 48.9% | 94.2% / **49.2%** |
| 40× | 0.075% | 44.7% / 34.5% | 73.1% / 46.3% | 81.0% / 47.4% | 91.2% / 47.8% | 96.9% / **47.8%** |

SHORT is within ±1 point of LONG in every cell.

**Read the last column.** As the time limit grows, `P(1st)` converges to **49–50% and never crosses it**. The market will give you the move; it will not give you the move first more often than a coin flip.

### Net expectancy at a 1:1 structure, 4h limit, cost inside

| leverage | BTC target | P(win) | P(loss) | gross %acct | cost %acct | **NET %acct** |
|---|---:|---:|---:|---:|---:|---:|
| 1× | 3.000% | 4.5% | 5.2% | +0.008 | 0.066 | **−0.058** |
| 2× | 1.500% | 14.6% | 15.6% | +0.007 | 0.133 | **−0.125** |
| 5× | 0.600% | 36.6% | 37.3% | −0.008 | 0.332 | **−0.340** |
| 10× | 0.300% | 46.7% | 47.7% | −0.029 | 0.663 | **−0.692** |
| 20× | 0.150% | 48.9% | 50.6% | −0.051 | 1.326 | **−1.377** |
| 40× | 0.075% | 47.8% | 52.2% | −0.130 | 2.652 | **−2.782** |

Gross expectancy is ~zero at every leverage. Net expectancy is **−cost × leverage**. This is the invariance made visible.

---

## 3. Best timeframe

There is no timeframe that produces a favourable path. What the timeframe controls is **how much of your target the cost eats**:

| holding limit | typical BTC move available | cost share at 10× | verdict |
|---|---:|---:|---|
| 1m–5m | 0.05–0.15% | 44–133% | dead on arrival |
| 15m–30m | 0.15–0.30% | 22–44% | fee-dominated |
| 1h–4h | 0.30–0.60% | 11–22% | least bad |
| 4h–24h | 0.60–1.50% | 4–11% | best cost ratio, but funding and overnight gap risk appear |

**Best cost ratio: 4h–24h holds at 2–5× leverage.** That corresponds to targeting 0.6–1.5% BTC moves, where cost is 4–11% of the target rather than 44–88%. This does not make expectancy positive — it minimises the loss rate.

---

## 4. Volatility regimes — the most instructive table in the study

Trailing 30-day ATR percentile, causal. 10× leverage, 1:1, 4h limit.

| volatility bucket | n | P(hit target) | **P(target 1st)** | median MFE | median MAE | median min to target | net %acct |
|---|---:|---:|---:|---:|---:|---:|---:|
| bottom 10% | 25,291 | 55.6% | 48.4% | 0.316% | −0.306% | 48 | −0.688 |
| 10–25% | 31,000 | 62.9% | 48.7% | 0.406% | −0.403% | 34 | −0.694 |
| 25–50% | 49,111 | 67.5% | 48.5% | 0.478% | −0.493% | 27 | −0.700 |
| 50–75% | 47,936 | 71.6% | **48.4%** | 0.570% | −0.584% | 22 | −0.695 |
| 75–90% | 28,998 | 76.5% | **48.9%** | 0.709% | −0.700% | 13 | −0.709 |
| 90–95% | 10,063 | 79.7% | **49.2%** | 0.818% | −0.845% | 8 | −0.704 |
| 95–99% | 8,488 | 83.1% | **49.0%** | 0.993% | −1.007% | 5 | −0.720 |
| top 1% | 2,687 | 87.6% | 47.3% | 1.339% | −1.273% | 3 | −0.822 |

**Volatility changes everything except the thing that matters.** From the bottom decile to the top percentile:

- P(hit target) rises from 55.6% → **87.6%**
- Median time to target falls from 48 minutes → **3 minutes**
- Median MFE rises from 0.316% → **1.339%**
- **P(target before stop) stays at 47–49% throughout**

MFE and MAE grow together, almost exactly in step (0.316/−0.306 at the bottom, 1.339/−1.273 at the top). **There is no optimal volatility regime for edge. There is an optimal regime for speed, and it is the high-volatility one — but you arrive at a coin flip faster.**

---

## 5. Risk:reward structures — 10×, target 0.30% BTC

| r:r | target | stop | side | P(win) | martingale | gross %acct | cost | **NET %acct** | profit factor |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| 1:1 | 0.300% | 0.300% | LONG | 46.7% | 50.0% | −0.029 | 0.663 | **−0.692** | 0.980 |
| 1:1 | 0.300% | 0.300% | SHORT | 47.5% | 50.0% | +0.017 | 0.663 | **−0.646** | 1.012 |
| 1:1.5 | 0.300% | 0.200% | LONG | 38.4% | 40.0% | −0.007 | 0.663 | **−0.670** | 0.994 |
| 1:1.5 | 0.300% | 0.200% | SHORT | 39.0% | 40.0% | +0.025 | 0.663 | **−0.639** | 1.021 |
| 1:2 | 0.300% | 0.150% | LONG | 32.7% | 33.3% | +0.015 | 0.663 | **−0.648** | 1.015 |
| 1:2 | 0.300% | 0.150% | SHORT | 33.4% | 33.3% | +0.044 | 0.663 | **−0.620** | 1.045 |
| **1:3** | 0.300% | 0.100% | LONG | 25.7% | 25.0% | +0.048 | 0.663 | **−0.615** | 1.066 |
| **1:3** | 0.300% | 0.100% | SHORT | 26.1% | 25.0% | +0.063 | 0.663 | **−0.600** | 1.087 |

**Measured win rates track the martingale prediction `stop/(stop+target)` to within 1.5 points at every structure.** 1:3 is marginally the least bad (gross profit factor 1.07–1.09) because the wider target catches more of the fat right tail — but no structure comes close to covering the 0.663% cost.

**Do not assume 1:2 is optimal — it isn't, and neither is anything else.** The ranking among structures is a rounding error next to the cost.

---

## 6. Long vs short

Effectively identical. Across every leverage, volatility bucket, r:r structure and time limit, SHORT runs **0.5–1.0 percentage points better** than LONG on win rate and roughly 0.03–0.05% better on net EV per trade. That is consistent with a mild short-side skew in the sample period, not a tradeable asymmetry — it is far below the cost and it is not stable enough to lean on. **BTC does not offer better opportunities on one side.**

---

## 7. Entry conditions — your most important question, answered

Three-way chronological split, conditions fixed on TRAIN only:
**TRAIN** 2017-08→2018-12 · **VALIDATE** 2019 · **TEST** 2023-01→2026-07 · sealed 2020–2022 untouched.

94 condition × side combinations tested (ATR, RSI, MFI, relative volume, 1h/4h/24h returns, distance from 24h high and low, distance from the 200-hour EMA, 24-hour range, plus a priori combinations).

```
positive net EV in ALL THREE periods:  0 of 94
```

Every single cell is negative in every period, spanning **−0.27% to −0.95% per trade** at 10×. Best win rates seen anywhere: 41.3% (train) collapsing to 30.4% (test) for the same condition — the classic pattern.

**By UTC hour** (4h limit, 10×, 1:1): P(target first) ranges 44.4% (02h) to 49.2% (11h). Flat. No session edge.

---

## 8. Opportunity frequency

Target = 0.30% BTC (+3% account at 10×):

| limit | target touched | **reached before the stop** |
|---|---:|---:|
| 1 hour | 43.1% of entries | 35.0% |
| 4 hours | 68.0% | 46.7% |
| 24 hours | 88.4% | 49.6% |

At 15-minute decision intervals that is roughly **27 touches per day within an hour** and **43 per day within four hours**. You wanted "one high-quality opportunity every 1–2 days rather than 20 terrible signals." The honest finding is that **all of them are the same quality**: a ~47–50% coin flip. There is no subset that separates.

---

## 9. The $20 compounding simulation

At 10×, 1:2 (target 0.30% BTC, stop 0.15% BTC), maker-in/taker-out:

```
a WIN  returns  (0.30% - 0.0663%) x 10 = +2.337% of account
a LOSS returns  (0.15% + 0.0663%) x 10 = -2.163% of account

martingale P(win)  33.3%
measured   P(win)  32.7%
BREAKEVEN  P(win)  48.1%      shortfall: 15.4 percentage points
net EV per trade   -0.69% of account
```

### Trades required to reach each milestone

| from → to | multiple | p=33% | p=36% | p=40% | p=45% | p=50% |
|---|---:|---|---|---|---|---:|
| $20 → $25 | 1.2× | never | never | never | never | 362 |
| $25 → $50 | 2.0× | never | never | never | never | 1,124 |
| $50 → $100 | 2.0× | never | never | never | never | 1,124 |
| $100 → $500 | 5.0× | never | never | never | never | 2,609 |
| $500 → $1,000 | 2.0× | never | never | never | never | 1,124 |
| $1,000 → $10,000 | 10.0× | never | never | never | never | 3,733 |

*"never" = negative log-growth. The account decays no matter how long you trade. **The measured 32.7% sits in the "never" column.***

### Monte Carlo, 20,000 paths, $20 start

| scenario | trades | median | p5 | p95 | survived | median max DD |
|---|---:|---:|---:|---:|---:|---:|
| **measured (32.7%)** | 100 | **$9.90** | $6.91 | $13.57 | 100% | 53.1% |
| **measured (32.7%)** | 500 | **$1.98** | $1.96 | $2.00 | **0.3%** | 90.2% |
| +2pp optimism (34.7%) | 500 | $1.98 | $1.96 | $2.00 | 3.3% | 90.3% |
| breakeven (48.1%) | 500 | $17.37 | $7.73 | $40.81 | 100% | 45.7% |
| +3pp above breakeven | 500 | $34.09 | $15.17 | $76.59 | 100% | 32.7% |

Conservative / median / optimistic on the measured distribution are **$1.96 / $1.98 / $2.00** after 500 trades. There is no scenario branch to present — the distribution has collapsed.

### The inverse question: what edge would each goal require?

| goal | p(win) needed | **edge over martingale** |
|---|---:|---:|
| $20 → $100 in 6 months, 1 trade/day | 68.5% | **+35.2 pts** |
| $20 → $100 in 6 months, 3 trades/day | 55.3% | **+21.9 pts** |
| $20 → $1,000 in 1 year, 1 trade/day | 72.5% | **+39.1 pts** |
| $20 → $1,000 in 1 year, 3 trades/day | 56.6% | **+23.2 pts** |
| $20 → $10,000 in 2 years, 3 trades/day | 54.9% | **+21.6 pts** |

**The largest conditional edge measured anywhere in this project is 2–4 percentage points, and none of it replicated out of sample.** The requirement is 22–39 points. That is not a gap to be closed by better features; it is an order of magnitude.

---

## 10. Summary of the fourteen deliverables

| # | Deliverable | Finding |
|---|---|---|
| 1 | Best recurring patterns | **None.** 0 of 94 condition × side combinations positive across three periods |
| 2 | Long vs short | Effectively identical; SHORT better by 0.5–1.0 pts, far below cost, not stable |
| 3 | Best timeframe | 4h–24h holds at 2–5× — best cost-to-target ratio, still negative |
| 4 | Best volatility regime | None for edge. High vol is fastest (3 min vs 48 min to target) at the same ~48% odds |
| 5 | Best market conditions | None identified that survive out of sample |
| 6 | Opportunity frequency | 27/day within 1h, 43/day within 4h — all the same ~47% quality |
| 7 | Typical time-to-target | 48 min (low vol) → 3 min (top 1% vol) for a 0.30% move |
| 8 | Typical adverse movement | MAE tracks MFE almost exactly: −0.31% vs +0.32% (low vol), −1.27% vs +1.34% (top 1%) |
| 9 | Best risk:reward | 1:3 marginally (gross PF 1.07–1.09), all negative net |
| 10 | Best features | None. ATR is the strongest conditioner of *movement* and is direction-neutral |
| 11 | Out-of-sample results | 0 of 94 survive |
| 12 | Fee-adjusted expectancy | −0.058% (1×) to −2.78% (40×) per trade; ≈ −cost × leverage |
| 13 | $20 simulation | $20 → $1.98 median after 500 trades; 0.3% survival |
| 14 | Next hypotheses | Below |

---

## 11. Limitations

1. **Spot data, perp execution.** Analysis uses Binance BTCUSDT spot (longest history); trading would be on perps. Prior Stratum work measured HL-vs-Binance close correlation at 0.999997, so path structure transfers, but wick-level triggers do not.
2. **Sealed 2020–2022 excluded** — no COVID crash, no 2021 bull, no 2022 bear. Regime coverage is 2017–2019 plus 2023–2026.
3. **Entries every 15 minutes.** A finer grid would add overlapping, non-independent observations without adding information.
4. **Fills assumed at the bar close.** Prior work (R-3, correction C7) showed that indexing errors here can manufacture large phantom edges; this study indexes the 1-minute grid directly and walks paths from `i+1`, so the class of bug is structurally excluded.
5. **No liquidation modelling.** At 10× the maintenance buffer is roughly 8.75%; the 0.15% stop sits far inside it, so liquidation is not binding at these parameters. At 40× it would be.
6. **Multiple testing.** ~94 conditions × 2 sides, 8 volatility buckets, 8 r:r cells, 24 hourly cells ≈ 250 tests. Expected false positives at α = 0.05 ≈ 12. **Observed: 0.** Fewer than chance alone would produce.

---

## 12. What is actually worth testing next

Given the invariance in §1, the only lever that moves the answer is **cost relative to target**. Three hypotheses, ranked:

**H-1 — Larger targets, lower leverage.** Cost share falls from 22.1% (10×, 0.30%) to 2.2% (1×, 3.00%). A 1–2× system targeting 1.5–3.0% BTC moves over days needs only a **1.5–3 point** edge to break even rather than 15.4. This is the single highest-leverage change available and it is exactly the untested R-2 domain. **It also means abandoning "+3% per trade" as a frequent event** — at 2× you get roughly one 1.5% opportunity every day or two, not several per day.

**H-2 — Maker-only execution.** Halves round-trip cost from 6.63 to 3.00 bps, cutting the 10× breakeven from 48.1% to ~42%. Necessary but not sufficient: it closes about a third of the gap.

**H-3 — Earn the spread rather than pay it.** The measured structure — MFE and MAE growing in lockstep at a ~50% hit rate — is what a fairly-priced market looks like to a liquidity taker. The party with positive expectancy in that picture is the one providing liquidity. That is a market-making problem with different infrastructure requirements, and it is the only framing in which this data shows anyone making money.

**Explicitly closed by this study:** leverage as a route to +3% per trade; volatility-regime selection for directional edge; time-of-day selection; risk:reward optimisation; and all 94 tested entry conditions.

---

## 13. The one-paragraph answer

BTC gives you the movement. At 10× you need a 0.30% move and you get one within four hours 68% of the time. What it does not give you is the **order** — the target arrives before an equal-sized adverse move 47–50% of the time, in every volatility regime, at every leverage, in every hour, on both sides, in all three test periods. A 1:2 structure at 10× needs a **48.1%** win rate to break even after fees and the market supplies **32.7%**. Leverage cannot fix this because it multiplies cost and payoff identically while shrinking the move you need, which makes the fee a *larger* share of it — the 40× breakeven win rate is 92.3%. Starting from $20, the measured distribution compounds to **$1.98 after 500 trades with a 0.3% survival rate**. Reaching $1,000 in a year would require an edge of **+23 to +39 percentage points** over the martingale; the largest edge found anywhere in this entire project is **2–4 points**, none of it replicating out of sample.

*The opportunity you are looking for is real in the sense that the price movement exists. It is not real in the sense that anyone can systematically be on the right side of it for less than it costs to trade.*

---

*Code: `research/acct/`. Data: `scripts/fetch_spot.py`. Prior phases: `EDGE_REPORT.md`, `R1_REPORT.md`, `R3_REPORT.md`, `BTC_PLUS3PCT_STUDY.md`. Corrections log: `research/CORRECTIONS.md`.*
