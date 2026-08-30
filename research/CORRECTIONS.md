# Corrections log

Errors found in Stratum's own research code, with the fix and the impact.
Recorded per the research mission's rule: never silently change a result.

---

## C1 — Label/payoff mismatch (found 2026-08-28, in v3 §0 work)

**Bug.** `triple_barrier()` placed both barriers at ±k·ATR (symmetric) while the
EV table paid 1.5:1. A symmetric label scored against an asymmetric payoff.

**Impact.** Base rate for "target before stop" appeared as **44%** when the true
value for that payoff is **28%**. Made a dead process look tradeable.

**Fix.** `triple_barrier(..., rr=)`; target barrier sits at `rr × stop`.
Verified by P0/T3: P(win|resolved) now matches random-walk theory 1/(1+rr) to
within 0.8pp at rr = 1.0, 1.5, 2.0.

---

## C2 — Unresolved trades charged as full stop-outs (found 2026-08-28, P2)

**Bug.** `p2_surface.py` computed `netEV = p·rr − (1−p)·1 − cost_R`, where `p` was
P(target first) and *everything else* — including trades still open at the
vertical barrier — was charged −1R.

**How it surfaced.** Cells reported `lift > hurdle` (a signal that should imply
positive EV) while simultaneously reporting `netEV = −0.12 to −0.67R`. Those two
statements are incompatible, which is what exposed the bug.

**Two separate errors compounded:**

1. A trade unresolved at the vertical barrier is closed at market, realising a
   *markout* somewhere between −1R and +rr. Charging it −1R is not conservative,
   it is simply wrong, and the error grows with barrier width because wider
   barriers resolve less often.
2. The `hurdle = cost_R/(1+rr)` derivation assumed the random-walk base rate
   `1/(1+rr)`, which only holds when the vertical barrier never binds. At
   k=14 ATR the observed base rate was 28.1% against a theoretical 40% — the
   vertical barrier was binding roughly 30% of the time, so the hurdle was
   being compared against the wrong null.

**Fix.** Compute realised R per trade directly:

```
R = +rr                      if target hit first
R = -1                       if stop hit first
R = (markout at vertical)/stop_distance   otherwise
netEV = mean(R) - cost_R
```

No theoretical base rate enters the EV calculation at all. The hurdle framing
from P1 remains valid **only** for configurations where the vertical barrier is
negligible (< 5% unresolved), and every table now reports the unresolved
fraction so that condition is visible rather than assumed.

**Impact.** All P2 cells previously flagged `<<< CLEARS HURDLE` are void and
were re-run. See `p2_surface.py` output after the fix.

---

## C3 — Block bootstrap too short for slow conditioning variables (found 2026-08-28, R-1)

**Bug.** `r1_events.py` set the bootstrap block length to the *forward horizon*
(max 36 bars = 3h). But the conditioning variables are far more persistent than
that: `funding_z` updates every 8h and mean-reverts over days;
`toptrader_sum_ls_z` is a slow positioning series. An extreme-quantile event on
such a variable does not produce 18,821 independent observations — it produces
a few dozen multi-day *episodes*.

**Impact.** Confidence intervals were far too narrow. The "20 significant cells
out of 65, vs 3.2 expected" headline is not trustworthy as stated.

**Fix.** Block length must reflect the persistence of the *conditioning*
variable, not the forward horizon. Now estimated per-feature from the integrated
autocorrelation time of the event indicator, floored at one day (288 bars).
Also report the number of distinct episodes alongside n.

---

## C4 — Missing control in the magnitude x direction split (found 2026-08-28, R-1)

**Bug.** Q5 split high-magnitude states by the *combined* (OHLCV+micro)
direction model and reported a 7.5pp spread in P(up) between top and bottom
quintiles. No OHLCV-only control was run on the same split.

**Why it matters.** Q2 on the same data showed the combined model has a *lower*
directional AUC than OHLCV alone (−0.0027 to −0.0082 at every magnitude
tercile). A spread produced by a model that is worse than the OHLCV baseline
cannot be evidence that microstructure adds anything — the same or a larger
spread is likely available from OHLCV alone.

**Fix.** Q5 now runs the identical quintile split three times — OHLCV-only,
micro-only, combined — so the incremental contribution is visible rather than
assumed.

---

## C5 — Blended exit cost mislabelled as "maker out" (found 2026-08-28, R-3)

**Bug.** `r3_validate.py` labelled a scenario "TAKER in / maker out (realistic)"
and charged a single maker fee on every exit. But only the **target** exit can
rest as a passive limit. The stop exit and the horizon (unresolved) exit are
both takers — and in this candidate they are the **majority** of outcomes:

```
P(target first)  ~24%   -> maker exit
P(stop first)    ~25%   -> taker exit
P(unresolved)    ~51%   -> taker exit at the horizon
```

So the exit is maker only ~24% of the time. The correct blended exit cost is
`0.24 x 1.5 + 0.76 x 5.13 = 4.26 bps`, not 1.5 bps.

**Impact.** The scenario labelled "realistic" understated round-trip cost by
~2.8 bps and reported +0.0130% EV. Recomputed properly the candidate is
**negative**. The label, not the arithmetic, was doing the work.

**Fix.** Exit cost is now computed from the realised outcome mix per cell rather
than assumed, and the scenario is renamed to what it actually is.

---

## C6 — Look-ahead in the tail threshold (found 2026-08-28, R-3)

**Bug.** The momentum candidate selects entries in the top/bottom `q` tail of the
30-minute return. The threshold was computed as `np.nanquantile(r6, q)` over the
**entire sample** — so the decision to trade at time *t* used the distribution of
returns from the whole 2023–2026 period, including the future.

**Why it matters here specifically.** The candidate's EV rises monotonically as
the tail gets more extreme (+0.013% at 5%, +0.157% at 0.2%). A full-sample
threshold systematically picks the *ex-post* most extreme moves. In a period
where volatility trends, this silently front-runs regime changes.

**Fix.** Threshold is now a trailing empirical quantile over the previous 30
days (8,640 5m bars), recomputed at each bar and using only past data. Trades
before the window fills are dropped.

**Impact.** Re-run below. Any result quoted before this fix is void.

---

## C7 — Four-minute look-ahead on every R-3 conditional entry (found 2026-08-28)

**Bug.** `situations.agg()` returns `i1m` = the index of the **first** 1-minute
bar of each 5-minute bar. Every R-3 conditional experiment set
`entry = b['i1m'][k]` and then filled at `O[entry+1]`.

But the signal (`ret6`, the 30-minute return) is computed from the **close** of
5m bar `k`, which is 1-minute index `i1m[k+1]-1`. So the fill was taken at the
*second minute of the very bar whose close produced the signal* —
**four minutes before the signal could exist.**

**How it surfaced.** The sequential portfolio simulation returned a
3,153,883× equity multiple and +6,430% CAGR. That is not a discovery; nothing
real compounds like that. Working backwards from an impossible number found the
index error.

**Why it was so damaging here.** The look-ahead scales with the size of the
signal bar. The candidate selects the most extreme 30-minute moves, so it was
systematically buying 4 minutes into the largest up-bars in the sample. That is
precisely why EV rose monotonically as the tail got more extreme — the
"selectivity effect" was the look-ahead getting larger, not the edge getting
stronger.

**Fix.** `entry = i1m[k+1] - 1` (the last 1-minute bar of the signal bar), with
the fill at `O[i1m[k+1]]` — the first price available after the signal exists.

**Impact.** VOID: every R-3 conditional result — `r3_states.py`,
`r3_validate.py`, `r3_final.py`, `r3_execution.py`, `r3_causal.py`,
`r3_stress.py`, `r3_portfolio.py`. The unconditional surface in
`r3_surface.py` is unaffected (it indexes the 1m grid directly and uses no 5m
signal). Re-run below.

---

## C8 — Overlap contamination in the +3% forward label (found 2026-08-30, BTC+3% study)

**Bug.** Step 5/6 labelled the future event as *"does `close[t]/close[t-60] - 1`
cross +3% at any t in the next 60 minutes?"* — a rolling **trailing-window**
condition evaluated forward.

At `t = i+1` that window is `[i-59, i+1]`, which shares **59 of 60 minutes with
the conditioning window** used to build the features. So a state that already
contains a large trailing rise (`ret_1h >= p95`, `rsi >= p95`) is nearly
guaranteed to satisfy the "future" condition with almost no further price
movement. The label was largely a restatement of the feature.

**Impact.** Void: the apparent directional asymmetries in step 6
(`ret_1h >= p95` → P(+3%)=40.0% vs P(−3%)=7.4%; `rsi >= p95` → 9.8x ratio).
These measured overlap, not prediction.

**Fix.** Forward-only, non-overlapping definition anchored at the decision time:

```
UP   event:  max(High[i+1 .. i+60]) / Close[i] - 1 >=  +3%
DOWN event:  min(Low [i+1 .. i+60]) / Close[i] - 1 <=  -3%
```

Nothing before `i` enters the label. Re-run below.
