# Stratum

**Product specification**  
Version 1.1 · 28 August 2026 · Markdown source of record

A parameterized confluence engine plus a situation-analog reporter for Hyperliquid perps.

The operator reads charts by eye (EMA, RSI, volume, clustered support/resistance, location candles). Stratum turns that language into functions, finds historical cousins of the *current situation* (not the exact price), and prints what happened next as frequencies.

This document is an engineering spec, not investment advice. Live trading can lose the entire account. Frequencies are not forecasts.

---

## 1. Problem

The operator already sees situations:

- price lost a mid shelf and is testing it from below
- RSI diverged while price made a lower low
- 1m lifted into the underside and stalled
- a range low was swept and price is mid-box

The painful question is always the same:

> Will it go to the next purple line?

That question has no honest answer. The useful question is:

> The last N times the tape looked like *this structurally*, what distribution of paths followed on 1m / 5m / 1h / 1d?

Without that, “wait” feels like prison and “click” feels like gambling. Both feelings come from the same gap: no written situation, no measured cousins, no end condition for the wait.

---

## 2. Product thesis

1. A **level** is an area where buyer/seller balance can change. It is not a wall.
2. A **wick** is not a break. A **close** plus a failed reclaim is a break.
3. A **situation** is a snapshot of structure, location, regime, stretch, and volume — in ATR units, never raw dollars.
4. Code does not invent strategy. The operator defines templates and knobs. Code finds every historical bar that matched and scores outcomes after fees.
5. Live entries still require a **written trigger candle**. Analogs advise. They do not click.

---

## 3. Goals

- Encode EMA, RSI / Stoch RSI, volume, clustered S/R, volume-at-price nodes, and four location candles as testable code.
- Label every 5m close with a **situation vector** and an optional **bucket**.
- Retrieve historical cousins on BTC first (ETH later) across 1m context, 5m identity, 1h/1d filters.
- Report forward outcomes as counts and frequencies, including “still inside / chop.”
- Compare **click now** vs **wait for trigger** on the same situation class.
- Paper, then armed-live, under a hard micro-account risk table.
- Expose every threshold in TOML. Search ranges. Never auto-promote a sweep winner to live.

---

## 4. Non-goals

- HFT, ALO queue racing, validator / order-book node infrastructure.
- Genetic programming that invents new indicators.
- “AI found a pattern” with no human-readable reason string.
- Predicting that price *will* travel yellow → purple.
- Trading thin meme perps on a ~$15 book.
- Holding 10x–40x through known unlocks without an explicit flatten rule.
- Guaranteeing $15 → $1,000.

---

## 5. Users and context

| Field | Value |
|---|---|
| Operator | Discretionary reader moving toward systematic rules (software / web3 engineer) |
| Venue | Hyperliquid L1 perps, USDC collateral |
| Language | Rust core, TOML config, Markdown reports |
| Account | ~$15 isolated challenge book, target $1,000 as stage 7 not a quota |
| Session | Up to 12h watch, 6h review. Max 2 trades/day |
| Decision TF | 5m |
| Execution TF | 1m |
| Context TF | 1h, 1d as filters only |

---

## 6. Universe

Until $100 equity the engine only scores and trades the Core book.

| Bucket | Tickers | Role |
|---|---|---|
| Core | BTC first; then ETH, SOL, HYPE, XRP, BNB, LINK, DOGE | Research + live |
| Watch | SUI, AAVE, TAO, ZEC, UNI, NEAR | Replay only until $100 |
| Ban under $200 | PUMP, FARTCOIN, CASHCAT, PENGU, TRUMP, thin books | Wick risk > $1.50 stop |

Hard constraint: one ticker in position at a time.  
v1 analog tables: **BTC 5m only**. Add ETH when BTC buckets are frozen.

---

## 7. Account and cost constraints

| Item | Rule |
|---|---|
| Starting equity | ~$15 USDC isolated |
| Risk per trade at $15 | $1.50 (10% of equity) |
| Working margin | $7–8, not the full $15 |
| Starting notional | ~$75–80 at 5–10x |
| 40x | Optional later, only if replay shows stop ≤ ~0.5% and dollar risk stays $1.50 |
| Max trades / session | 2 |
| Daily kill | −20% while equity < $50 |
| Green-day stop | +25% on the day → flatten |

