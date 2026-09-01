# research/policy — adaptive policy research

| File | Purpose |
|---|---|
| `PRESPEC.md` | Splits, action set, state space and pass criteria, **written before scoring** |
| `engine.py` | Market state, dynamic structural stop, dynamic next-liquidity target, trade walk |
| `run_policy.py` | Action-value table, greedy/shrunk policies, permuted-state control |
| `run_rev.py` | The reversion actions: entry timing, holdout, cross-asset |
| `run_sweepstop.py` | Second (post-hoc, declared) stop definition: the swept extreme |

Report: `../../ADAPTIVE_POLICY.md`

## The three invariants every trade must assert

C9, C10, C11 and C12 were all execution errors, all flattering. Four assertions
catch every one of them:

```python
assert (side > 0 and stop < entry) or (side < 0 and stop > entry)   # C11
assert (side > 0 and tgt  > entry) or (side < 0 and tgt  < entry)   # C11
# entry bar may trigger the STOP but never the TARGET                 C9/C10
# trailing stop may never move past the current bar's extreme          C12
```

## Why adaptive logic needs them and static logic does not

A fixed 1-ATR stop cannot land on the wrong side of the entry. A *structural*
stop can, whenever the relevant extreme is not yet a confirmed pivot — which is
exactly the situation a liquidity sweep creates. Both C11 and C12 are the same
root cause surfacing in two places: reading a confirmed level at a moment when
the level that matters is unconfirmed.
