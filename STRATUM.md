# STRATUM v2.0 — Executable Specification

**A cost-governed confluence engine for BTC-USDC perps on Hyperliquid**

| Field | Value |
|---|---|
| Project | Stratum |
| Owner | Praveen Matheesha |
| Version | 2.0 · 28 August 2026 · Status: **build-ready, edge unproven** |
| Instrument | **BTC-USDC perp on Hyperliquid L1 — single market, nothing else** |
| Language | Rust (core), Python (research harness), TOML (knobs) |
| Account | ~$15 USDC isolated → $1,000 stated target |
| Not this project | HFT, market making, queue racing, multi-asset, alpha discovery by ML |

> This is an engineering specification, not investment advice. Live trading can lose the entire account. The system is designed so that outcome is a **risk parameter**, not a surprise.

---

## 0. Read this first — the verdict from measurement

Before writing this document I implemented v1's core hypothesis and ran it against **44 months of real BTC 1-minute data (≈1.88 million bars, 2023-01-01 → 2026-08-28)** with a realistic Hyperliquid cost model and 1-minute intrabar resolution of every fill, stop, and target.

**Result: the strategy as specified in v1 loses money, and it loses significantly.**

| Configuration (1h decision TF, 2.0 ATR stop, 1.5R target) | Period | n | win% | net R/trade | cost R/trade | gross R/trade | t-stat |
|---|---|---:|---:|---:|---:|---:|---:|
| Unconditional level touch | 2025-01→2026-07 | 1006 | 41.3 | −0.033 | 0.063 | +0.030 | −0.85 |
| Unconditional level touch | **2023-01→2024-12 (OOS)** | 1257 | 37.5 | −0.126 | 0.061 | −0.065 | −3.73 |
| **v1 T1 exactly: reject wick + weak second push** | 2025-01→2026-07 | 436 | 36.0 | **−0.160** | 0.066 | −0.094 | **−2.79** |
| **v1 T1 exactly: reject wick + weak second push** | **2023-01→2024-12 (OOS)** | 519 | 35.1 | **−0.191** | 0.063 | −0.128 | **−3.68** |

Three findings, each replicated in both periods:

1. **Fading a clustered level on BTC has no gross edge.** Gross expectancy sits between −0.07R and +0.03R — indistinguishable from zero, before you pay anyone.
2. **The rejection wick — the operator's most-trusted visual cue — makes results significantly *worse*.** Baseline gross +0.030 → −0.048 (in-sample, t=−2.32); −0.065 → −0.128 (out-of-sample, t=−3.68). This is a stable, replicated, negative result. On BTC, a long wick into a level is *not* rejection; it is the start of continuation.
3. **Breakout continuation is no better.** Tested across 6 configurations on both periods: gross +0.01R to +0.16R, net mostly negative, and **no configuration keeps its sign across both periods.**

One configuration looked promising in-sample and then died out-of-sample, which is exactly the trap this document exists to prevent:

| wick + **climax** volume (not weak volume) | n | win% | net R | t | max DD |
|---|---:|---:|---:|---:|---:|
| 2025-01 → 2026-07 (in-sample) | 127 | 50.4 | **+0.186** | +1.68 | 7.6R |
| 2023-01 → 2024-12 (**out-of-sample**) | 210 | 43.8 | **+0.007** | +0.09 | 24.4R |

In-sample it earned +23.66R over 19 months with 14/19 profitable months. Out-of-sample it earned +1.53R over 24 months with 13/24 profitable months and a 24.4R drawdown. It was selection noise from testing ~25 configurations. **A v1-shaped build would have spent three weeks arriving here.**

### What this means for the project

The project is not dead. It is **re-pointed**. What the data actually establishes:

- **Cost is the governing term, and it is knowable in advance.** Round-trip cost is 3.0–10.2 bps depending on execution style. Whether that is 3% or 33% of your 1R is decided entirely by your stop width. This is the single most important design variable and v1 never mentions it.
- **v1's timeframe is arithmetically impossible on BTC.** BTC 5m ATR(14) has a median of **0.123% of price**. A 0.35–1.0 ATR stop is 0.04–0.12% wide. Round-trip taker cost of 10.2 bps against a 0.12% stop is **83% of 1R**. There is no win rate that survives that. v1's stop-width intuition (0.8–1.5%) was right; its 5m timeframe was calibrated to HYPE, where 5m ATR is much larger. On BTC that stop band lives on the **1h–4h** chart.
- **Gross edge in level geometry is consistently small-but-positive (+0.01 to +0.16R) and is eaten by cost.** The lever is therefore *cost*, not *more indicators*. Longer holds and maker entries are worth more than any filter tested.
- **Realistic trade frequency for anything selective is 0.2–1.5/day, not 2/day.** The "12 hours of market availability" cadence in v1 is wrong by an order of magnitude. This is a patience system.

So Stratum v2 keeps v1's engineering skeleton — which was sound — and replaces its *certainty* with a **falsification harness**. The strategy becomes a pluggable hypothesis that must clear a measured bar before a single live order is signed.

---

## 1. What changed from v1, and why

| # | v1 said | v2 says | Why |
|---|---|---|---|
| 1 | 8 Core tickers + 6 watch | **BTC only** | Operator decision. Also removes the cross-ticker robustness check, replaced by cross-venue + cross-period validation (§14). |
| 2 | 5m decision TF | **1h decision, 4h regime, 5m trigger, 1m resolution** | Measured: BTC 5m ATR = 0.123%; cost would be 8–33% of R. At 1h ATR = 0.646%, cost is 3–6% of R. |
| 3 | "Ingest 120 days of 1m via HL info API" | **Impossible.** HL serves a rolling ~5000 bars/interval | Verified: 1m→3.5 days, 5m→17 days, 15m→52 days, 1h→208 days. Older windows return `[]`. Deep history must come from Binance/Reservoir (§7). |
| 4 | 4.5 bps taker assumed everywhere | **Maker-first execution mandated**; full cost ladder in §3 | Maker 1.5 bps vs taker 4.5 bps. On a 1% stop that is 6.6 bps vs 10.2 bps round trip — a 35% cut in the dominant cost term. |
| 5 | T1 fade = the flagship template | **T1 as written is falsified.** Templates are now hypothesis slots | −0.191R OOS, t=−3.68 over 519 trades. |
| 6 | `min_score = 6`, additive confluence | **Marginal-lift gating** — every condition must earn its place | Measured: adding conditions monotonically *reduced* edge. Additive scoring hides which term is doing harm. |
| 7 | Poor-man's volume-profile heatmap | **Deferred.** Real liquidation prints available free (§7) | HL fills carry liquidation flags; Coinalyze gives free aggregated liquidations. No need to approximate. |
| 8 | Risk 10% of equity/trade | **5% cap, 2% preferred** | Monte Carlo: at 10% risk with a genuine 0.45/1.5R edge, P(ruin) = 38%. At 5%, P(ruin) = 5.5%. |
| 9 | No mention of rate limits on actions | **Order budget is a hard resource** (§11.4) | HL allows 1 request per 1 USDC of cumulative volume, +10,000 initial buffer. At $160/day volume you *earn* 160 requests/day. |
| 10 | "Search never writes strategy.toml" | Kept, plus **purged walk-forward + embargo + top-decile selection** | 400-bar level TTL leaks across naive WF boundaries. |
| 11 | Golden-file replay tests | Kept, plus **look-ahead assertions and a cross-venue wick-noise floor** | Measured: HL vs Binance 5m pivots agree only 70.6% of the time; p95 wick difference 8 bps. Any trigger tighter than that is fitting venue noise. |
| 12 | $15 → $1,000 as "stage 7" | **Explicit arithmetic and a probability** (§5) | Honest numbers beat aspiration. |