Taker fee ≈ 0.045% per side (≈ 0.09% round trip) plus spread.  
A 0.20% scalp on $80 notional is noise after fees. Engine targets 0.5R–1R with stops about 0.8%–1.5% of price, or cuts size if the stop must be wider than 2%.

If stop width > 2% of price, shrink notional. Never widen the stop to keep leverage.

---

## 8. Product surfaces

| Surface | Human | Code |
|---|---|---|
| `strategy.toml` | Live knobs | Hot-reload. Paper/live read only this file |
| `search.toml` | Ranges for a sweep | Walk-forward search. Writes a report. Never writes `strategy.toml` |
| Analog report | Reads cousins + pictures | Situation vector → neighbors/bucket → outcome table |
| Journal | Labels take / skip / wrong-template | Stores labels for later bucket refinement |
| ARM command | Enables one live template on one ticker | Places brackets only after ARM |

Promotion path:

```text
sweep or analog table
    → human looks at 10 best / 10 worst pictures
    → manual copy into strategy.toml
    → paper
    → ARM
    → live
```

No automatic promotion.

---

## 9. Feature specification

If a quantity cannot be computed from stored OHLCV (and optional L2/trades), it does not exist. No TradingView scrape.

### 9.1 Bars

Canonical bar: `{ ts, ticker, tf, o, h, l, c, v }`.

1m is stored. 5m, 15m, 1h, 1d are aggregated from 1m  
(open = first, high = max, low = min, close = last, volume = sum).

Missing 1m bars may extend the time index. Volume is never invented.

### 9.2 ATR

Wilder ATR(14) on the decision TF. All distances are in ATR units so the same toml works on BTC and ETH.

### 9.3 EMA

```text
EMA_t = α P_t + (1−α) EMA_{t−1}
α = 2 / (n+1)
seed = SMA of first n closes
```

| Output | Default | Use |
|---|---|---|
| ema_fast | 20 on 5m | Tactical regime |
| ema_slow | 50 on 5m | Structure filter |
| ema_fast_slope | sign(EMA_t − EMA_{t−5}) | Rising / falling |
| dist_ema_atr | (close − ema_fast) / ATR | Extension |
| stack_up | close > ema_fast > ema_slow | Long regime |
| stack_down | close < ema_fast < ema_slow | Short regime |

EMA is a filter, never an entry.

### 9.4 RSI and Stochastic RSI

Wilder RSI(14).  
Stoch RSI = (RSI − RSI_low) / (RSI_high − RSI_low) over 14, then SMA-smooth %K/%D (3).

| State | Default | Meaning |
|---|---|---|
| rsi_ob | > 70 | Stretch long — fade candidate only at resistance |
| rsi_os | < 30 | Stretch short — cover / do-not-add at support |
| stoch_floor | %K and %D < 20 | 5m momentum spent lower |
| stoch_ceil | %K and %D > 80 | 5m momentum spent higher |
| rsi_bear_div | price HH, RSI LH on last two *confirmed* swings | Optional T1 confirm |
| rsi_bull_div | price LL, RSI HL on last two *confirmed* swings | Brake on late shorts / T3 |

Divergence is computed only on confirmed swing points. Never on raw consecutive bars.

### 9.5 Volume

| Feature | Definition | Default |
|---|---|---|
| vol_sma | SMA(volume, 20) | 20 |
| vol_z | (vol − mean20) / std20 | 20 |
| vol_ratio | sum(vol current push) / sum(vol prior push) | push = bars from last opposite swing |
| climax | vol_z > vol_climax | 2.0 |
| weak_second | vol_ratio < vol_weak_max | 0.80 |

### 9.6 Support / resistance — clustered swings

This module is the product. If clustering does not match the operator’s eye on sample days, stop here.

**Swing:** bar `i` is a 5m swing high if `high[i] = max(high[i−L..i+R])` and the right window has closed. Same for lows. Default `L = R = 3`.

**Cluster:** merge swings if `|price − cluster_mean| ≤ cluster_atr × ATR`. Keep mean, touch count, last touch, member volume, polarity (support vs resistance).

**Expire:** no touch for `level_ttl_bars` (default 400 on 5m) and strength below `min_strength`.

