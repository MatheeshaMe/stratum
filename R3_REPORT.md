# Stratum R-3 — Intraday Path / Barrier Research

**28 August 2026 · ~1,190 hypotheses · 810-cell barrier surface · 376,000 entries**

---

## VERDICT: **No intraday path edge found**

The one candidate that survived the search was a four-minute look-ahead bug in
my own code. Corrected, it is negative by approximately its own transaction
cost, everywhere, in every regime, at every parameter setting.

The sealed 2020–2022 holdout **was not opened**, per instruction. Nothing
survived to justify it.

---

## 1. The framing that decides this phase

P0/T3 established that BTC 5m is a driftless random walk to within 0.8pp. For a
martingale the optional stopping theorem fixes first passage **exactly**:

```
P(target T before stop S) = S / (S + T)
EV = P·T − (1−P)·S = S·T/(S+T) − T·S/(S+T) = 0
```

Gross expectancy is **identically zero for every cell in the grid**. So the
barrier geometry is not where an edge can live. What the grid does determine is
the deviation a conditional state must produce:

```
EV = δ·(S + T) − cost        REQUIRED  δ > cost / (S + T)
```

Note this depends only on the **span** S+T, not the ratio. Required deviation
under maker/taker execution:

| stop / target | 0.10% | 0.20% | 0.50% | 1.00% | 1.50% |
|---|---:|---:|---:|---:|---:|
| 0.05% | 44.2pp | 26.5pp | 12.1pp | 6.3pp | 4.3pp |
| 0.20% | 22.1pp | 16.6pp | 9.5pp | 5.5pp | 3.9pp |
| 0.50% | 11.1pp | 9.5pp | 6.6pp | 4.4pp | 3.3pp |
| 1.00% | 6.0pp | 5.5pp | 4.4pp | 3.3pp | **2.7pp** |

Measured conditional lifts across this entire project are 1–4pp. **Only the
wide-span corner is even reachable**, which is where the search concentrated.

---

## 2. The unconditional surface confirms it precisely

810 cells (9 stops × 9 targets × 5 horizons × 2 sides), first passage resolved
on 1m bars, cost inside the search:

```
LONG   net EV per trade, maker/taker, 120m horizon
  stop\target   0.10%    0.20%    0.50%    1.00%    1.50%
  0.05%       -0.0647  -0.0623  -0.0601  -0.0598  -0.0598
  0.20%       -0.0693  -0.0674  -0.0648  -0.0643  -0.0642
  0.50%       -0.0705  -0.0689  -0.0654  -0.0644  -0.0641
  1.00%       -0.0704  -0.0689  -0.0647  -0.0637  -0.0634
```

Every cell sits at **−cost** (0.0663%). Best cell across both sides:
−0.0598%. There is no barrier geometry that helps, and none that hurts beyond
what you pay to trade it.

The raw deviation surface *does* show large numbers (up to +16pp at wide-stop /
narrow-target cells) — but that is the **vertical-barrier selection effect**:
with a short horizon a wide stop is rarely reached, so "resolved" cases
over-represent target hits. It is not an edge, and the net-EV table proves it.

---

## 3. The candidate, and how it died

Conditioning on 16 states across the reachable corner produced 10 hits against
~10 expected by chance — but the hits were not scattered. They clustered in one
family: **short-term momentum**, symmetric on both sides, across many barrier
choices. That coherence is what made it worth pursuing rather than dismissing.

It then survived, in order: realistic fill at `open[i+1]`, blended exit cost
derived from the realised outcome mix (C5), 4× spread stress, stop slippage to
+20bps, a look-ahead-free trailing threshold (C6), split-half replication, and a
concentration check (1,211 distinct days, top-5 days = 2.0%).

Then the sequential portfolio simulation returned a **3,153,883× equity multiple
and +6,430% CAGR**. Nothing real compounds like that. Working backwards from an
impossible number found the bug.

### C7 — four-minute look-ahead

`situations.agg()` returns `i1m` = the index of the **first** 1-minute bar of
each 5-minute bar. Every R-3 conditional experiment used `entry = i1m[k]` and
filled at `O[entry+1]`. But the signal comes from the **close** of 5m bar `k`,
which is 1-minute index `i1m[k+1]−1`.

**The fill was taken at the second minute of the very bar whose close produced
the signal — four minutes before the signal could exist.**

The damage scaled with the size of the signal bar. Because the candidate selects
the most extreme 30-minute moves, it was systematically buying four minutes into
the largest up-bars in the sample. That is exactly why EV appeared to rise
monotonically with tail depth: **the "selectivity effect" was the look-ahead
growing, not the edge.**

