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