| Event | Definition |
|---|---|
| At level | \|close − level\| ≤ touch_atr × ATR, or wick traded the band |
| Reject | Wick beyond the band, 5m close back inside |
| Break | 5m **close** beyond the band by break_atr × ATR |
| Failed reclaim | Break, then within reclaim_bars a return that cannot close back through |
| Accept | Two consecutive 5m closes beyond the band |

Eye-match gate for BTC 5m (27–28 Aug 2026 sample): recover the ~81.4k spent high, the ~79.95–80.00 flipped shelf, and the ~78.9–79.0 shelf without a forest of junk lines.

### 9.7 Poor-man’s liquidity map

True liquidation heatmaps are a different dataset. v1 approximates accepted liquidity from tape.

- Bin size = max(native tick, `vp_bin_atr × ATR`). Default `vp_bin_atr = 0.10`.
- Each 1m bar dumps volume into the bin of typical price `(H+L+C)/3`.
- Volume node: bin ≥ `vp_peak_mult × median` in a rolling window (default 12h). Default mult = 2.5.
- Promote a node to a level if it sits within 0.25 ATR of a swing cluster.

v2 (later): accumulate HL `l2Book` / prints by price. Do not block v1.

### 9.8 Candles (four only, and only at a level)

| Pattern | Rule | Intent |
|---|---|---|
| reject_wick | Wick ≥ 1.5 × body, close back inside prior range | T1 / T3 |
| engulf | Body fully covers prior body; close in trade direction; vol ≥ vol_sma | T1 / T2 |
| inside_break | Close outside mother bar toward trade | T2 trigger |
| climax_fail | vol_z > climax, next bar opposite through 50% of climax bar | Exhaustion |

A hammer in the middle of a range is not a pattern. Location first.

---

## 10. Strategy templates

Three templates. No fourth until 100 accepted paper trades exist on the first.

### 10.1 T1 — Failed high fade

Visual: second tap of a marked high, weaker volume, rejection, oscillators rolling over.  
This is the 85.2–85.4 HYPE short. It is not the 84.02 dip short.

| Knob | Default |
|---|---|
| swing_left / swing_right | 3 / 3 |
| touch_atr | 0.25 |
| min_bars_between / max_bars_between | 6 / 72 |
| vol_weak_max | 0.80 |
| need_stoch_roll | true |
| need_rsi_div | false |
| entry | close_back_under |
| stop_atr | 0.35 |
| t1_r | 1.0 |
| trend_filter | lower_highs_or_below_fast |

Invalidation: 5m accept above the cluster (two closes). Flatten. Do not add.

### 10.2 T2 — Break and failed reclaim

Visual: level gives way on a close, bounce cannot recapture it.

| Knob | Default |
|---|---|
| break_tf | 5m |
| reclaim_bars | 8 |
| reclaim_max_pen_atr | 0.20 |
| need_ema_agree | true |
| stop_atr | 0.40 |
| t1_r | 1.0 |

### 10.3 T3 — Stretch into opposite shelf

Visual: RSI / Stoch spent while price arrives at the next cluster.  
Default action is **manage**, not reverse.

| Knob | Default |
|---|---|
| stoch_lt | 20 |
| rsi_lt | 35 |
| shelf_touch_atr | 0.25 |
| action | reduce_or_cover |

`flip` stays off until $200 equity.

---

## 11. Confluence score

A bar is a candidate only if it sits at a cluster.

| Condition | Points |
|---|---|---|
| At clustered S/R or volume node | +2 (required; else skip) |
| EMA stack agrees with direction | +2 |
| Valid location candle | +2 |
| Volume confirms (weak second or climax_fail) | +1 |
| RSI / Stoch state agrees | +1 |
| Against EMA stack without T1 complete | −2 |
| Event window and `hold_events = false` | block |

Default `min_score = 6`.

Every signal carries a reason string:

```text
T1 SHORT BTC 5m 80012 score=7 vol_ratio=0.74 reject_wick stop=80110 t1=79600
```

If the operator cannot read the string, the template is not ready.

---

## 12. Situations and analogs (core of v1.1)

### 12.1 Situation vector

Taken at every **5m close**. Prices only appear as ATR distances and ranks.

