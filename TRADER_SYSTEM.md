# Reconstructing the Discretionary S&D Trader

**31 August 2026 · 5 assets · 1h decision TF · 2,668 qualified setups · 2017–2026**

---

## Verdict: **PROMISING BUT UNPROVEN — worth paper trading, not worth funding**

Your critique was correct and it changed the answer. The prior phase tested S&D
*mechanically* and found nothing. Testing it *contextually* found something —
but almost none of it came from the context hierarchy you'd expect.

**What survives:**

```
zone (base + impulse origin)
  + HTF regime alignment
  + limit at the proximal edge
  + trailing STRUCTURAL exit, no profit cap
```

n = 2,668 · win **25.6%** · median trade **−1.06 R** · **EV +0.314 R** (moderate funding)
95% CI **[+0.149, +0.494]** · max R 115.7 · longest losing streak **36**

And it beats the control that matters: an HTF-aligned **random** entry using the
identical trailing exit returns +0.041 R. **Differential +0.369 R, CI [+0.183, +0.569].**
The zone location is doing real work, not just riding the exit.

**What does not survive: the hierarchy itself.**

---

## Phase 7 — The ablation, which is the most important table here

If the trader model is right, context compounds. It does not.

| thesis | n | win% | EV R | 95% CI | ΔEV |
|---|---:|---:|---:|---|---:|
| **T0** zone alone | 716 | 31.4% | −0.133 | [−0.233, −0.030] | — |
| **T1** + HTF regime aligned | 419 | 35.1% | −0.023 | [−0.160, +0.113] | **+0.110** |
| **T2** + HTF location (discount/premium) | 129 | 25.6% | −0.318 | [−0.546, −0.101] | **−0.295** |
| **T3** + liquidity swept | 13 | — | too few | — | — |
| **T4** + decelerating approach | 0 | — | none | — | — |
| **T5** + zone broke structure | 0 | — | none | — | — |
| **R1** reversal at HTF extreme | 16 | — | too few | — | — |

*(fixed-2R management shown; the pattern is identical across all five exits)*

**Only the first rung pays.** HTF regime alignment adds +0.110 R. Every layer
after that either destroys expectancy (location, −0.295) or annihilates the
sample (liquidity: 716 → 13 setups; approach: → 0).

This is the central finding of the phase. The trader's reasoning chain —
regime → location → liquidity → structure → zone → approach — sounds like it
compounds. Measured, **it is one useful filter followed by four that cost sample
without buying information.** Six conditions ANDed together on 1h bars leaves
you with 13 trades in four years. That is not a strategy; it is a story with
enough clauses to always sound right afterwards.

---

## Phases 1–3 — What was built

**Phase 1 (trader model)** separated three kinds of claim: *observable in OHLCV*
(swing structure, displacement, penetration and recovery of prior extremes,
approach velocity/efficiency, volume vs its own history, range position);
*interpretation* ("institutions left unfilled orders"); and *unobservable in this
data* (book depth, iceberg orders, actual positioning). The previous phase failed
because it tested the **interpretation** — assuming impulse size proxies order
size. This phase tests only what is observable and treats the narration as
unproven.

**Phase 3 (feature engine)** — six levels, every feature causal, each answering a
trader question rather than being an available indicator:

| level | question | features |
|---|---|---|
| L1 regime | what kind of market | ATR percentile, path efficiency, expansion ratio |
| L2 location | where in the HTF picture | range position (premium/discount), distance to extremes in ATR |
| L3 structure | who is in control | confirmed ZigZag swings, HH/HL vs LH/LL, BOS |
| L4 liquidity | where is the fuel, what happened | prior extremes, sweep (penetrate + close back), clean break, equal highs/lows, penetration depth |
| L5 setup | where did displacement originate | base+impulse zone, FVG, width, freshness |
| L6 approach | how is price arriving | velocity in ATR, directional efficiency, deceleration, volume trend |

RSI and MFI were **excluded** — they add nothing not already in structure and
volume, and the brief was explicit about not overloading the system.

---

## Phase 5 — Entry models