### Before and after

| | with C7 bug | corrected |
|---|---:|---:|
| 5% tail (28.5/day) | +0.0122% | **−0.0878%** |
| 1% tail (5.8/day) | +0.0924% | **−0.0738%** |
| 0.2% tail (1.3/day) | +0.1568% | **−0.0706%** |
| sequential system, 2.67× | 3,153,883× | **0.00× (−92.4% CAGR)** |

Every corrected CI is entirely below zero. Both halves negative. Every
volatility tercile negative. Every session negative. Every year negative
(2023 −0.095%, 2024 −0.086%, 2025 −0.085%).

**The parameter surface is the clearest evidence.** Before the fix it was a
strong monotone gradient (+0.088 → +0.240 toward shorter lookbacks and deeper
tails). After the fix it is **flat at ≈ −0.075% across every cell** — which is
the blended round-trip cost. Gross expectancy is zero, exactly as §1 predicts.

---

## 4. Answers to the phase questions

**Payoff surface** — searched completely; net EV = −cost in all 810 cells.

**Mean reversion vs momentum** — neither. Both directions net to −cost once the
look-ahead is removed.

**Long vs short** — analysed separately throughout. Symmetric, both negative.
No LONG-only or SHORT-only regime survives.

**Magnitude × direction** — high expected magnitude does not resolve direction
(established in R-1: micro *reduces* AUC in every magnitude band; here the
high-vol tercile is −0.054%).

**Entry timing** — tested close[i], open[i+1], close[i+1], close[i+2]. Once C7
is fixed, all are negative; the apparent decay with delay was the look-ahead
advantage being consumed.

**Opportunity frequency** — the target of 0–3/day is reachable (0.2% tail gives
1.3/day), but at −0.0706% per trade selectivity buys nothing. **Being selective
about a zero-EV process yields a zero-EV process.**

**The 2% objective** — a 0.75% target at ~2.7× leverage does return ~2% on
margin, and that leverage keeps the 0.5% stop far from liquidation. The geometry
is entirely feasible. **There is simply no state that makes the path favourable
enough to pay for itself.** Leverage was never the binding constraint.

**No-trade filter** — the correct output for every state tested.

---

## 5. Corrections made in R-3

Three bugs in my own code, all of which inflated results.

| ID | Bug | Impact |
|---|---|---|
| **C5** | Exit cost labelled "maker out" while only ~24% of exits (target hits) can rest passively; stop and horizon exits are takers | Understated round-trip by ~2.8 bps; the "realistic" scenario's +0.0130% was the label, not the arithmetic |
| **C6** | Tail thresholds computed with `nanquantile` over the **whole sample** — the decision to trade at *t* used the full-period return distribution | Systematically selected ex-post extreme moves; replaced with a trailing 30-day quantile |
| **C7** | **Four-minute look-ahead on every conditional entry** | Void every R-3 conditional result. Surfaced only because the portfolio simulation produced an impossible 3.15-million-× return |

Cumulative across the project: **7 bugs found in Stratum's own research code, every one of which had made results look better.** That asymmetry is not coincidence — it is what motivated reasoning looks like in code, and it is the reason each phase ends with a falsification pass rather than a backtest.

---

## 6. Accounting

```
R-3 barrier cells (unconditional)        810
R-3 state x cell combinations            210
R-3 momentum drill-down and stress      ~170
R-3 total                              ~1,190
significant after C6 + C7                   0

cumulative project total               ~1,650 hypotheses
cumulative tradeable                        0
```

---

## 7. Where this leaves the project

**R-3 is closed.** Intraday path/barrier structure on BTC perps at 1m–120m
horizons contains no exploitable asymmetry. Combined with R-0 (situations),
R-1 (microstructure), and the unconditional null, the intraday domain is
exhausted at the resolution this data supports.

**What remains open, unchanged:**

**R-2 — multi-day horizons.** The hurdle scales as `1/(S+T)`. At 5–8% spans the
required deviation falls to 0.4–0.8pp, the lowest bar this project has ever
faced, and nothing has been tested beyond 8 hours. It is also the only remaining
domain where the sealed holdout would be a fair test rather than a wasted one.

**The one genuine asset produced so far** is the research machine: a validated
null, an exact cost hurdle, leak-proof CV, block bootstraps sized to the
conditioning variable, a hypothesis registry, and — demonstrated seven times now
— the ability to detect and kill its own false positives before they reach a
trading account.

*The account is not the deadline. The edge is.*
