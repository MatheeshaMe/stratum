# Pre-specification — adaptive policy research

Written before any action-value was scored.

## The falsifiable question

> Does a policy that selects behaviour **conditional on market state** outperform
> the single best behaviour applied uniformly, **out of sample**?

This is the whole brief reduced to something that can be wrong. If a
state-conditional policy cannot beat its own best constant action on held-out
data, "adaptive" is decoration.

## Known trap, handled explicitly

Choosing argmax-action-per-state on discovery is guaranteed to look good
in-sample: with 6 actions per state I am taking the maximum of 6 noisy
estimates. Three defences:

1. **The policy is frozen on DISCOVERY and never re-fit.**
2. **A SHRUNK policy** is also built: deviate from the global best action only
   where a state's advantage clears its own confidence interval. If the greedy
   policy beats shrunk out-of-sample, the states carry real information; if
   shrunk wins, greedy was fitting noise.
3. **A permuted-state control**: identical machinery with state labels shuffled.
   Anything the greedy policy earns above this is selection bias, not adaptation.

## Splits

| set | window | use |
|---|---|---|
| DISCOVERY | 2017-08 → 2021-12 | state definition, action-value table, policy |
| VALIDATION | 2022-01 → 2024-12 | confirm or kill |
| **HOLDOUT** | **2025-01 → 2026-07** | **one look, no changes after** |
| cross-asset | ETH SOL XRP DOGE | transfer without refit |

## Action set (each with DYNAMIC stop and DYNAMIC target)

| id | behaviour |
|---|---|
| L_CONT | long continuation — pullback in an uptrend |
| S_CONT | short continuation — pullback in a downtrend |
| L_REV | long mean-reversion — downside liquidity swept at a discount |
| S_REV | short mean-reversion — upside liquidity swept at a premium |
| L_BRK | long breakout — acceptance above structure |
| S_BRK | short breakout — acceptance below structure |
| WAIT | no trade, expectancy exactly 0 |

**Stop** = structural invalidation (last opposing confirmed swing ± 0.25 ATR),
not a fixed multiple.
**Target** = next opposing liquidity (prior swing extreme / range boundary),
not a fixed R. R:R is therefore an *output*.

## State space (interpretable, causal)

`trend` (up/flat/down) × `volatility` (low/mid/high) × `location`
(discount/mid/premium) = 27 states. A KMeans clustering on the same features is
run alongside as a check that the rule-based discretisation is not the binding
constraint.

## Pass criteria
1. Greedy policy > best constant action on VALIDATION
2. Greedy policy > permuted-state control on VALIDATION
3. Positive with CI excluding zero on HOLDOUT
4. Positive on ≥ 3 of 5 assets
