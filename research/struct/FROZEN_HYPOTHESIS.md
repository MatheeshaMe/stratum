# Frozen hypothesis for the sealed 2020–2022 test

**Frozen 2026-08-30, before any 2020–2022 data was loaded into a structural test.**
No parameter below may be changed after seeing the result.

## Instrument and data
- Binance **spot** BTCUSDT, 1-minute klines, aggregated to 5-minute bars
- Window: **2020-01-01 → 2022-12-31** (the sealed holdout)

## Structure engine (unchanged from `zigzag.py`)
- ATR(14) Wilder on 5m bars
- ZigZag pivot threshold **θ = 3.0 × ATR**
- Pivots are **confirmed-only**: a pivot is written into state at its
  `confirm_bar`, never its `pivot_bar`
- `trend = +1` iff last swing high > previous swing high **and** last swing low >
  previous swing low; `−1` for the mirror; `0` otherwise
- `efficiency` = |net move over 60 bars| / total path length over 60 bars

## Entry
- **Primary**: `trend == +1` **and** close breaks the last confirmed swing high
  (rising edge) → LONG. Mirror for SHORT.
- **Filter**: `efficiency > 0.35`
- **Fill**: open of the next 5m bar

## Risk and exit
- Initial stop: last confirmed swing low − 0.25 × ATR (mirror for shorts)
- Reject if risk < 0.15% or > 8% of price
- Exit: **trailing structural stop**, ratcheted to each newly confirmed swing
  low − 0.25 × ATR. **No profit target.** Max hold 2000 bars.

## Costs
- Taker in / taker out: (4.5 + 0.63) × 2 = **10.26 bps round trip**

## Pre-registered pass criteria
The hypothesis PASSES only if **all** hold on 2020–2022:
1. EV per trade > 0 with a 95% bootstrap CI **excluding zero**
2. n ≥ 150 trades
3. Profit factor > 1.0
4. Sign holds for **both** LONG and SHORT sub-samples

Anything less is a FAIL and is reported as such.

## Prior (discovery) result being tested
BTC 2017–2019 + 2023–2026: n = 446, win 36.8%, **EV +0.063 R**,
CI [−0.073, +0.220], PF 1.15 — already not significant, and negative in the
most recent era (2025–26: −0.081). This test asks whether the strongest
trending regimes in crypto history rescue it.
