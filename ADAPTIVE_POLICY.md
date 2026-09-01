# Adaptive Trading Intelligence — Policy Research

**1 September 2026 · BTC + 4 alts · 1h · dynamic stop, dynamic target, R:R as an output**

---

## The falsifiable question, and the answer

You were right that I had been converting discretionary reasoning into fixed
strategies. So I built the thing you asked for — a **policy**: market state →
action, with structural invalidation instead of a fixed stop and next-liquidity
instead of a fixed target. Then I reduced the whole brief to one question that
can be wrong:

> **Does a state-conditional policy beat the best single behaviour applied uniformly, out of sample?**

**No.**

| policy | discovery | validation |
|---|---:|---:|
| best constant action | −0.057 | **+0.023** |
| greedy state policy | +0.155 | **−0.064** |
| shrunk state policy | +0.187 | **−0.026** |
| permuted-state control | +0.034 | −0.154 |

The greedy policy beats the permuted control in both windows, so the state space
does carry *some* information. It is not enough to be worth acting on. The best
constant action, after correcting the execution, is **WAIT**.

---

## What was built (deliverables 1–13)

| engine | implementation |
|---|---|
| **Market state** | trend (3) × volatility percentile (3) × range location (3) = 27 states, 18 occupied. Causal, refreshed each bar. |
| **Structure** | confirmed-only ZigZag (θ=3 ATR), HH/HL vs LH/LL, BOS, swing store written at `confirm_bar` |
| **Liquidity** | trailing extremes, equal highs/lows, sweep = penetrate + close back inside, clean break, penetration depth in ATR |
| **Supply/demand** | base+impulse origin, freshness counter, FVG (carried from the prior phase) |
| **Price action** | body/range, wick fraction, close location, approach velocity, directional efficiency, deceleration |
| **Thesis** | 6 canonical actions + WAIT, each with its own trigger, invalidation and objective |
| **Entry** | limit / confirmation / breakout / retest / structural, selected per action |
| **Invalidation** | structural, *not* a fixed ATR multiple — **this is where two bugs lived** |
| **Target** | next opposing liquidity pool, *not* a fixed R |
| **Risk** | R:R computed as `distance to objective / distance to invalidation` — an output |
| **Management** | fixed-objective vs structural trailing, per action type |
| **Adaptation** | greedy and shrunk policies over the state space |
| **Validation** | discovery / validation / holdout, permuted-state control, cross-asset |

---

## The action-value table — the most useful output of this phase

Unconditional expectancy per behaviour on discovery, dynamic stop and target,
full costs:

| action | n | EV R | 95% CI | median R:R | win% |
|---|---:|---:|---|---:|---:|
| L_CONT long continuation | 4,533 | −0.104 | [−0.131, −0.078] | 0.65 | 55.0% |
| S_CONT short continuation | 4,356 | −0.063 | [−0.097, −0.029] | 0.74 | 54.4% |
| L_REV long reversion | 105 | −0.925 | [−1.054, −0.777] | 3.49 | 10.5% |
| S_REV short reversion | 129 | −0.931 | [−1.066, −0.771] | 4.47 | 8.5% |
| L_BRK long breakout | 169 | −0.262 | [−0.372, −0.140] | 0.55 | 46.7% |
| S_BRK short breakout | 207 | −0.057 | [−0.168, +0.052] | 0.60 | 58.5% |
| **WAIT** | — | **0.000** | — | — | — |

Two things worth reading off this table. **Continuation setups have a median R:R
below 1** — the structural stop is far and the next liquidity is near, so the
geometry is against you before probability enters. **Reversion setups have R:R of
3.5–4.5 and win rates under 11%** — the geometry is excellent and the probability
is not.

---

## The deepest finding: the market prices these setups exactly

Because reward here is an *output* (next liquidity) rather than a chosen 2R, it
is possible to ask whether the available asymmetry is compensated:

| window | n | median R:R | breakeven win% | observed win% | gap |
|---|---:|---:|---:|---:|---:|
| discovery | 847 | 5.21 | 16.1% | 16.5% | **+0.4%** |
| validation | 621 | 4.24 | 19.1% | 21.3% | **+2.2%** |

**The available reward-to-risk is almost exactly offset by the hit rate.** A 5.21:1
setup breaks even at 16.1% and delivers 16.5%. That gap — under half a
percentage point — is smaller than the transaction cost, which is why net
expectancy is negative despite the ratio looking attractive.

This is the efficient-market statement written in a trader's own vocabulary. It
also explains every prior phase of this project: whenever the geometry looked
good, the probability was bad by an almost exactly offsetting amount. Chasing
"high R:R setups" is chasing a number the market has already balanced.

---

## Long and short are not symmetric (deliverable 8, 31)

Modelled as separate policies throughout:

- Short continuation (−0.063) is materially better than long continuation (−0.104)
- Short breakout (−0.057) is much better than long breakout (−0.262)
- Reversion is equally bad both ways once invalidation is correct

Short-side behaviours are consistently less bad. None is positive. The asymmetry
is real but it is an asymmetry between two losing behaviours.

---

## Two more bugs, both flattering. Eleven and twelve.

Before the fixes this phase reported: reversion at **+0.433 R with a 76% win
rate**, holdout **+0.451 R**, and all eight cross-asset cells significant. All of
it was execution error.

### C11 — structural stop on the wrong side of entry

A sweep bar's new extreme is not yet a confirmed pivot, so `structural_stop()`
returned an *older* level, frequently on the wrong side of the entry. With
`risk = abs(entry − stop)` the trade was never rejected, and on the entry bar the
stop test fired immediately, evaluating to **+1.0 R**.

**Inverted in 70.1% of shorts and 59.9% of longs. Every one an instant fake win.**

| | with C11 | corrected |
|---|---:|---:|
| S_REV discovery | +0.433 R, 76.2% win | **−0.931 R, 8.5% win** |
| L_REV discovery | +0.215 R, 65.7% win | **−0.925 R, 10.5% win** |
| best constant action | S_REV +0.433 | **WAIT 0.000** |

### C12 — trailing stop jumping past price into locked profit

Same root cause, different surface. The trail took `min(st, level)` without
checking the level was still beyond current price. After a sweep the confirmed
swing is stale and already on the profitable side, so the stop moved there on the
first bar and that same bar "hit" it.

**63.2% of trades (552/874), median fake gain +2.56 R, max +44.1 R.**

| | with C12 | corrected |
|---|---:|---:|
| discovery, trailing | +1.761 R, PF 5.32 | **−0.031 R, PF 0.96** |
| validation, trailing | +1.089 R, PF 3.31 | **−0.215 R, PF 0.75** |

### Scope check on the already-delivered reports

I audited whether C12 contaminates `STRUCTURE_STUDY.md` and `TRADER_SYSTEM.md`,
which both use a trailing structural exit.

**It does not. 0 of 651 break-of-structure setups are affected.** A BOS entry
means price has just broken the swing, so the opposing swing is genuinely behind
price and the stale-level condition cannot arise. Those results stand as
published.

**Running total: twelve errors found in my own research code. All twelve made
results look better.** C11 and C12 are the same root cause — using a *confirmed*
structural level at a moment when the relevant extreme is *not yet confirmed* —
surfacing in two different places.

---

## What "adaptive" actually bought

Honestly assessed:

**It helped.** Dynamic invalidation and dynamic targets are the right formulation
and they produced the efficiency identity above, which a fixed-2R framework
cannot even express. R:R as an output is a genuine methodological improvement and
I will keep it.

**It did not create edge.** State conditioning underperformed its own best
constant action out of sample. The shrunk policy — which deviates only where a
state's advantage clears its confidence interval — found **zero** such states
before C11 and behaved no better after.

**And it created new ways to be wrong.** Both bugs this phase came from the
dynamic machinery: structural levels that are correct in concept but stale at the
moment they are read. A fixed 1-ATR stop cannot be on the wrong side of the
entry. That is not an argument for fixed stops; it is a warning that adaptive
logic needs invariant checks that static logic does not.

---

## Verdict: **DO NOT BUILD as an adaptive policy**

The state-conditional policy does not beat WAIT. Every canonical behaviour is
negative. The reversion setups that looked spectacular were two execution bugs.

What survives from the whole project remains what `TRADER_SYSTEM.md` reported —
zone + HTF alignment + trailing structural exit, +0.314 R, which failed its own
pre-registered holdout and is a paper-trading candidate, not a funded one.

### What I would keep from this phase

1. **R:R as an output.** Never again specify a target as a fixed multiple.
2. **The action-value table.** Continuation R:R < 1, reversion R:R > 3 with a
   sub-11% hit rate — that shapes what is worth even looking at.
3. **The efficiency identity.** Before testing any setup, check whether its
   available R:R times its plausible hit rate clears cost. It usually will not,
   and that check is free.
4. **Invariant assertions.** Every trade must assert: stop strictly beyond entry
   in the losing direction; target strictly beyond entry in the winning
   direction; trailing stop never moved past the current bar's extreme. These
   three assertions would have caught C9, C10, C11 and C12.

### What I would not do

Add more state features. The permuted-state control shows the state space
already carries more signal than the greedy policy can safely exploit; more
dimensions will widen the gap between in-sample and out-of-sample, not close it.

---

*Code: `research/policy/`. Pre-specification: `research/policy/PRESPEC.md`.
Corrections: `research/CORRECTIONS.md` §C11, §C12. TradingView implementation
unchanged: `pine/stratum_sd.pine` — the policy findings give it nothing to add.*