| model | description | discovery EV | verdict |
|---|---|---:|---|
| **A** | blind limit at proximal edge | best with trailing exit | **kept** |
| B | rejection candle → market | +0.200 (trailS) | comparable, worse fills |
| C | sweep + reversal close → market | +1.123 on n=68 | sample too small to trust |
| D | local CHoCH → pullback limit | rarely triggers | dropped |
| E | momentum continuation → market | +0.205 (trailS) | comparable, pays taker |

**Confirmation reduces frequency without improving expectancy.** Model A — the
"naive" resting limit — wins because it is the only one that gets a maker fill
(1.5 bps vs 5.13 bps taker). At a median risk of 0.93% of price, that execution
difference alone is worth ~0.04 R per trade.

---

## Phase 6 — Management is where the edge actually lives

| management | EV R | note |
|---|---:|---|
| fixed 2R | −0.133 | negative |
| fixed 3R | +0.055 | flat |
| fixed 5R | +0.054 | flat |
| trail 2.5 ATR | −0.010 | flat |
| **trailing structural** | **+0.314** | **the entire result** |

Fixed targets truncate the distribution that pays for a 26% win rate. The
holding-time distribution shows why: **median hold 2 hours, p75 14 hours, p95
106 hours.** Most trades die immediately; the payoff comes from the small
fraction that run for days. Any fixed target caps exactly those.

**Tail dependence** (moderate funding):

| excluding | n | EV R | 95% CI |
|---|---:|---:|---|
| — | 2,668 | +0.314 | [+0.144, +0.492] |
| top 3 | 2,665 | +0.218 | [+0.086, +0.355] |
| top 10 | 2,658 | +0.141 | [+0.024, +0.258] |
| top 25 | 2,643 | +0.014 | [−0.084, +0.113] |

It survives removing the ten biggest winners out of 2,668 — better than I
expected — but dies at 25. **This is a genuine fat-tail strategy, and it needs
roughly the top 1% of its trades to work.**

---

## Phase 8 — Validation, including the part that failed

| test | result |
|---|---|
| Discovery 2017–2021 | +0.165 R (BTC, n=419) |
| Validation 2022–2024 | +0.992 R (BTC, n=315) |
| **Pre-registered held-out 2025–2026, BTC only** | **+0.360 R, CI [−0.159, +1.000] — FAILS** (n=160) |
| Pooled 2025–2026, all 5 assets | +0.290 R, CI [+0.079, +0.522] — passes |
| Cross-asset pooled (full period) | +0.368 R, CI [+0.192, +0.556] |
| ETH / SOL / XRP / DOGE | +0.401 / +0.317 / +0.436 / +0.281 — all positive |

**The pre-registered test failed.** I wrote the criteria before scoring: BTC
held-out with a CI excluding zero. At n = 160 the interval spans zero. The
pooled cross-asset version of the same period passes, but that was not the
pre-registered test and I am not going to retroactively promote it.

**Era stability is the other weakness:**

| era | n | EV R | 95% CI |
|---|---:|---:|---|
| 2017–2019 | 602 | +0.326 | [+0.042, +0.651] |
| **2020–2022** | 299 | **−0.075** | [−0.379, +0.261] |
| 2023–2024 | 958 | +0.447 | [+0.088, +0.846] |
| 2025–2026 | 809 | +0.290 | [+0.079, +0.522] |

Negative through the COVID crash, the 2021 bull and the 2022 bear — the three
regimes a trend-exit system should most enjoy.

---

## Costs, including the one I nearly missed

| funding assumption | median cost | EV after | 95% CI |
|---|---:|---:|---|
| typical 0.00125%/h | 0.003 R | +0.386 | [+0.217, +0.574] |
| **moderate 0.005%/h** | 0.011 R | **+0.314** | [+0.149, +0.494] |
| elevated 0.01%/h | 0.021 R | +0.218 | [+0.059, +0.390] |
| **stressed 0.03%/h** | 0.064 R | **−0.165** | [−0.300, −0.023] |

Fees are maker-in (1.5 bps) / taker-out (5.13 bps). **In a sustained
high-funding regime the strategy is negative** — and high funding correlates
with exactly the trending conditions that generate the signals.

---

## The bug that decided this phase

> **C10 — the target could trigger on the entry bar.** `manage()` checked both
> stop and target on bar `i`. A limit fills partway through that bar; OHLC gives
> no intrabar path, so whether price reached a 2R target before or after taking
> out the stop is unknowable. The standing rule is that same-bar ambiguity
> resolves against the trade.