```text
loc_res_atr          distance to nearest resistance cluster / ATR
loc_sup_atr          distance to nearest support cluster / ATR
side_of_broken       under_flipped | over_flipped | none
ema_regime           below_stack | above_stack | mixed
structure_5m         LH_LL | HH_HL | range
rsi_zone             os | mid | ob
rsi_div              bull | bear | none
vol_state            climax | dry | normal
dist_up_atr          ATR to next upper cluster
dist_down_atr        ATR to next lower cluster
hour_utc
```

1m contributes extra fields on the same 5m snapshot (last 5 ones):

```text
m1_lift_into_level     true | false
m1_macd_state          rising | flat | rolling_over
m1_vol_pop             true | false
```

1h / 1d are filters, not identity:

```text
h1_regime, h1_loc_in_range (0–1), h1_ext_atr
d1_regime, d1_loc_in_range
```

Do not search 1m analogs as the identity of a situation. 1m twins are cheap and meaningless.

### 12.2 Buckets first, neighbors later

v1 uses named buckets so the operator can read them. Neighbor search (z-scored Euclidean / cosine) is v1.1 after buckets stabilize.

Frozen starter buckets (BTC 5m):

| ID | Name | Plain language |
|---|---|---|
| B1 | underside_retest | Lost a mid shelf on close, now testing it from below |
| B2 | failed_high_t1 | Second tap of a marked high, weak volume |
| B3 | range_low_hold | Sweep or touch of range low, close back inside |
| B4 | range_mid | Inside a 5m/1h box, not at a wall |
| B5 | stretch_into_shelf | RSI/Stoch os or ob *at* the opposite cluster |
| B6 | accept_break | Two 5m closes beyond the band, first pause |

A bar may belong to one primary bucket. If two fire, pick the higher-priority: B2 > B1 > B6 > B3 > B5 > B4.

### 12.3 Forward outcomes

From analog time `t`:

**Horizon A** — 12 × 5m bars (~1 hour)  
**Horizon B** — 36 × 5m bars (~3 hours)  
**Horizon C** — 12 × 1h bars (optional, slow situations only)

Record:

```text
hit_upper_first
hit_lower_first
still_inside
close_through_upper
close_through_lower
bars_to_first_touch
MFE_atr_if_short_t
MAE_atr_if_short_t
MFE_atr_if_long_t
MAE_atr_if_long_t
hit_1R_before_stop_if_short_after_fees
hit_1R_before_stop_if_waited_for_trigger
```

Fees: 4.5 bps taker each side + 1 tick slip.

### 12.4 Report shape

```text
Situation: B1 underside retest after 5m break
           bullish RSI div, 1m lift stalling
Ticker: BTC   TF identity: 5m
Window: last 120 calendar days
Analogs: 84

Next 12 × 5m bars
  tagged upper first     38%   (32)
  tagged lower first     31%   (26)
  still inside           31%   (26)

If shorted at t
  median MAE    0.42 ATR
  median MFE    0.35 ATR
  1R before stop after fees   41%

If waited for 5m reject close
  analogs 29
  1R before stop              58%
  still inside                22%

Pictures: 8 analog paths attached
```

Rules:

- If analog count < 30, print the count and **do not** print a clean percentage as a headline.
- Always print chop / still_inside. Hiding it is how tables lie.
- The analog engine never places an order.

### 12.5 Why this kills the wait-vs-gambling loop

Wait with no score feels like prison.  
Click with no cousins feels like gambling.

After this exists, a stall under a flipped shelf can say: short-now 1R = 41%, wait-for-reject-close 1R = 58%, chop = 31%. Then wait is a measured choice, not a personality.

---

## 13. Written live triggers (session rules)

These are the only clicks allowed until templates are frozen. Analogs may comment. They may not add a fifth trigger.

**BTC**

```text
SHORT  if 5m closes back under ~79,990 after a lift into it
LONG   if 5m closes above ~79,990 and the next 5m holds
```

**ETH**

```text
LONG   if 5m holds ~2,484–2,490 on a pullback
    or 5m closes above 2,534 and holds
SHORT  if 5m tags ~2,534 and closes back under
```

Mid-range / mid-air / first wick: no.

```text
IF none of the written candles printed
    → flat is a completed session
IF one printed and I still do not click
    → fear, not discipline
IF none printed and I click anyway
    → gambling
```

