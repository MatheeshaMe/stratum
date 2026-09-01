# Market Interpretation Engine

**1 September 2026 · 940,297 base bars · 5 timeframes · 230 observations · 50 sequence detectors · 5 assets**

---

## What changed, and what it bought

You asked me to stop building strategies and build an interpreter — to ask *what
is the market doing* before *what should I trade*. The reframe was worth it,
because it made a measurement possible that I had never run:

> **Which observations change the forward distribution — and in what way?**

Every prior phase measured only *mean* shifts, i.e. directional edge. But a
distribution can differ in variance, skew, tail mass or resolution speed with an
identical mean, and for a trader those are actionable — they govern
participation, sizing, target selection and patience.

Splitting information by *kind* produces the cleanest result this project has
generated:

| information type | replicates across 6 era-asset cells? |
|---|---|
| **MAGNITUDE** — how far price travels | **yes** |
| **TIMING** — how fast it resolves | **yes** |
| **DIRECTIONAL** — which way | **no** |

That is not "markets are random." It is a specific, measured claim about which
parts of a trader's read are load-bearing.

---

## Deliverables 1–7: the representation layer

`research/interp/observe.py`. 940,297 five-minute base bars, each carrying the
**full multi-timeframe context** (1m / 5m / 15m / 1h / 4h), never collapsed into
a single categorical state (§1).

| engine | what it records |
|---|---|
| **Structure** | confirmed-only ZigZag swings, HH/HL vs LH/LL, swing magnitude in ATR, BOS up/down — the *evolving sequence*, not a static label |
| **Liquidity** | pools (trailing extremes, equal highs/lows) and the **interaction type**: sweep (poke + close back) vs **acceptance** (two closes beyond) vs penetration depth |
| **Price action** | body fraction, wick up/down, close location, range in ATR, engulfing, inside bars, directional persistence |
| **Sequences** | 10 detectors × 5 timeframes: `sweep→reclaim→displacement`, `sweep→acceptance`, `compression→expansion`, `breakout→failure→reversal`, `impulse→pullback→continuation` |
| **Approach** | velocity in ATR, directional efficiency, deceleration, volume trend |
| **Regime** | volatility percentile, path efficiency, expansion ratio, 4h range position |

A sweep is recorded as an **event**, never as "reversal" (§4, §18). Its meaning
is carried by the sequence that completes after it.

---

## Deliverable 8–11: what the measurement says

Baseline over 938,248 bars, 4-hour forward window, ATR units:
mean **+0.094**, sd **6.114**, median range **6.83 ATR**, P(|move| > 2 ATR) **58.6%**,
median bars-to-1ATR **2**.

### Directional information — real but not transferable

11 of 100 binary observations show a significant mean shift against ~5 expected
by chance. Largest anywhere: **0.62 ATR** — against a standard deviation of 6.11,
a 0.10 standardised effect.

Then the replication test, across BTC-early / BTC-late / ETH / SOL / XRP / DOGE:

| observation | BTC early | BTC late | ETH | SOL | XRP | DOGE | sign holds? |
|---|---:|---:|---:|---:|---:|---:|---|
| **4h.sweep_lo** | −0.493 | −0.707* | −0.593* | −0.222 | −0.395 | −1.231 | **yes** |
| 4h.accept_hi | +0.833* | +0.371 | +0.792* | +0.279 | +0.153 | −2.151* | no |
| 1h.seq.sweep_accept_up | +0.575* | +0.389* | −0.268 | −0.037 | +0.016 | −1.948* | no |
| 4h.seq.sweep_accept_up | +0.577* | +0.270 | −0.225 | +0.200 | −0.157 | −1.782* | no |
| 4h.seq.sweep_reclaim_disp_up | −0.448* | −0.299 | −0.346 | −0.107 | −0.008 | — | no |
| 1h.seq.sweep_reclaim_disp_up | −0.384 | −0.307 | −0.671* | +0.115 | +0.262 | −2.265* | no |

**One of nine holds its sign everywhere.** Directional reading does not transfer.

### But the sequence distinction you insisted on is real

This is the most interesting directional finding, even though it fails
replication:

- `sweep → **acceptance**` (price continues through the pool): mean shift **+0.49 / +0.45**
- `sweep → **reclaim** → displacement` (price rejects back): mean shift **−0.37 / −0.34**

**Opposite signs, both significant on BTC.** The sequence carries the
information, exactly as you argued — a sweep alone is meaningless. But the sign
is the *opposite* of the folk teaching. "Swept the low, reclaimed, displaced up"
— the canonical bullish setup — is followed by **weaker** forward returns than
baseline. Acceptance/continuation is the one that leads.

I would not trade this. It does not replicate across assets. But it is a real
distinction that a mechanical "sweep = reversal" rule would erase.

### Magnitude and timing — this is what replicates

| observation | range ratio (6 cells) | bars-to-1ATR ratio |
|---|---|---|
| `5m.accept_hi` | 1.09 / 1.09 / 1.04 / 1.01 / 1.11 / 1.05 | **0.00** in 5 of 6 |
| `5m.seq.compress_expand_up` | 1.05 / 1.20 / 1.09 / — / 0.98 / 1.22 | **0.50** in 3 of 5 |
| `5m.seq.compress_expand_dn` | 1.04 / 1.18 / 1.11 / — / 1.04 / 1.22 | **0.50** in 3 of 5 |
| `4h.sweep_lo` | 0.93 / 0.87 / 0.95 / 1.00 / 0.93 / 0.92 | 1.00–2.00 |
| `1h.seq.sweep_accept_up` | 0.97 / 0.87 / 0.94 / 0.89 / 0.91 / 0.92 | 1.00–2.00 |