It surfaced because **two phases of this project disagreed**: `ZONES_STUDY`
put 1h zones + alignment + fixed target at ≈ +0.005 R; this engine put the same
idea at +0.36 R held out. Diffing the two execution loops found it.

| cell | with C10 bug | corrected |
|---|---:|---:|
| T0/A/fix2 discovery | +0.165 | **−0.133** |
| T1/A/fix2 discovery | +0.271 | **−0.023** |
| T0/A/fix2 pooled alts | +0.173 | **−0.068** |
| held-out cells with CI above zero | 2 of 13 | **0 of 9** |

**Every fixed-target result in this phase was that bug.** Only the trailing exit
— which has no target and was therefore untouched — survived.

That is **ten errors found in my own research code across this project, and all
ten made results look better.** C9 and C10 were the same class of mistake in two
different engines, one phase apart.

---

## Phase 9 — The final specification

```
MARKET      BTC, ETH, SOL, XRP, DOGE perpetuals. Decision TF 1h.
            (5m is unusable: zone depth ~0.16% of price vs 6.6 bps cost = 41% of risk)

REGIME      HTF trend = close beyond the trailing 96-bar high/low, carried forward.
            NO TRADE unless the HTF trend agrees with the zone side.

ZONE        base : 1-3 bars, mean body/range < 0.5, total range <= 1.0 ATR
            impulse: 1-3 bars immediately after, net displacement >= 2.0 ATR,
                     every bar pushing the same way, mean body/range >= 0.55
            proximal = base edge price meets first; distal = far edge
            A zone is knowable only from the last bar of its impulse.

ENTRY       Resting limit at the proximal edge. First touch only.
            Zone expires after 480 bars or on a close 0.5 ATR beyond the distal edge.

STOP        distal edge -/+ 0.25 ATR. Live from the entry bar.
            Reject if risk < 0.10% or > 12% of price.

EXIT        Trailing structural stop: ratchet to each newly confirmed swing
            low/high -/+ 0.25 ATR. NO PROFIT TARGET. Max hold 120 bars.

SIZE        Fixed fractional on R. Given a 36-trade losing streak, cap risk at
            1-2% per trade. At 5% risk this strategy has a materially non-trivial
            chance of a 60%+ drawdown.

NO TRADE    HTF trend disagrees with the zone · zone already touched ·
            risk outside [0.10%, 12%] · price never reaches the proximal edge ·
            funding above ~0.02%/h · zone older than 480 bars
```

**What was deliberately left out**, because the ablation says it costs more than
it adds: HTF premium/discount location, liquidity sweeps, approach deceleration,
FVG, base tightness, volume confirmation, RSI, MFI, and all confirmation entries.

---

## Failure modes

1. **Sustained high funding** turns it negative (−0.165 R at 0.03%/h).
2. **A 36-trade losing streak** at 26% win rate. Most operators stop before the tail arrives.
3. **The 2020–2022 era was negative** — it is not regime-proof.
4. **It needs the top ~1%** of trades. Excluding the top 25 of 2,668, it is flat.
5. **Maker fills are assumed.** If the limit at the proximal edge does not fill in fast markets — precisely when the good trades happen — realised expectancy is lower than modelled.
6. **The pre-registered held-out test failed** at n = 160.

---

## What I would do next

**N-1 — Paper trade it, long enough to matter.** ~48 setups per asset-year across
5 assets ≈ 240 trades/year. One year of paper trading produces a sample
comparable to the entire held-out test, at zero risk, on data nobody has seen.
Given a 26% win rate, no shorter test can distinguish this from noise.

**N-2 — Add a funding filter and re-test.** The strategy is negative above
~0.02%/h. That is measurable in real time and is the single cheapest improvement
available.

**N-3 — Do not add more context.** The ablation is unambiguous: layers beyond
HTF alignment destroyed expectancy or the sample. The instinct to keep stacking
conditions is exactly what this table falsifies.

---

*Code: `research/trader/`. Pre-specification: `research/trader/PRESPEC.md`.
Trader model: `research/trader/PHASE1_TRADER_MODEL.md`. Pine Script:
`pine/stratum_sd.pine`. Corrections: `research/CORRECTIONS.md` §C10.*