---

## 2. Scope

### 2.1 The instrument

Single market: **BTC perp, USDC-margined, on Hyperliquid L1.** Verified live 2026-08-28:

| Property | Value | Consequence |
|---|---|---|
| Mark price | ~$79,850 | — |
| `szDecimals` | 5 | Size increment 0.00001 BTC ≈ **$0.80** |
| Price tick | $1 (5 significant figures) | 1 tick = **1.25 bps** |
| Top-of-book spread | $1 typical | Half-spread cross = **0.63 bps** |
| Max leverage | 40× | Capped to 20× by policy (§12) |
| Min order notional | **$10** (exception: exact-close reduce-only) | Governs scale-out feasibility |
| 24h volume | $4.26B — deepest book on the venue | Slippage beyond top-of-book is negligible at our size |
| Median 5m bar volume | $4.4M, 811 trades | You are invisible. Market impact is not a concern. |

Trading one instrument is a real advantage: one book to model, one funding stream, one liquidation regime, one set of levels, and every hour of research compounds on the same object. The cost is that you lose the cross-ticker overfit brake. §14 replaces it.

### 2.2 Timeframes (revised — this is the central change)

| TF | Median ATR(14) | as % of price | Role |
|---|---:|---:|---|
| 1m | $51 | 0.065% | Fill resolution, execution only — **never a decision TF** |
| 5m | $87 | 0.123% | Entry trigger inside a 1h setup |
| 15m | $207 | 0.271% | Optional confirm |
| **1h** | **$501** | **0.646%** | **Primary decision TF** |
| 4h | ~$1,150 | ~1.44% | Regime / bias |

BTC daily range over the last 17 days: median 2.81%, p25 1.83%, p75 4.23%. A trade that captures a third of a typical day's range is ~0.9% — which is exactly one 1.5R move on a 0.6% stop. That is the natural scale of this instrument.

### 2.3 Non-goals

Unchanged from v1: no HFT, no ALO queue games, no validator, no genetic programming, no meme perps. Added: **no multi-asset**, and **no live order until §17's Gate 3 passes**.

---

## 3. The cost model — the governing constraint

Everything in this system is downstream of this table. Internalise it before writing a line of strategy code.

### 3.1 Cost ladder (Hyperliquid perps, verified 2026-08-28)

| Component | bps | Note |
|---|---:|---|
| Taker fee | 4.5 | Base tier (VIP 0) |
| Maker fee | 1.5 | Base tier |
| Half-spread cross | 0.63 | BTC $1 tick on $79,850 |
| Referral discount | −4% of fee | Permanent, first $25M volume. **Free money — set it up on day 1.** |
| HYPE staking discount | up to −40% of fee | Needs staked HYPE; irrelevant below ~$1,000 equity |
| Volume tier | — | Needs $M volume; irrelevant at this size |

### 3.2 What that costs you, as a fraction of 1R

**This is the table that decides the project.** Cost as % of 1R, by stop width and execution style:

| Execution style | RT bps | 0.6% stop | 0.8% | 1.0% | **1.2%** | 1.5% | 2.0% | 3.0% |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| taker in / taker out | 10.2 | 17.0% | 12.7% | 10.2% | **8.5%** | 6.8% | 5.1% | 3.4% |
| **maker in / taker out** | 6.6 | 11.0% | 8.2% | 6.6% | **5.5%** | 4.4% | 3.3% | 2.2% |
| maker in / maker out | 3.0 | 5.0% | 3.8% | 3.0% | **2.5%** | 2.0% | 1.5% | 1.0% |
| maker in / taker out + referral + 20% stake | 5.3 | 8.8% | 6.6% | 5.3% | **4.4%** | 3.5% | 2.6% | 1.8% |

And the win rate you need at a 1.5R payoff just to break even (gross breakeven is 40.0%):

| Execution style | 0.6% stop | 0.8% | 1.0% | 1.2% | 1.5% | 2.0% |
|---|---:|---:|---:|---:|---:|---:|
| taker / taker | 46.8% | 45.1% | 44.1% | 43.4% | 42.7% | 42.0% |
| maker / taker | 44.4% | 43.3% | 42.6% | 42.2% | 41.8% | 41.3% |
| maker / maker | 42.0% | 41.5% | 41.2% | 41.0% | 40.8% | 40.6% |

### 3.3 The three rules this forces

> **COST-1 — Stop floor.** No trade with a stop narrower than **0.60% of price**. Below that, cost exceeds 11% of R even with a maker entry, and no measured gross edge covers it. Encoded as `risk.min_stop_pct = 0.006`; the OMS rejects the signal, it does not widen the stop.

> **COST-2 — Maker entry is the default.** Every entry is a post-only limit resting at the level. A signal that requires crossing the spread is a signal you skip. Only the emergency flatten is market. Encoded as `exec.entry = "post_only"`, `exec.allow_taker_entry = false`.

> **COST-3 — Cost is charged inside R, always.** Every backtest, every report, every journal entry states net-of-cost R. A gross number never appears without its net beside it. The v1 habit of quoting "expectancy after fees" without showing the cost fraction is what let a −0.19R strategy look plausible.

### 3.4 Cross-venue noise floor

Measured over 4,673 overlapping 5m bars, HL vs Binance BTC:

- Close correlation **0.999997**; basis median +1.6 bps, sd 3.0 bps
- 5m swing-pivot agreement: **70.6%** — nearly one pivot in three differs
- p95 absolute wick difference: **8 bps**

> **COST-4 — Trigger noise floor.** No entry, stop, or level-touch tolerance may be tighter than **25 bps** (≈3× the p95 cross-venue wick difference). Anything tighter is fitting the wick noise of one venue's tape. Encoded as `levels.min_band_bps = 25`.

---

## 4. Account, sizing, and the honest arithmetic

### 4.1 Position sizing — solve from risk, never from leverage

```
notional = risk_dollars / stop_pct
size_btc = round_down(notional / price, 5 decimals)
margin   = notional / leverage
```

Worked example at $15 equity, 2% risk, 1.0% stop:

```
risk        = $0.30
notional    = 0.30 / 0.010 = $30.00
size        = 30 / 79850   = 0.00037 BTC
margin @10x = $3.00
liq distance @10x ≈ 8.75%   (stop is 11% of it — safe)
```

At 5% risk: notional $150, margin $15 at 10× — too much of the book. Use 20×: margin $7.50, liq distance ≈3.75%, stop is 27% of it. Acceptable but that is the ceiling.

> **SIZE-1** `stop_pct ≤ 0.40 × liquidation_distance_pct`. Assert at order construction; refuse the order otherwise.
> **SIZE-2** `notional ≥ $10`. If risk budget and stop width imply less, **skip the trade** — do not widen the stop and do not raise leverage.
> **SIZE-3** Partial scale-out requires *both* legs ≥ $10 notional. Below $20 notional, take the full exit at T1 instead of scaling. (Exact-close reduce-only is exempt from the $10 minimum; a partial is not.)
> **SIZE-4** Leverage is an *output*, never an input. It is whatever `notional / margin` happens to be, capped at 20×.

### 4.2 Risk table (revised down from v1)

| Equity | Risk/trade | Lev cap | Daily kill | Max trades/day |
|---|---|---|---|---|
| $15–30 | **2%** ($0.30) | 10× | −10% | 2 |
| $30–60 | 2.5% | 10× | −10% | 2 |
| $60–120 | 3% | 10× | −8% | 3 |
| $120–300 | 3% | 5× | −8% | 3 |
| $300–700 | 2.5% | 5× | −6% | 3 |
| $700–1000 | 2% | 3× | −5% | 3 |