Levels in this section are *session examples* from 28 Aug 2026. The engine uses clusters, not hardcoded prints, once clustering matches the eye.

---

## 14. Search and overfitting control

`search.toml` lists ranges. Walk-forward: train 60 calendar days, test 20, step 20.

```text
score = expectancy_R_after_fees
      − λ × max_drawdown_R
      − μ × excess_trade_rate
```

Defaults: `λ = 0.25`, `μ = 0.02` per trade above 2/day.

Discard if:

- fewer than 100 test-window trades across the walk-forward
- works only on one ticker
- winning knobs sit on every slider edge
- analog bucket was defined *after* seeing the outcome table

Search never writes `strategy.toml`.

---

## 15. Execution and OMS

- One net position. No hedge. No add to losers.
- Entry: limit at level preferred. Market only to flatten.
- Stop: reduce-only, beyond cluster + `stop_atr`.
- Scale: 50% at `t1_r` or next opposite cluster, whichever is closer. Remainder stop → breakeven + 1 tick.
- Client order ids on every order. Idempotent place.
- If WS stale > 8s: cancel working entries; flatten 1m-sensitive positions per policy.
- ARM mode: live orders only after `ARM <TICKER> <T1|T2>`.
- `auto_live` default false.
- `hold_events` default false. Calendar file of unlocks / catalysts. Inside `event_window_hours` (12) no new 10x; flatten 10x to flat or 2x max if operator overrides.

### Risk table (code must enforce)

| Equity | Risk / trade | Lev cap | Daily kill | Names |
|---|---|---|---|---|
| $15–30 | $1.50 | 10x | −20% | Core 8 |
| $30–50 | $2.50 | 8–10x | −15% | Core 8 |
| $50–100 | $4 | 5–8x | −12% | Core + watch |
| $100–200 | $6–8 | 5x | −10% | Core + watch |
| $200–400 | 4% | 3–5x | −8% | Top 15 liquid |
| $400–700 | 3% | 3x | −6% | Top 15 |
| $700–1000 | 2% | 2–3x | −5% | Top 15 |

---

## 16. Software architecture

```text
crates/
  stratum-data         HL candleSnapshot + WS; parquet store
  stratum-features     ATR EMA RSI Stoch vol swings clusters VP candles
  stratum-templates    T1 T2 T3 + score() → Signal
  stratum-situations   vector, bucket label, neighbor index
  stratum-outcomes     forward scanner
  stratum-backtest     next-bar fill, fees, daily caps
  stratum-search       grid / TPE, walk-forward
  stratum-oms          paper + live state machine
  stratum-live         rust SDK signing, ARM, flatten-on-disconnect

apps/
  stratum-replay
  stratum-sweep
  stratum-analogs      “what did cousins do?”
  stratum-paper
  stratum-arm
```

`signal(feat, levels, params) -> Option<Signal>` is pure. No I/O inside templates.

Stack: Rust + Tokio, official or community Hyperliquid Rust SDK, parquet for candles, SQLite for signals/fills/analogs, TOML knobs, $5–20 VPS.

Public API: prefer WebSocket; respect ~1200 REST weight/min/IP; do not poll `l2Book` in a tight REST loop. 5m confluence does not need a 128GB node.

---

## 17. Default `strategy.toml` (v1 freeze)

```toml
tf_decision = "5m"
ema_fast = 20
ema_slow = 50
rsi_len = 14
stoch_len = 14
swing_left = 3
swing_right = 3
cluster_atr = 0.25
touch_atr = 0.25
break_atr = 0.15
vol_weak_max = 0.80
vol_climax = 2.0
wick_body_mult = 1.5
min_score = 6
max_trades_day = 2
hold_events = false
auto_live = false

[t1]
entry = "close_back_under"
stop_atr = 0.35
t1_r = 1.0

[t3]
action = "reduce_or_cover"
```

---

## 18. Build plan

### Phase 0 — repo and data (days 1–2)

- Workspace, clippy + fmt, no secrets in git.
- Ingest ≥ 120 days of BTC 1m (ETH optional). Persist parquet.
- Unit test 1m → 5m aggregation.

### Phase 1 — features match the eye (days 3–6)

