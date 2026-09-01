# Phase 1 — The trader model, before any code

What a skilled intraday S&D trader is actually doing, decomposed into claims
that can be observed, and claims that cannot.

## The reasoning chain

A trader does not evaluate a zone. They build a **thesis** and then ask whether
price is confirming or contradicting it. The zone is the *location* where the
thesis becomes actionable — not the reason for the trade.

```
"Where are we?"        regime + HTF location
"What's the story?"    who is in control, structurally
"Where's the fuel?"    liquidity — where are stops parked
"What just happened
 to that fuel?"        swept / broken / untouched
"Where did real
 money show up?"       origin of displacement = the zone
"How are we
 arriving?"            approach quality — desperate or exhausted
"Is it working?"       reaction inside the zone
"Am I wrong yet?"      invalidation
```

## Three categories of claim

**(A) Observable in OHLCV.** Swing structure, displacement magnitude, imbalance
gaps, penetration depth and recovery of prior extremes, approach velocity and
efficiency, volume relative to its own history, position within a range,
volatility regime, time spent at a level, revisit counts.

**(B) Interpretation — a hypothesis, not an observation.** "Institutions left
unfilled orders here." "Smart money hunted retail stops." "This is accumulation."
These are *stories attached to* (A). They may be true; they are not measurable.
The prior phase tested (B) directly by assuming impulse size proxies order size,
and it failed. This phase tests (A) only, and treats (B) as unproven narration.

**(C) Not observable in this data at all.** Order book depth history, iceberg
orders, actual institutional positioning, dark pool flow. Any claim resting on
these is outside what can be validated here and will not be asserted.

## What the previous phase got wrong

It tested the *mechanism* (unfilled orders ⇒ impulse size predicts reaction) and
the *mechanical pattern* (touch ⇒ trade). Both failed. Neither is what a trader
does. A trader would never take a zone touch without asking where price is in
the higher-timeframe range, what happened to the liquidity below, and whether
the approach looks like exhaustion or like conviction.

**The untested claim is the conditional one:** that zone reaction is worthless
on average but meaningfully different inside a specific context. That is a real
statistical proposition — a factor can have zero marginal effect and a large
interaction effect — and it is what this phase tests.

## The honest prior

Nine bugs across this project, all flattering. Roughly 1,900 hypotheses tested,
none surviving. The base rate for "this one is different" is low, and the
interaction search space is where overfitting is easiest. So this phase
pre-specifies its theses, holds out 2025–2026 entirely, ablates every component,
and reports expected false discoveries alongside observed ones.