v1 specified 10% risk per trade at $15. Monte Carlo over 20,000 paths, 2 trades/day, 180 trading days, with the daily kill and green-day stop enforced:

| Edge assumed (gross) | Risk/trade | P(reach $1,000) | **P(ruin < $5)** | Median end | Median max DD |
|---|---|---:|---:|---:|---:|
| 45% win @ 1.5R | 10% | 20.1% | **38.3%** | $42.64 | 79.7% |
| 45% win @ 1.5R | 5% | 1.8% | **5.5%** | $71.37 | 57.4% |
| 40% win @ 2.0R | 10% | 44.6% | **29.6%** | $371 | 78.3% |
| 40% win @ 2.0R | 5% | 16.0% | **3.3%** | $211 | 56.8% |
| 50% win @ 1.0R (no edge) | 10% | 0.2% | **82.6%** | $4.85 | 78.5% |

And the same 45%/1.5R edge, once cost is charged against a 1.2% stop:

| | P($1,000) | P(ruin) |
|---|---:|---:|
| gross (no cost) | 20.1% | 38.3% |
| **taker in/out (0.085R)** | **2.1%** | **77.9%** |
| **maker in/taker out (0.050R)** | **6.2%** | **63.0%** |

Read that last block twice. A genuinely profitable gross edge becomes a 78%-chance-of-ruin strategy purely through execution style. **Fees are not a rounding error on this account; they are the dominant term.**

### 4.3 The $15 → $1,000 path, stated honestly

66.7× requires ~4.2 doublings. The only configuration in 44 months of testing that showed positive in-sample expectancy produced **+1.25R/month at ~6.7 trades/month** — and it did not replicate out-of-sample. If a future hypothesis clears §17's gates at that rate:

- At 2% risk: ~2.5%/month → **~170 months**
- At 5% risk: ~6.3%/month → **~68 months**
- At 10% risk: ~12.5%/month → **~35 months**, with a 38% chance of ruin first

> **The target is not reachable on this edge at survivable risk.** It becomes reachable only if (a) a materially stronger edge is found, or (b) capital is added, or (c) the timeline is measured in years. State which one you are choosing. Do not solve the gap by raising leverage — the table above shows exactly where that road ends.
>
> This does not mean stop. It means: **build the machine that can find and prove an edge cheaply, and let the account follow the edge.** That machine is what the rest of this document specifies.

---

## 5. Free data stack — verified, production-grade, $0

Every endpoint below was called successfully on 2026-08-28. Status column reflects that test.

### 5.1 Primary — Hyperliquid (free, no key)

| Source | Endpoint | Gives | Limits | Status |
|---|---|---|---|---|
| Info REST | `POST https://api.hyperliquid.xyz/info` | `candleSnapshot`, `l2Book`, `meta`, `metaAndAssetCtxs`, `fundingHistory`, `predictedFundings` | 1200 weight/min/IP; candles +1 weight per 60 items | ✅ 200 |
| WebSocket | `wss://api.hyperliquid.xyz/ws` | `candle`, `trades`, `bbo`, `l2Book`, `activeAssetCtx`, `userFills`, `orderUpdates`, `userEvents` | 10 conns, 1000 subs, 2000 msg/min, 100 inflight posts | ✅ |
| Exchange | `POST /exchange` | Signed orders | **1 request per 1 USDC traded**, +10,000 initial buffer | — |

> ⚠️ **HARD LIMIT — candle retention.** `candleSnapshot` serves a **rolling ~5000-bar buffer per interval**. Verified: 1m → 3.5 days, 5m → 17 days, 15m → 52 days, 1h → 208 days, 4h → 5.5 years, 1d → since 2020-08. **A window older than the buffer returns `[]` regardless of `startTime`.** v1's Phase 0 ("ingest ≥120 days of 1m") cannot be done from this API. Two consequences: deep history comes from §5.2, and **you must start your own WS recorder on day 1** — HL 1m data you do not capture is permanently lost to you.

Pagination that actually works (bounded windows, not forward-seek):

```python
MS = {'1m':60_000,'5m':300_000,'15m':900_000,'1h':3_600_000}
def candles(coin, iv, start, end, page=4000):
    step = MS[iv]*page; out=[]; cur=start
    while cur < end:
        hi = min(cur+step, end)
        c = info({"type":"candleSnapshot",
                  "req":{"coin":coin,"interval":iv,"startTime":cur,"endTime":hi}})
        out += [x for x in c if not out or x['t'] > out[-1]['t']]
        cur = hi+1; time.sleep(0.55)          # stay under 1200 weight/min
    return out
```

### 5.2 Deep history — Binance Data Vision (free, no key, no account)

`https://data.binance.vision/data/futures/um/{monthly|daily}/klines/BTCUSDT/1m/BTCUSDT-1m-{YYYY-MM|YYYY-MM-DD}.zip`

- ✅ Verified: 43 monthly files (2023-01 → 2026-07) = **1,883,520 1m bars downloaded in ~90 seconds**. Current month via daily files.
- Every zip has a `.CHECKSUM` sibling — verify it.
- Also free at the same root: `aggTrades`, `trades`, `bookTicker`, `bookDepth`, `markPriceKlines`, `premiumIndexKlines`, and **`metrics`** (5m open interest + top-trader long/short ratio + taker buy/sell volume ratio — a genuinely useful free substitute for CoinGlass positioning data). ✅ verified schema:
  `create_time, symbol, sum_open_interest, sum_open_interest_value, count_toptrader_long_short_ratio, sum_toptrader_long_short_ratio, count_long_short_ratio, sum_taker_long_short_vol_ratio`
- ⚠️ `liquidationSnapshot` is **discontinued** for USD-M futures (404, empty prefix). Do not plan around it.

**Validity as a proxy for HL BTC** — measured, not assumed:

| Metric | Value | Use it for | Do **not** use it for |
|---|---|---|---|
| Close correlation | 0.999997 | Structural params: cluster width, swing L/R, stop/target multiples, regime filters, expectancy geometry | — |
| Basis (HL−Binance) | median +1.6 bps, sd 3.0 | — | Absolute price triggers |
| 5m pivot agreement | **70.6%** | — | **Wick-trigger thresholds, touch tolerance** |
| p95 wick difference | **8 bps** | — | Any tolerance tighter than 25 bps (COST-4) |

### 5.3 Hyperliquid-native deep archives (S3, requester-pays)

| Bucket | Contents | Cost |
|---|---|---|
| `s3://hydromancer-reservoir/requester-pays` (**Reservoir**) | All fills incl. **liquidations, ADLs, TWAP, builder fills**; **1s OHLCV** (backfilled pre-Aug-2025); daily account snapshots; 20-level L2 @1min. Parquet, updated daily. | No subscription; you pay AWS egress. Free from an EC2 box in the same region. |
| `s3://hyperliquid-archive` (official) | L2 book snapshots (`market_data/`), asset contexts (`asset_ctxs/`). LZ4. | Requester-pays. "No guarantee of timely updates; data may be missing." |
| `s3://hl-mainnet-node-data` (official) | Node fills, blocks, L1 transactions, non-trade events | Requester-pays. Fills alone ≈0.8–1.0 GiB/day all-coin. |

Reservoir is the right answer for HL liquidation prints and tick data. Pull **BTC only** and the egress is trivial.

### 5.4 Supporting free sources