- EMA, RSI, Stoch RSI, ATR, volume z. Snapshot-test one known session.
- Swings + clusters. Overlay 27–28 Aug 2026 BTC 5m. Recover 81.4k / 79.95–80.00 / 78.9–79.0.
- Volume profile nodes.
- Four candle detectors with `at_level` gate.

Exit: operator says “these lines are what I was looking at.”

### Phase 2 — templates + replay (days 7–10)

- T1 T2 T3 + score() + reason strings.
- Replay 90 days BTC. CSV of every signal.
- Operator labels 50 rows.

### Phase 3 — situations + analogs (days 11–16)

- Situation vector at each 5m close.
- Implement B1–B6.
- Outcome scanner + Markdown report.
- Freeze B1 definition *before* reading its table.
- Human review of 8 analog thumbnails.

### Phase 4 — search (days 17–20)

- Walk-forward on T1 only.
- Manual freeze into `strategy.toml`.

### Phase 5 — paper OMS (days 21–28)

- Live WS, simulated fills, risk table, 2-trade cap.
- 7 consecutive paper days without a rule breach.

### Phase 6 — armed live

- ARM only. Size from the $15 table. BTC. T1 only.
- 100 live-or-paper fills before T2 or a second coin.

---

## 19. Operator cadence

12 hours available ≠ 12 hours of orders.

| Block | Work |
|---|---|
| Prep 30 min | Core levels vs engine levels. 3 names max |
| Hunt | Watch. Click only if a written trigger printed. Max 2 |
| Last hour | No new entries |
| Review 6h | Label every signal and every analog miss. One paragraph: what the eyes saw that code missed |

Journal card (required or the day did not happen):

```text
Date:
Ticker:
Bucket / template:
What I saw:
What code / analogs said:
What I did:
Stop:
Target:
Result R:
Take again? Y/N
```

---

## 20. Testing

- Pure feature tests against fixture candles.
- Golden-file replay: one BTC day checked into git; reason strings must not drift silently.
- Swing confirmation must not use future bars beyond `R`.
- Outcome scanner must not leak `t+1` unconfirmed swings into the vector at `t`.
- OMS: no add-to-loser, no third trade, flatten on accept-above-high, shrink size when stop > 2%.
- Duplicate cloid does not double position.
- Stale WS → cancel entries / flatten per policy.
- Analog report with n < 30 refuses a headline percentage.

---

## 21. Risks and limitations

- Visual edge may not survive fees. Replay exists to discover that cheaply.
- Cluster knobs that fit one squeeze will fail on another week. Walk-forward is mandatory.
- Heatmap v1 is not liquidation data.
- Analog frequencies are conditional on the recent sample. Markets change.
- Public API latency is hundreds of ms. Fine for 5m. Fatal if someone “just adds HFT” without a node.
- A $15 book can still die on one 10x hold through an unlock.
- A pretty analog table defined after seeing outcomes is just overfitting with extra steps.

---

## 22. Open decisions

| Decision | Default until changed |
|---|---|
| SDK | Official `hyperliquid-rust-sdk` or `hypersdk` — pick in Phase 0 |
| Store | Parquet candles, SQLite signals / fills / analogs |
| CCI | Computed, off in T1 score unless enabled |
| Neighbor search | After buckets freeze |
| L2 heatmap v2 | After Phase 3 |
| Dashboard | After paper is stable |
| ETH analogs | After BTC B1–B6 are readable |
| T3 flip | Off until $200 |

---

## 23. Immediate next action

1. Create the workspace. Ingest 120 days of BTC 1m candles.
2. Implement swings + clusters. Print levels for 27–28 Aug 2026 BTC 5m.
3. Sit that print next to TradingView. Tune `cluster_atr` until 81.4k, 79.95–80.00, and 78.9–79.0 appear without 40 junk lines.
4. Only then build the situation vector and B1 analog table.
5. Do not open a live order module before step 3.

---

## 24. One-page doctrine

```text
A level is an area, not a wall.
A wick is not a break.
A situation is structure in ATR units, not a price.
Analogs print frequencies, including chop.
Live clicks need a written 5m close.
Flat is a position.
Search never promotes itself.
```

---

*End of specification. Stratum v1.1 — 28 August 2026.*  
*Update this file when a knob or bucket is frozen from walk-forward, not when a single session feels right.*
