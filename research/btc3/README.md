# research/btc3 — Bitcoin +3% event study

| File | Produces |
|---|---|
| `events.py` | Event detection (C2C / L2H / O2H), dedupe rules, indicators |
| `step1_detect.py` | Event counts under every definition; overlap collapse |
| `step2_dataset.py` | The structured event dataset (before / during / after) |
| `step3_after.py` | Forward-return distributions vs unconditional baseline |
| `step4_before.py` | Precursor profile with Cohen *d* vs 20k random points |
| `step5_conditional.py` | P(+3% \| state), train/test — **superseded by step6b** |
| `step6_symmetry.py` | Up-vs-down test — **contains the C8 bug, kept for the record** |
| `step6b_clean.py` | C8-corrected forward-only label. **Use this one.** |
| `step7_path.py` | Normalised event timeline, archetypes, segmentation |
| `step8_sig.py` | Bootstrap + Wilson CIs on the notable segments |

Report: `../../BTC_PLUS3PCT_STUDY.md`

## Reproduce

```bash
python3 scripts/fetch_spot.py            # free, no key, skips the sealed window
python3 research/btc3/step1_detect.py
python3 research/btc3/step2_dataset.py
python3 research/btc3/step3_after.py
python3 research/btc3/step4_before.py
python3 research/btc3/step6b_clean.py
python3 research/btc3/step7_path.py
python3 research/btc3/step8_sig.py
```

## The C8 trap

`step6_symmetry.py` is deliberately kept even though it is wrong. It labelled
the future event with a *trailing*-window condition evaluated forward, so the
label shared up to 59 of 60 minutes with the conditioning window. It produced
`ret_1h >= p95` → P(+3%)=40.0% vs P(-3%)=7.4%, a 5.38x directional asymmetry.

`step6b_clean.py` anchors the label at the decision time:

```
UP:   max(High[i+1..i+60]) / Close[i] - 1 >= +3%
DOWN: min(Low [i+1..i+60]) / Close[i] - 1 <= -3%
```

Same condition, same data: the ratio falls to **0.97x**. Diff the two files
before writing any new forward label.