| Source | Gives | Access | Status |
|---|---|---|---|
| **Coinalyze** `api.coinalyze.net/v1` | Aggregated cross-exchange OI, funding, **liquidations**, long/short ratio, CVD | Free key, **40 req/min** | ✅ 200 |
| **Binance futures data** `fapi.binance.com/futures/data/openInterestHist` | 5m OI history | Free, no key | ✅ 200 |
| **Binance WS** `!forceOrder@arr` | Live liquidation prints | Free | — |
| **ForexFactory** `nfs.faireconomy.media/ff_calendar_thisweek.json` | FOMC / CPI / NFP with impact ratings | Free, no key | ✅ 200, 9.8 KB |
| **DefiLlama** `api.llama.fi` | TVL, prices, protocol data | Free, no key | ✅ 200 |
| DefiLlama unlocks | Token unlock calendar | **Pro only ($300/mo)**; web calendar free | — |
| **CoinGlass** | Liquidation heatmap | **No free tier** — $29/mo minimum | Not required |

> **Event calendar for BTC-only is trivial.** BTC has no token unlocks. The only events that matter are macro (FOMC, CPI, NFP) and they come free from ForexFactory. Poll weekly, cache to `data/calendar.json`, flatten inside the window. This replaces v1's whole unlock-calendar apparatus.

### 5.5 Total infrastructure cost

| Item | Cost |
|---|---|
| All market data (research + live) | **$0** |
| Macro calendar | **$0** |
| VPS (Hetzner CX22 / DO basic, 2 vCPU 4GB) | ~$5–8/mo |
| S3 egress for Reservoir BTC pulls | <$2 one-off |
| **Total** | **~$6–10/month** |

---

## 6. Data layer

### 6.1 Canonical bar

```rust
pub struct Bar {
    pub ts: i64,        // ms, bar OPEN time, UTC
    pub tf: Tf,
    pub o: f64, pub h: f64, pub l: f64, pub c: f64,
    pub v: f64,         // base volume
    pub n: u32,         // trade count — free in HL payload, v1 never used it
    pub closed: bool,   // NEVER compute features on closed == false
}
```

`n` is in every HL candle and every Binance kline. `v/n` = average trade size, a real tape-character feature that costs nothing. A push with rising trade count but *falling* average size is retail chasing; the reverse is size stepping in. v1 discarded this field.

### 6.2 The three bugs that make live diverge from backtest

> **DATA-1 — Never compute on an unclosed bar.** The HL WS `candle` channel streams the *forming* bar on every update. Gate every feature on `bar.closed`, set when `now_ms >= bar.T` or when the next bar's first message arrives. This is the single most common live/backtest divergence.
>
> **DATA-2 — Aggregate deterministically, forward-fill only the index.** 1m → 5m/1h: `o` = first, `h` = max, `l` = min, `c` = last, `v` = sum, `n` = sum. A missing 1m bar creates a time-index gap, never a synthetic volume-0 bar that feeds `vol_sma`.
>
> **DATA-3 — Bit-stable replay.** The same parquet + the same TOML must produce byte-identical signal output on any machine. Pin the float ops, no `HashMap` iteration order in scoring, no wall-clock in pure functions.

### 6.3 Store

```
data/
  bars/venue=hl/coin=BTC/tf=1m/date=YYYY-MM-DD/part.parquet
  bars/venue=binance/coin=BTCUSDT/tf=1m/...
  ctx/venue=hl/coin=BTC/date=.../ctx.parquet      # funding, OI, mark, oracle, premium
  liq/venue=agg/coin=BTC/...                       # Coinalyze + Reservoir liquidation prints
  calendar.json
  signals.sqlite                                   # signals, fills, journal
```

Parquet for bulk bars (columnar, bit-stable, compresses ~10×). SQLite for signals/fills/journal (transactional, queryable, one file to back up).

### 6.4 Live recorder — start this on day 1

Because HL's candle buffer is a rolling 5000 bars, **every hour you do not record is gone forever.** The recorder is the first thing that ships and the last thing you turn off.

```
stratum-record --coin BTC \
  --subs candle:1m,trades,bbo,l2Book,activeAssetCtx \
  --out data/bars/venue=hl/coin=BTC
```

Requirements: reconnect with exponential backoff; on reconnect, backfill the gap from `candleSnapshot`; write append-only; log every gap to `data/gaps.log`; heartbeat to disk every 60s so a supervisor can detect a wedged socket.

---

## 7. Features

All features are pure functions of stored bars plus context. If it cannot be computed from what is on disk, it does not exist.

### 7.1 Carried from v1 (unchanged, they were correct)

Wilder **ATR(14)** on the decision TF — every distance knob is in ATR units. **EMA** 20/50 with `ema_fast_slope`, `dist_ema_atr`, `stack_up`/`stack_down` — a filter, never an entry. Wilder **RSI(14)** and **Stoch RSI** with `%K`/`%D` smoothing; divergence computed **only on confirmed swing points**. **Volume**: `vol_sma(20)`, `vol_z`, `vol_ratio` (current push vs prior push).

### 7.2 Added in v2 — free, and each one is a real signal

| Feature | Definition | Source | Why |
|---|---|---|---|
| `avg_trade_size` | `v / n` | HL candle payload | Distinguishes size from retail chasing. Free, unused in v1. |
| `oi_delta` | Δ open interest over k bars | `activeAssetCtx` WS / `metaAndAssetCtxs` | Price up + OI up = new longs (fuel for a squeeze). Price up + OI down = short covering (exhaustion). This is the best free upgrade to any level signal. |
| `funding_z` | z-score of hourly funding over 7d | `fundingHistory` | Extreme funding = crowded positioning. HL funds **hourly**, so a 4h hold pays ~4 ticks — negligible; but the *level* is a crowding read. |
| `basis_bps` | HL mark − Binance mark | both, live | Divergence >8 bps signals venue-local flow. |
| `xvenue_funding_spread` | HL 1h-annualised − Binance/Bybit 8h-annualised | `predictedFundings` | Free cross-venue positioning divergence. |
| `liq_cluster` | Liquidation notional binned by price, 12h rolling | Coinalyze / Reservoir fills | **Real** liquidation prints. Replaces v1's guessed volume-profile heatmap. |
| `toptrader_ls_ratio` | Top-trader long/short ratio | Binance `metrics` (free, historical) | Free positioning series with matching history depth. |

> **FEAT-1 — Every feature must justify itself by marginal lift (§14.3), not by being in the confluence list.** The measured lesson: adding the rejection wick to the baseline *cost* 0.08R. Conditions are not free.

### 7.3 Deferred

Volume-profile "poor-man's heatmap" (§7.7 in v1). Real liquidation prints are free; approximating them from typical-price bins is strictly worse. Revisit only if `liq_cluster` proves useful and needs higher resolution.

---

## 8. Levels engine

This module remains the product. Everything else modifies it.

### 8.1 Swings

Bar `i` is a swing high if `high[i] == max(high[i-L .. i+R])`. **The pivot is only knowable at bar `i+R`.** Defaults on 1h: `L = R = 3`.

> **LEVEL-1 — As-of semantics are mandatory.** The level store exposes `levels.as_of(ts)` and may only return levels confirmed at or before `ts`. A unit test must assert that `as_of(t)` is identical whether computed forward-only or from a full-history rebuild. This is where look-ahead bias enters, and it is invisible in results until live trading finds it for you.

### 8.2 Clustering

Sort swings by price; greedily merge into a cluster when `|price − cluster_mean| ≤ cluster_atr × ATR`. Default `cluster_atr = 0.25`.

Each cluster carries: `price` (volume-weighted mean), `lo`/`hi` band, `touches`, `last_touch_ts`, `strength`, `polarity` (held-from-below = support, from-above = resistance).

Expire when untouched for `level_ttl_bars` (default 300 on 1h ≈ 12.5 days) **and** `strength < min_strength`.

