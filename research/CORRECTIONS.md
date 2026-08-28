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
