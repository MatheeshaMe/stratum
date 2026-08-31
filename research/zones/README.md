# research/zones — supply & demand zone mechanism test

| File | Purpose |
|---|---|
| `zoneengine.py` | Base+impulse zone detection, causal touch tracking, reaction measure |
| `h1_freshness.py` | P1 freshness decay vs random-band and base-no-impulse controls |
| `h2_quality.py` | P2/P3 + all quality axes + the liquidity-sweep compound |
| `h3_economic.py` | Limit-at-proximal-edge economics, 5m/1h/4h, cross-asset |
| `h4_htf.py` | 1h candidate: parameter perturbation, era and asset splits |
| `h5_control.py` | Controls A/B/C — is it the zone or just trend alignment? |
| `h6_fixed.py` | **C9 fix: stop live on the entry bar.** Use this one. |

Report: `../../ZONES_STUDY.md`

## The C9 trap

`h3`–`h5` scan for the stop starting at bar `i+1`. But a limit at the proximal
edge fills **during** bar `i`, and a zone is only ~0.9 ATR deep — on a 1h bar
price can fill you and stop you in the same bar. Those trades were being
credited with the later path.

```
optimistic (stop from i+1):  EV +0.179 R   CI [+0.100,+0.258]   win 31.6%
correct    (stop from i)  :  EV +0.005 R   CI [-0.069,+0.080]   win 27.2%
```

Any backtest with a limit entry and a stop closer than one bar's range must
check the stop on the entry bar. `h6_fixed.py` does; nothing before it does.