> **LEVEL-2 — Band floor.** `max(cluster_atr × ATR, 25 bps × price)`. Per COST-4, a band tighter than 25 bps is fitting one venue's wick noise (measured p95 cross-venue wick difference: 8 bps; 3× that is the floor).

### 8.3 Events

| Event | Definition |
|---|---|
| At level | `\|close − level.price\| ≤ touch_atr × ATR`, or a wick traded through the band |
| Reject | Wick beyond the band, decision-TF close back inside |
| Break | Decision-TF close beyond the band by `break_atr × ATR` |
| Failed reclaim | Break, then within `reclaim_bars` a return that cannot close back through |
| Accept | Two consecutive decision-TF closes beyond the band |

### 8.4 Eye-match gate (Gate 1)

Before any template is written, overlay computed clusters on the operator's own charts for 10 sampled sessions. The operator must say *"these lines are what I was looking at."* If not, fix clustering and stop — **do not proceed to templates.** This gate is inherited unchanged from v1 and it was the best idea in that document.

---

## 9. Strategy — hypothesis slots, not fixed templates

### 9.1 What the measurements permit

v1's T1 (reject wick + weak second push) is **falsified**: −0.191R OOS, t=−3.68, n=519. It is not in v2 and must not be built.

A template is now a **hypothesis** with a mandatory pre-registered kill criterion. The engine ships with the harness; the strategy is what survives it.

### 9.2 Template interface

```rust
/// MUST be pure: no I/O, no clock, no global state.
/// This purity is what makes search cheap and tests possible.
pub fn signal(f: &Features, lv: &Levels, p: &Params) -> Option<Signal>;

pub struct Signal {
    pub template: &'static str,
    pub side: Side,
    pub entry: f64,       // post-only limit price
    pub stop: f64,
    pub targets: Vec<(f64, f64)>,   // (price, fraction)
    pub reason: String,   // human-readable, mandatory
    pub ts: i64,
}
```

Every signal carries a reason string:

```
H1 SHORT BTC 79,850 stop=80,650 (1.00%) t1=78,650 R=1.5
  lvl=79,845 touches=3 age=41h  oi_delta=+2.1σ  funding_z=+1.8
  cost=0.066R  net_exp_hint=+0.09R
```

> **STRAT-1** If the operator cannot read the reason string and recognise the trade, the template is not ready.
> **STRAT-2** The reason string **must** include `cost=` as a fraction of R. Cost is never invisible.

### 9.3 Candidate hypotheses (ranked by what the data suggests)

These are starting points, each to be run through §17 Gate 2 and killed without ceremony if it fails.

**H1 — Climax exhaustion at a level.** Wick into a cluster *with* volume `> 2.0 × vol_sma`. Note this is the **opposite** of v1's weak-second-push hypothesis, and it is the only variant that showed in-sample promise (+0.186R, 127 trades, 14/19 profitable months) — but it did **not** replicate OOS (+0.007R, t=+0.09). Status: **not proven**. Retest with `oi_delta` and `liq_cluster` conditioning, which the original test lacked.

**H2 — Long-hold breakout, cost-minimised.** 4h decision, ≥2% stop, 2R target. Cost falls to ~3% of R. OOS showed +0.118R net (t=+1.28) but IS was −0.023R — sign did not hold. Status: **not proven**, but the *cost geometry* is right and it deserves a proper test with maker entries.

**H3 — Liquidation-cluster reversion.** Price sweeps into a `liq_cluster` peak, liquidation prints spike, price closes back. Untested — the data (Reservoir / Coinalyze) was not in v1's scope. This is the most genuinely new hypothesis available and the cheapest to test now that the harness exists.

**H4 — Funding/OI-conditioned regime gate.** Not a standalone entry: a *filter* applied to H1/H2. Test as marginal lift only (§14.3).

> **STRAT-3 — No fourth template until one template has 100 accepted paper trades.** Carried from v1, and v1 was right.

### 9.4 Scoring — marginal lift, not additive points

v1 assigned points and set `min_score = 6`. The measurements show why that fails: adding conditions **reduced** expectancy, and an additive score cannot tell you which term is doing the damage.

v2 replaces it:

```
For each candidate condition c:
    lift(c) = E[net R | base ∧ c] − E[net R | base]
Keep c only if:
    lift(c) > 0  AND  n(base ∧ c) ≥ 150  AND  lift holds sign in BOTH periods
```

The engine reports a lift table per condition, per period, every sweep. A condition that does not clear the bar is **removed from the template**, not down-weighted.

---

## 10. Execution and OMS

### 10.1 Order lifecycle

```
SIGNAL → post-only limit at level (cloid = uuid)
       → [filled]  → place reduce-only stop (trigger) immediately, same tick
                   → place reduce-only TP ladder
                   → on T1 fill: move stop to breakeven + 1 tick
       → [unfilled after entry_ttl_bars] → cancel, mark MISSED, journal it
       → [invalidated before fill]       → cancel
```

> **OMS-1** Stop goes on **in the same event-loop tick as the entry fill**. A position without a resting stop is a bug, and a supervisor thread asserts this every second.
> **OMS-2** One position at a time. No hedging. **No averaging losers, ever** — enforced in code, not in discipline.
> **OMS-3** Every order carries a `cloid`. Duplicate `cloid` must not double the position — test it (§16).
> **OMS-4** On restart, reconcile from `clearinghouseState` + `openOrders`, never from local state. On-chain is truth.

### 10.2 Post-only entries

Hyperliquid ALO (add-liquidity-only) orders reject rather than cross. Handle the reject as **"the market moved to me; the setup may be invalid"**, not as "retry one tick worse". Chasing converts a 1.5 bps entry into a 5.1 bps entry and burns rate-limit budget (§10.4).

```
max_entry_reprices = 1     # then abandon the signal
reprice_only_if    = level still valid AND score unchanged
```

### 10.3 Disconnect policy

Heartbeat on the WS. If stale > 8s:
- Working entry orders → **cancel**
- Open position → keep the exchange-side reduce-only stop (it lives on HL, not in your process) and alert
- If stale > 60s → flatten via REST market order

The reduce-only stop resting on the exchange is what makes a $6/month VPS acceptable. Your process dying must not be able to lose the account.

### 10.4 Rate-limit budget — a hard resource v1 never mentioned

Hyperliquid's address-based limit: **1 request per 1 USDC of cumulative volume traded**, plus a **10,000-request initial buffer**. Rate-limited state = 1 request per 10 seconds.

At $30 notional × 2 trades/day = $60/day of volume, you **earn 60 requests/day**. Each trade consumes: 1 place entry + 1 place stop + 1 place TP + up to 2 cancels + 1 modify ≈ **6 requests**. Two trades = 12 requests/day against 60 earned. Comfortable — *until* a repricing loop runs.

> **OMS-5** Track `requests_used` and `requests_earned` in the OMS. Refuse any non-flatten action below a 500-request reserve. Log the ratio daily. A repricing loop that burns the buffer leaves you unable to *exit* — which is how a rate limit turns into a liquidation.
>
> Batched requests count as **one** for IP limits but as **individual** requests for the address limit. Batching does not save address budget.

### 10.5 Signing and key security

- **Never put the master key on the VPS.** Use an **API/agent wallet** (`approveAgent`), which can trade but cannot withdraw.
- One agent wallet per process. Nonces are stored per signer — sharing a wallet across processes corrupts nonce state.
- HL keeps the **100 highest nonces** per signer; use a monotonic atomic counter seeded to `unix_ms`.
- Set an **expiry** on the agent wallet. Rotate it monthly.
- Never reuse a deregistered agent address — nonce state is pruned and prior signed actions become replayable.
- L1 actions sign over **chain id 1337**. A "valid signature, rejected order" is almost always chain-id or nonce, not the key.
- Run **NTP**. Nonces are millisecond timestamps; clock drift silently rejects orders.
- Secrets from environment or file with `0600`, never in git. Add a pre-commit hook that greps for `0x[a-fA-F0-9]{64}`.

