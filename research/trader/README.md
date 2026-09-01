# research/trader — reconstructing the discretionary S&D trader

| File | Phase | Purpose |
|---|---|---|
| `PHASE1_TRADER_MODEL.md` | 1 | The reasoning chain; what is observable vs interpreted vs unmeasurable |
| `PRESPEC.md` | — | Data splits and theses, **written before scoring** |
| `features.py` | 3 | Six-level contextual feature engine, all causal |
| `setups.py` | 4–6 | Zone detection, 5 entry models, 5 management models |
| `run_discovery.py` | 4–6 | Discovery scoring (2017-08 .. 2021-12) |
| `run_ablation.py` | 7 | **The ablation ladder** + validation |
| `run_held.py` | 8 | Distribution audit, held-out test, cross-asset |
| `run_trail_control.py` | 8 | Does the zone beat an aligned random entry with the same exit? |
| `run_funding.py` | 8 | Funding on multi-day holds |

Report: `../../TRADER_SYSTEM.md` · Pine: `../../pine/stratum_sd.pine`

## The C10 trap

`manage()` originally checked stop AND target on the entry bar. A limit fills
partway through that bar and OHLC gives no intrabar path, so the target must not
be reachable on bar `i` — only the stop.

```
with C10 bug : T0/A/fix2 discovery +0.165 R ; held-out 2 of 13 cells significant
corrected    : T0/A/fix2 discovery -0.133 R ; held-out 0 of  9 cells significant
```

Every fixed-target result in this phase was that bug. It surfaced only because
`ZONES_STUDY` and this engine disagreed on the same idea by 0.36 R — diffing the
two execution loops found it. **When two of your own phases disagree, diff the
execution loop before believing either.**