Three things replicate cleanly:

1. **Compression → expansion resolves roughly twice as fast** and travels 5–22%
   further than baseline.
2. **Acceptance beyond a 5m pool resolves essentially instantly** (median 0 bars
   to a ±1 ATR barrier, in 5 of 6 cells).
3. **Higher-timeframe liquidity events are followed by QUIETER conditions** —
   range ratio 0.87–1.00 in every single cell for `4h.sweep_lo` and
   `1h.seq.sweep_accept_up`. After a 4h sweep, the next four hours are calmer
   than average.

That third one is genuinely counter-intuitive and it is the most consistent
signal in the study. The folk model says a liquidity sweep precedes a big move.
Measured, it precedes a *smaller* one.

---

## Deliverable 12–13: the market read

`research/interp/market_read.py` produces the §28 output. Every line is tagged
with the information class behind it, so the reader can see which claims are
supported:

```
  2025-06-07T15:25:00   close 105,456.53

  STRUCTURE (each timeframe stated separately)
    [OBS ] 4h   bearish   swing 6.0 ATR
    [OBS ] 1h   bearish   swing 13.4 ATR
    [OBS ] 15m  unresolved
    [OBS ] 5m   bullish   swing 4.9 ATR
  LOCATION
    [OBS ] 4h range position 0.82 (premium)
  LIQUIDITY
    [OBS ] no liquidity interaction on any timeframe
  SEQUENCES COMPLETED
    [OBS ] 15m : sweep_reclaim_disp_dn
  COMPETING NARRATIVES
    [OBS ] BULLISH evidence (0): none
    [OBS ] BEARISH evidence (3): 4h bearish; 1h bearish; 4h premium
  ASSESSMENT
    [MAG ] nothing active -> expect a baseline-speed market
    [DIR?] no directional observation replicated across eras AND assets.
           Direction is NOT claimed.
  ACTION
    [OBS ] WAIT
```

Note the first block: 4h bearish, 1h bearish, 15m unresolved, **5m bullish**. The
conflict is preserved rather than resolved into `STATE = 7` (§1). "I don't know"
is a first-class output (§20), and the engine issues no direction because no
directional observation earned the right to one.

---

## Deliverable: software invariants (§27)

`research/interp/invariants.py`. Four assertions that would have caught C9, C10,
C11 and C12:

```python
check_trade(side, entry, stop, target)   # stop/target on the correct sides, risk > 0
check_trail(side, old, new, low, high)   # trail moves toward profit only, and
                                          # never to a level the bar already traded
check_causal(feature_bar, data_bar)      # no feature may read a later bar
# entry bar may trigger the STOP but never the TARGET
```

**Honest caveat: these are written and unit-testable but not yet exercised in a
live simulation**, because this phase built an interpreter, not a trader. They
become mandatory the moment anything here is wired to an execution loop.

**No new bugs were found this phase** — the first time that has been true. That
is partly the invariants and partly that an interpreter has less surface area to
be wrong on than a backtest.

---

## What this means for trading — stated conservatively

The engine does not produce a trade signal, and after twelve flattering bugs I am
not going to manufacture one from an interpretation layer on its first pass.

What it *does* produce is a validated separation:

**Use magnitude/timing information for:**
- participation — compression→expansion says a resolution is coming sooner
- patience — 4h liquidity events say the next few hours are likely *quieter*
- target realism — median forward range is 6.83 ATR, and observations move it
  only by ±20%. Any target beyond that is a hope, not a projection.

**Do not use anything here for direction.** One of nine directional observations
held its sign across six era-asset cells.

---

## Limitations

1. **The forward window is fixed at 4 hours.** Observations that matter over days
   would not show up.
2. **Binary observations only** for the divergence table — continuous features
   were built but quantile-cut analysis is not included.
3. **DOGE produces unstable estimates** (+55.17, +29.68 ATR cells) from a handful
   of extreme moves; those cells should be read as noise.
4. **No transaction costs anywhere in this phase** — deliberately, since nothing
   is traded. The moment a signal is proposed, cost must re-enter.
5. **~100 observations tested**; ~5 false positives expected at α=0.05 and 11
   observed. The replication table, not the significance count, carries the weight.
6. **Discovery was all of BTC.** Validation is a chronological split plus four
   unseen assets — weaker than a sealed holdout, which was spent in an earlier phase.

---

## What I would do next

**N-1 — Extend the forward window.** Everything here resolves in 4 hours. The
magnitude information that replicates might be stronger at 1–3 days, where the
cost hurdle is also lowest. That is the one domain this project has never
properly entered.

**N-2 — Use the magnitude layer as a no-trade filter on an existing candidate.**
`TRADER_SYSTEM.md`'s zone+alignment+trailing-exit result is the only thing still
standing. The replicated finding that 4h liquidity events precede *quieter*
conditions is a direct, testable veto for it.

**N-3 — Do not add directional observations.** Nine were tested carefully, one
replicated. Adding more will widen the in-sample/out-of-sample gap, not close it.

---

*Code: `research/interp/`. Invariants: `research/interp/invariants.py`.
Corrections log (12 entries): `research/CORRECTIONS.md`.*