### 10.6 ARM mode

Live orders are placed only after the operator sends `ARM <TEMPLATE>`. ARM expires after `arm_ttl_minutes` (default 120) or one fill, whichever is first. `auto_live` stays `false` until a template has 100 live-or-paper fills.

---

## 11. Risk engine

Enforced in code at the OMS boundary. Every check reads equity from `clearinghouseState` — **on-chain truth, never local PnL accounting**.

| Check | Rule | Action on breach |
|---|---|---|
| Per-trade risk | ≤ table (§4.2) | Reject signal |
| Stop floor | ≥ 0.60% of price (COST-1) | Reject signal |
| Liquidation buffer | `stop_pct ≤ 0.40 × liq_distance` | Reject signal |
| Min notional | ≥ $10 | Reject signal |
| Leverage cap | ≤ table | Reject signal |
| Trades/day | ≤ table | Block new entries |
| Daily kill | equity ≤ day_open × (1 − kill%) | **Flatten, block until UTC midnight** |
| Green-day stop | equity ≥ day_open × 1.25 | Flatten, no new risk today |
| Consecutive losses | 4 in a row | Block 24h, force journal review |
| Weekly drawdown | −25% from week open | Block until operator re-arms manually |
| Event window | inside `event_window_hours` of a high-impact macro print | No new entries; reduce open position to ≤5× |
| Data staleness | no closed bar in 3× TF | Block new entries |

Macro event source: ForexFactory weekly JSON (§5.4), filtered to `impact == "High"` and `country == "USD"`. For BTC this is FOMC, CPI, NFP, PCE. Default `event_window_hours = 4` (v1's 12 is too wide for a 1h system).

---

## 12. Backtest engine

The backtester's job is to be **pessimistic and honest**. Every ambiguity resolves against you.

### 12.1 Fill model

| Situation | Rule |
|---|---|
| Post-only entry | Filled only when a **1m bar trades through the limit by ≥1 tick**. Touching is not filling. |
| Queue position | Assume worst: you are last in the queue at your price. |
| Entry TTL | Unfilled after `entry_ttl_bars` → MISSED, recorded (miss rate is a headline metric). |
| Stop and target in the same bar | **Assume the stop.** Always. |
| Intrabar resolution | Walk **1m bars** inside every decision-TF bar. Never assume a path within a bar. |
| Stop fill | Taker + half-spread + 1 tick adverse. |
| Gap through stop | Fill at the 1m open beyond the stop, not at the stop price. |
| Funding | Charged per hour held, from `fundingHistory`. |

### 12.2 Cost accounting

```rust
let cost_bps = maker_bps                     // entry (post-only)
             + taker_bps + half_spread_bps   // exit
             + funding_bps(hours_held);
let cost_R  = cost_bps * entry / risk_per_unit;
let net_R   = gross_R - cost_R;
```

Every report prints `n, win%, gross_R, cost_R, net_R, t-stat, max_dd_R, trades/day, miss_rate, median_stop_pct`. **A report without `cost_R` is rejected by the report writer.**

### 12.3 Reference implementation

The Python harness used to produce §0's results lives in `research/` and is the reference the Rust backtester must match to within 1e-9 on a golden fixture. It is ~200 lines. Port it, do not reinvent it.

---

## 13. Search and overfitting control

### 13.1 Purged walk-forward with embargo

Train window W = 120 days, test T = 40, step = 40, on 1h BTC.

> **SEARCH-1 — Embargo.** Levels carry a `level_ttl_bars` = 300 history. A naive WF boundary leaks train-window levels into the test window. Insert an embargo of `≥ level_ttl_bars` between train end and test start. v1's walk-forward had this leak.

### 13.2 Selection

```
score = net_expectancy_R − 0.25 × max_drawdown_R − 0.02 × excess_trade_rate
```

> **SEARCH-2 — Never select the argmax.** With N configurations tested, the best is biased upward by roughly `σ·√(2 ln N)`. Select the **median of the top decile** instead, and report N alongside every result. §0's climax candidate is exactly this failure: best-of-25, +0.186R in-sample, +0.007R out.

### 13.3 Kill criteria — pre-registered, non-negotiable

Discard a configuration if **any** holds:

- Fewer than **150** test-window trades
- Net expectancy ≤ 0 after full cost
- **Sign flips between the two validation periods** (2023–2024 vs 2025–2026)
- t-statistic < 2.0 on the pooled test windows
- Winning params sit on the edge of any slider range
- Expectancy collapses >50% when re-run on the **HL** window (§13.4)
- Expectancy collapses >50% when trigger tolerances are perturbed by ±8 bps (cross-venue wick noise)

### 13.4 The cross-venue check — v2's replacement for v1's dual-ticker brake

BTC-only removes the "does it work on BTC *and* ETH" test. Its replacement is stronger and is grounded in measurement:

1. **Fit** structural parameters on Binance BTC 2023–2024.
2. **Validate** on Binance BTC 2025–2026. Sign must hold.
3. **Confirm** on the Hyperliquid rolling window (208 days of 1h, 52 days of 15m). Expectancy must not collapse.
4. **Perturb** every trigger tolerance by ±8 bps. If results move materially, you fit venue wick noise (COST-4), not structure.

Search **never** writes `strategy.toml`. Promotion is: sweep → lift table → operator reviews 10 best and 10 worst *pictures* → manual copy → paper → ARM.

---

## 14. Architecture

### 14.1 Workspace

| Crate | Responsibility |
|---|---|
| `stratum-data` | HL REST + WS; Binance Vision loader; Reservoir S3; parquet/sqlite store; reconnection; gap backfill |
| `stratum-features` | ATR, EMA, RSI, StochRSI, volume, `avg_trade_size`, `oi_delta`, `funding_z`, `basis`, `liq_cluster` |
| `stratum-levels` | Swings, clustering, **as-of store**, events |
| `stratum-templates` | Hypothesis slots H1–H4 + lift table; `signal()` is pure |
| `stratum-backtest` | 1m-resolved fill model, full cost, risk caps, equity curve |
| `stratum-search` | Purged WF, embargo, top-decile selection, lift tables, report |
| `stratum-risk` | The §11 table — one place, one implementation, used by paper and live alike |
| `stratum-oms` | Paper + live state machine, cloids, reconciliation, rate budget, kill switches |
| `stratum-live` | Agent-wallet signing, ARM, flatten-on-disconnect |

### 14.2 Apps

```
stratum-record   # WS recorder — ships first, runs forever
stratum-fetch    # Binance Vision + HL backfill into parquet
stratum-replay   # replay --params strategy.toml --from ... --to ...
stratum-sweep    # overnight purged walk-forward
stratum-paper    # live data, simulated fills, real risk engine
stratum-arm      # live, operator-gated
```

### 14.3 Stack

Rust + Tokio (no GC pauses on the WS path, type-safe orders, cheap VPS). Python + polars for the research harness — sweeps are exploratory and Python iterates faster; the Rust backtester is the production reference and must match it on a golden fixture. Parquet for bars, SQLite for signals/fills/journal, TOML for knobs with hot reload.

SDK: pick one in Phase 0 and pin it — `hyperliquid-dex/hyperliquid-rust-sdk` (official) or `infinitefield/hypersdk` (community, referenced by HL's own docs). Wrap it behind your own `ExchangeClient` trait so swapping costs one file.

---

## 15. Configuration

### 15.1 `strategy.toml` (v2 freeze)

```toml
[market]
venue    = "hyperliquid"
coin     = "BTC"
quote    = "USDC"

[tf]
decision   = "1h"
regime     = "4h"
trigger    = "5m"
resolution = "1m"

[features]
ema_fast = 20
ema_slow = 50
rsi_len  = 14
stoch_len = 14
vol_sma  = 20
oi_lookback = 6

[levels]
swing_left      = 3
swing_right     = 3
cluster_atr     = 0.25
touch_atr       = 0.20
break_atr       = 0.15
level_ttl_bars  = 300
min_touches     = 2
min_band_bps    = 25        # COST-4 — do not lower

[exec]
entry              = "post_only"    # COST-2
allow_taker_entry  = false
max_entry_reprices = 1
entry_ttl_bars     = 2
emergency_flatten  = "market"

[costs]
maker_bps        = 1.5
taker_bps        = 4.5
half_spread_bps  = 0.63
referral_pct     = 4.0
charge_funding   = true

[risk]
risk_pct          = 0.02      # 2% — NOT v1's 10%
max_leverage      = 10
min_stop_pct      = 0.006     # COST-1
max_stop_pct      = 0.030
liq_buffer_ratio  = 0.40      # SIZE-1
min_notional_usd  = 10.0
max_trades_day    = 2
daily_kill_pct    = 0.10
green_day_stop    = 0.25
max_consec_losses = 4
weekly_dd_stop    = 0.25

[events]
hold_events        = false
event_window_hours = 4
calendar_source    = "forexfactory"
impact_filter      = ["High"]
currency_filter    = ["USD"]

[mode]
auto_live       = false
arm_ttl_minutes = 120
```

### 15.2 `search.toml`

```toml
[walkforward]
train_days = 120
test_days  = 40
step_days  = 40
embargo_bars = 300            # SEARCH-1 — must be >= levels.level_ttl_bars

[validation]
fit_period     = ["2023-01-01", "2024-12-31"]
validate_period= ["2025-01-01", "2026-08-28"]
confirm_venue  = "hyperliquid"
perturb_bps    = 8            # cross-venue wick noise
require_sign_stability = true

[selection]
method       = "top_decile_median"   # SEARCH-2 — never argmax
min_trades   = 150
min_t_stat   = 2.0
lambda_dd    = 0.25
mu_trade_rate= 0.02

[ranges]
cluster_atr  = { min = 0.15, max = 0.45, step = 0.05 }
touch_atr    = { min = 0.10, max = 0.40, step = 0.05 }
stop_atr     = { min = 1.0,  max = 3.5,  step = 0.25 }
rr           = { min = 1.0,  max = 3.0,  step = 0.25 }
min_touches  = { min = 2,    max = 4,    step = 1 }
level_ttl    = { min = 150,  max = 500,  step = 50 }
```

---

## 16. Build plan — gated, and designed to fail fast

The v1 plan spent Phases 0–2 (10 days) building toward a strategy that §0 shows is negative. v2 inverts the order: **the falsification harness comes first**, because the cheapest thing you can do is prove yourself wrong in two days instead of three weeks.

### Phase 0 — Recorder and history (Days 1–2)

- [ ] Cargo workspace, clippy + fmt + deny warnings, pre-commit secret scan
- [ ] **`stratum-record` shipped and running.** Every hour it is not running is HL data you cannot recover.
- [ ] `stratum-fetch`: Binance Vision 2023-01 → today, 1m, checksum-verified → parquet
- [ ] HL backfill: 1h (208 days), 15m (52 days), 5m (17 days) → parquet
- [ ] Referral code applied to the trading account (permanent 4% fee cut — do it now)
- [ ] Unit test: 1m → 1h aggregation against a hand-checked window
- [ ] **Gate 0:** `stratum-replay --sanity` reproduces §0's baseline table to within 1e-6

### Phase 1 — Levels match the eye (Days 3–5)

- [ ] ATR, EMA, RSI, StochRSI, volume, `avg_trade_size`
- [ ] Swings + clustering + **as-of store** with the look-ahead assertion test
- [ ] Overlay computed clusters on 10 operator-chosen BTC sessions
- [ ] **Gate 1 (inherited from v1, unchanged):** operator says *"these lines are what I was looking at."* If not — fix clustering. **Do not write a template.**

### Phase 2 — Falsification harness (Days 6–8)

- [ ] Backtester with the §12 fill model, 1m resolution, full cost
- [ ] Lift-table engine (§9.4)
- [ ] Purged WF with embargo (§13.1)
- [ ] Reproduce §0's negative results in Rust; they must match the Python harness
- [ ] **Gate 2:** the harness correctly rejects v1's T1 with net ≈ −0.19R OOS. *A harness that cannot reproduce a known-bad result cannot be trusted with a maybe-good one.*

### Phase 3 — Hypothesis testing (Days 9–16)

- [ ] Ingest `oi_delta`, `funding_z`, `basis`, `liq_cluster` (Coinalyze + Reservoir)
- [ ] Test H1, H2, H3, H4 against §13.3 kill criteria
- [ ] Lift table for every condition, both periods
- [ ] Operator reviews 10 best / 10 worst **pictures** per surviving hypothesis
- [ ] **Gate 3 — the hard one.** Proceed to paper *only* with a hypothesis that has: n ≥ 150 test trades, net expectancy > 0 after full cost, **sign stable across both periods**, t ≥ 2.0, survives ±8 bps perturbation, and survives on the HL window.
- [ ] **If nothing clears Gate 3: do not trade.** Return to Phase 3 with new hypotheses. The account is not the deadline; the edge is. This is the single most valuable instruction in this document.

### Phase 4 — Paper (Days 17–30)

- [ ] Live WS, simulated fills, **real** risk engine, real rate-limit accounting
- [ ] Telegram/log alerts with full reason strings
- [ ] Every signal journaled, including MISSED
- [ ] **Gate 4:** 14 consecutive days, zero rule breaches, and paper expectancy within 1 standard error of backtest expectancy. A gap means the fill model is wrong — fix it before risking money.

### Phase 5 — Armed live

- [ ] ARM only. One template. $0.30 risk per trade.
- [ ] First 20 trades at **half** table risk (1%)
- [ ] 100 live-or-paper fills before `auto_live` is even discussed
- [ ] Weekly: live vs backtest expectancy, slippage, miss rate, fee ratio, request budget

---

## 17. Testing

**Feature tests** — every indicator against hand-computed fixtures.

**Look-ahead assertion** — `levels.as_of(t)` must be identical computed forward-only vs. rebuilt from full history. Run over 1,000 random `t`. This test catches the bug class that makes backtests beautiful and live trading expensive.

**Golden replay** — one BTC week checked into git with expected signals and reason strings. Any drift fails CI. Reason strings are part of the contract.

**Cost invariant** — every backtest trade asserts `net_R == gross_R − cost_R` exactly.

**Bit-stability** — same parquet + same TOML → byte-identical output on two machines.

**OMS property tests:**
- No add-to-loser, under any sequence of signals
- No third trade after the cap
- Duplicate `cloid` never doubles the position
- Stop exists within one tick of any fill
- Stale WS → cancel entries, then flatten
- Rate budget: a repricing storm never drops the reserve below 500 requests
- Restart mid-position reconciles to on-chain truth, not local state

**Risk-engine table test** — every row of §11, asserted.

**Chaos test** — kill the process mid-position; the exchange-side reduce-only stop must still protect the account. Run it on testnet before it happens on mainnet.

---

## 18. Production operations

### 18.1 Deployment

- Hetzner CX22 or equivalent (~€4/mo), Debian, Frankfurt or Ashburn
- `systemd` units for `stratum-record` and `stratum-paper`/`stratum-arm`, `Restart=always`
- `chrony` for NTP — **mandatory**, nonces are ms timestamps
- UFW: outbound 443 only
- Daily `sqlite3 .backup` + parquet rsync to a second location
- Log rotation; keep 90 days of signals and fills

### 18.2 Monitoring — alert on all of these

| Condition | Severity |
|---|---|
| WS stale > 8s | warn |
| WS stale > 60s | **page** — flatten fires |
| Position without a resting stop | **page** |
| Rate-limit reserve < 1000 requests | warn |
| Rate-limit reserve < 500 | **page** |
| Daily kill triggered | **page** |
| Local equity vs `clearinghouseState` mismatch > $0.10 | **page** |
| Recorder gap > 5 minutes | warn |
| Live slippage > 2× modelled | **page** — the fill model is wrong |
| Order reject rate > 20% | warn |

### 18.3 Runbook

**Flatten now:** `stratum-arm --flatten --confirm` → verify via `clearinghouseState` → if the process is unreachable, use the Hyperliquid web UI. Keep the UI logged in on your phone. This is the actual disaster recovery plan and it is fine.

**Rate-limited (1 req/10s):** stop all non-flatten activity. You still have the exchange-side stop. Wait for volume to replenish the allowance.

**Suspected key compromise:** revoke the agent wallet from the master account immediately (the agent cannot withdraw — this is why you use one), then flatten from the UI.

---

## 19. Operator cadence — revised to match measured reality

v1 budgeted 12 hours of market availability for 2 trades/day. Measured signal frequency for anything selective is **0.2–1.5 trades/day**. Sitting at the screen does not create setups; it creates trades.

| Block | Duration | Work |
|---|---|---|
| Morning | 15 min | Check recorder health, gaps, request budget. Read overnight signals and their reason strings. Mark levels; compare with the engine's. |
| Day | — | **Alerts only.** The engine watches; you do not. If it fires and you are available and it is ARMed and the score holds — take it. Otherwise it is a MISSED and that is a data point, not a failure. |
| Last hour UTC | — | No new entries. Manage or flatten. |
| Evening | 30 min | Label every signal: taken / skipped / wrong-template / missed. One paragraph: what the eye saw that the code missed, or vice versa. |
| Weekly | 60 min | Live vs backtest expectancy. Slippage. Miss rate. Fee ratio. Request budget. Lift table refresh. |

**Journal card (required, or the day did not happen):** date · signal id · what I saw · what the code said · what I did · entry · stop · target · net R · cost R · take-again Y/N.

The journal is not a diary. It is the labelled dataset that makes the next hypothesis better than the last one.

---

## 20. Risk register

| Risk | Severity | Mitigation |
|---|---|---|
| **No edge exists at this timeframe on this instrument** | **Critical — and currently the base case** | §0 shows v1's edge is negative and the alternatives do not replicate. Gate 3 refuses to trade without proof. This is the honest headline risk. |
| Fees consume the edge | Critical | COST-1/2/3. Maker-first, 0.60% stop floor, cost always inside R. |
| Overfitting the sweep | High | Purged WF + embargo + top-decile selection + two-period sign stability + ±8 bps perturbation. |
| Look-ahead in the level store | High | As-of API + assertion test over 1,000 random timestamps. |
| Backtest/live divergence | High | 1m-resolved pessimistic fill model; Gate 4 requires paper to match backtest within 1 SE. |
| HL candle buffer loses history | Medium | Recorder from day 1; Binance + Reservoir for depth. |
| Rate limit blocks an **exit** | Medium | 500-request reserve, budget accounting, no repricing loops. |
| Key compromise | Medium | Agent wallet only (cannot withdraw), monthly rotation, expiry set. |
| Process death with open position | Medium | Exchange-side reduce-only stop; chaos test on testnet. |
| Single-instrument concentration | Medium | Accepted deliberately. Replaced by cross-venue + cross-period validation. |
| Binance proxy misleads on triggers | Medium | Measured: 70.6% pivot agreement. COST-4 noise floor; HL confirmation mandatory in Gate 3. |
| $15 book dies on one leveraged hold through a macro print | Medium | Event window, 10× cap, 2% risk, exchange-side stop. |
| Target arithmetic tempts higher leverage | **High (behavioural)** | §4.3 states the arithmetic. The Monte Carlo table is the argument. Risk caps are enforced in code, not in willpower. |

---

## 21. Open decisions

| Decision | Default until changed |
|---|---|
| Rust SDK | Pick official `hyperliquid-rust-sdk` or `hypersdk` in Phase 0; wrap behind own trait |
| Store | Parquet for bars, SQLite for signals/fills/journal |
| Research language | Python harness is the reference for exploration; Rust must match on a golden fixture |
| Reservoir ingest | Phase 3, BTC only, when `liq_cluster` is tested |
| Dashboard | After Gate 4. CLI + markdown report until then. |
| HYPE staking for fee discount | Not until equity > $1,000 — the capital is better used as margin |
| Auto mode | Not until 100 fills and a stable weekly review |

---

## 22. Day-1 commands

```bash
# 1. Verify the venue is reachable and BTC metadata is what this doc assumes
curl -s -X POST https://api.hyperliquid.xyz/info \
  -H 'Content-Type: application/json' -d '{"type":"meta"}' \
  | python3 -c "import json,sys;u=json.load(sys.stdin)['universe'];b=[a for a in u if a['name']=='BTC'][0];print(b)"
```

```bash
# 2. Confirm the candle-retention limit yourself — do not take this document's word for it
curl -s -X POST https://api.hyperliquid.xyz/info -H 'Content-Type: application/json' \
  -d '{"type":"candleSnapshot","req":{"coin":"BTC","interval":"1h","startTime":0,"endTime":9999999999999}}' \
  | python3 -c "import json,sys,time;c=json.load(sys.stdin);print(len(c),'bars, oldest',time.strftime('%Y-%m-%d',time.gmtime(c[0]['t']/1000)))"
```

```bash
# 3. Pull deep history — free, no key, ~90 seconds for 3.5 years
python3 scripts/fetch_binance.py --symbol BTCUSDT --from 2023-01 --to 2026-08 --out data/bars/venue=binance/
```

```bash
# 4. Start the recorder. Do this before anything else and never stop it.
cargo run --release --bin stratum-record -- --coin BTC --out data/bars/venue=hl/coin=BTC
```

```bash
# 5. Reproduce this document's negative result. If you cannot, your harness is wrong.
cargo run --release --bin stratum-replay -- --params config/strategy.toml \
  --template v1_t1_reject_wick_weak_volume \
  --from 2023-01-01 --to 2024-12-31 --expect-net-R -0.19
```

---

## 23. Immediate next action

1. Start `stratum-record`. Today. Every hour costs you data you cannot buy back.
2. Apply the referral code to the trading account — a permanent 4% fee cut, five minutes of work, and fees are the dominant term in §3.
3. Pull Binance BTC 1m from 2023-01. It is free and takes ninety seconds.
4. Build the levels engine and sit with the overlay until Gate 1 passes.
5. Build the falsification harness and reproduce §0's negative results.
6. **Only then** start proposing hypotheses.

Do not write a live order module until Gate 3 passes.

---

*End of specification. Stratum v2.0 — 28 August 2026.*

*Update this document when a knob default is frozen from walk-forward, or when a hypothesis is killed by measurement. Not when a single session feels right.*

*Every number in §0, §2.1, §2.2, §3, §4.2 and §5 was measured on live endpoints or on 1.88 million bars of real BTC data on 2026-08-28. The measurement code is in `research/`. Re-run it before you trust it.*
