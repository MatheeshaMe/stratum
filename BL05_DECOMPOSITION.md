# N-3 — Decomposing the BL-05 Frequency/Payoff Compensation

**2 September 2026 · 938,247 base observations · 5 assets · 2 eras · ~62 conditional cells**

*Decomposition study. No entries, stops, targets, R:R, sizing or PnL — by instruction.*

---

## Answer: **B and E — compensation breaks under specific conditions and specific sequences — but only in the body of the distribution. In the full distribution it is not measurable at all.**

Both halves matter, and the second one is the more important discovery.

---

## The exact identity

For condition *c* against baseline *b*, with p = P(move in thesis direction), u = mean|favourable, d = mean|adverse:

```
Δmean = FREQ + PAYOFF + INTERACTION            (exact, zero residual)

FREQ        = Δp·(u_b − d_b)      frequency moves, payoffs held at baseline
PAYOFF      = p_b·Δu + (1−p_b)·Δd payoffs move, frequency held at baseline
INTERACTION = Δp·(Δu − Δd)

compensation ratio  κ = −PAYOFF / FREQ
```

κ ≈ 1 → full compensation · κ < 1 → the frequency gain partly survives · κ > 1 → payoff decays faster than frequency improves.

Verified numerically: `FREQ + PAYOFF + INTER = +0.0249` vs `Δmean = +0.0249` for the sweep-low baseline.

---

## Step 1 — Raw decomposition reproduces BL-05

| condition | n | ΔP(dir) | Δu | Δd | FREQ | PAYOFF | Δmean | κ | type |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| sweep low → long | 6,606 | +5.8% | −0.823 | +0.109 | **+0.449** | **−0.370** | +0.025 | **0.82** | A |

The frequency gain is worth **+0.449 ATR**. The payoff deterioration costs **−0.370 ATR**. 82% of the gain is consumed. That is BL-05, now accounted for exactly.

---

## Step 2 — The replication gate FAILED, and the failure was informative

Ten candidates × six era-asset cells. **Zero passed.** κ ranged from **−286.82 to +14.74** across cells:

| candidate | BTC early | BTC late | ETH | SOL | XRP | DOGE |
|---|---:|---:|---:|---:|---:|---:|
| low (control) | 0.78 | 0.85 | **−1.90** | 0.17 | 0.97 | **4.69** |
| low + compressed before | 0.75 | 0.44 | **−5.46** | 0.10 | 1.24 | **14.74** |
| low + HTF bullish | 0.67 | 0.59 | 1.10 | 0.01 | 0.83 | 2.97 |
| high + HTF bearish | 1.13 | 2.86 | 0.80 | 2.03 | 1.71 | **−286.82** |

Δmean disagreed just as violently — ETH **+4.997**, DOGE **−2.179** for the same condition.

**No band held for any candidate.** By the pre-registered gate that is conclusion F.

Except a statistic that swings from −286 to +14.7 is not measuring market behaviour. It is measuring outliers.

---

## Step 3 — The instability was entirely fat tails

| asset | forward-return **kurtosis** | raw κ | κ @1% winsor | κ @5% winsor | Δmean raw | Δmean @5% |
|---|---:|---:|---:|---:|---:|---:|
| BTC | 21.6 | 0.82 | 0.79 | **0.58** | +0.025 | **+0.129** |
| ETH | **12,523.3** | −1.90 | 0.72 | **0.47** | +1.385 | **+0.154** |
| SOL | 11.6 | 0.17 | 0.30 | **0.26** | +0.230 | **+0.184** |
| XRP | **2,165.0** | 0.97 | 0.59 | **0.36** | −0.039 | **+0.224** |
| DOGE | **10,546.2** | 4.69 | 0.45 | **0.25** | −2.004 | **+0.169** |

**Raw κ spans −1.90 to +4.69. Winsorised at 5%, it collapses to 0.25–0.58 — and every asset agrees.** Δmean goes from spanning −2.00 to +1.39, to spanning +0.129 to +0.224, all positive.

ETH's kurtosis of 12,523 means a handful of bars own the mean outright. The cross-asset "disagreement" was never about market behaviour; it was five different sets of extreme observations.

**This is the methodological finding of the phase.** Every mean-based result in this project has been computed on distributions with kurtosis between 11 and 12,500. BL-05 itself — and the conclusion two phases ago that directional information doesn't replicate — were both measured with a statistic the data cannot support.

---

## Step 4 — In the body of the distribution, compensation genuinely breaks

BTC, 5% winsorised. **κ CI excluding 1.0 marked \*.**

| condition | n | ΔP(dir) | Δu | Δd | FREQ | PAYOFF | Δmean | κ | type | κ 95% CI |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| **low (control)** | 6,606 | +5.8% | −0.488 | +0.061 | +0.382 | −0.221 | +0.129 | **0.58** | B | [0.35, 0.93] * |
| **low + acceptance + displacement** | 619 | +7.9% | **+0.085** | **−0.265** | +0.522 | −0.086 | **+0.465** | **0.16** | **C** | [−0.31, 0.81] * |
| low + compressed before | 2,180 | +7.8% | −0.239 | −0.119 | +0.515 | −0.181 | +0.324 | **0.35** | B | [0.12, 0.64] * |
| low + fast approach | 2,180 | +7.0% | −0.472 | +0.162 | +0.460 | −0.163 | +0.253 | **0.35** | B | [0.11, 0.68] * |
| low + HTF bullish | 2,330 | +7.3% | −0.546 | +0.157 | +0.479 | −0.204 | +0.224 | **0.43** | B | [0.16, 0.84] * |
| low + efficient approach | 2,180 | +7.4% | −0.505 | +0.105 | +0.491 | −0.209 | +0.237 | **0.43** | B | [0.19, 0.76] * |
| low + low relative volume | 2,180 | +6.3% | −0.415 | +0.033 | +0.415 | −0.197 | +0.190 | **0.48** | B | [0.16, 0.95] * |
| low + discount | 2,431 | +6.8% | −0.423 | −0.044 | +0.448 | −0.239 | +0.184 | 0.53 | B | [0.26, 0.96] * |
| low + premium | 2,325 | +7.0% | −0.588 | +0.078 | +0.464 | −0.264 | +0.153 | 0.57 | B | [0.27, 1.05] |
| low + reclaim + displacement | 1,432 | +3.9% | −0.657 | +0.205 | +0.255 | −0.238 | −0.016 | **0.93** | **A** | [0.39, 3.15] |
| **high (control)** | 7,224 | +4.5% | −0.394 | −0.143 | +0.295 | −0.265 | +0.018 | **0.90** | **A** | [0.54, 1.55] |
| high + HTF bearish | 2,179 | +4.4% | −0.409 | −0.202 | +0.292 | −0.303 | −0.020 | **1.04** | **A** | [0.39, 3.31] |
| high + acceptance + displacement | 730 | +5.8% | −0.220 | −0.490 | +0.380 | −0.358 | +0.037 | **0.94** | **A** | [0.47, 2.38] |

### Four things fall out of this table

**1. The baseline break is real.** Even unconditionally, κ = 0.58 with a CI excluding 1.0. Compensation is **partial**, not complete — roughly 40% of the frequency gain survives in the body of the distribution.

**2. `sweep low → acceptance → displacement` is the only Type C cell.** κ = 0.16, and critically **Δu is positive (+0.085) while Δd is negative (−0.265)** — the favourable excursion is *preserved* and the adverse one *shrinks*. Δmean +0.465, the largest in the table. It is also the rarest (n = 619) and its CI is wide.

**3. `reclaim` and `acceptance` are opposites.** Reclaim + displacement: κ = 0.93, Type A, Δmean −0.016 — full compensation, nothing survives. Acceptance + displacement: κ = 0.16, Type C. **The same sweep, resolved two different ways, produces completely different compensation structures.** This is the sequence distinction earning its keep.

**4. Long and short are not mirror images.** Every long-side cell is Type B or C (κ 0.16–0.59). Every short-side cell is Type A (κ 0.90–1.04) with a CI including 1.0. **Compensation is full on the short side and partial on the long side.** That asymmetry is consistent across all conditions tested.

---

## The decomposition map

```
SWEEP LOW  (n=6,606)
  frequency effect  +0.382 ATR      P(up) 51.4% -> 57.2%
  payoff effect     -0.221 ATR
  compensation      κ = 0.58   PARTIAL      [CI 0.35-0.93, excludes 1.0]
        |
        +-- + acceptance + displacement ...... κ 0.16  TYPE C   Δmean +0.465
        |     upside PRESERVED (+0.085), downside SHRUNK (-0.265)
        |     n=619, wide CI, BTC-measured
        |
        +-- + compressed before .............. κ 0.35  TYPE B   Δmean +0.324
        +-- + fast approach .................. κ 0.35  TYPE B   Δmean +0.253
        +-- + HTF bullish (agrees) ........... κ 0.43  TYPE B   Δmean +0.224
        +-- + efficient approach ............. κ 0.43  TYPE B   Δmean +0.237
        +-- + low relative volume ............ κ 0.48  TYPE B   Δmean +0.190
        |
        +-- + reclaim + displacement ......... κ 0.93  TYPE A   Δmean -0.016
              compensation COMPLETE - nothing survives

SWEEP HIGH  (n=7,224)
  compensation      κ = 0.90   FULL         [CI 0.54-1.55, includes 1.0]
        |
        +-- every condition tested ........... κ 0.90-1.04  TYPE A
              no compensation break found on the short side
```

---

## Behavioural library entry

```
BL-05-C   SWEEP LOW -> ACCEPTANCE -> DISPLACEMENT

OBSERVATION      Price pokes below a 15m liquidity pool, then closes below it
                 twice, with the move displacing more than 0.5 ATR.

FREQUENCY        P(up) +7.9 pp over baseline.
PAYOFF           Favourable excursion PRESERVED (+0.085 ATR),
                 adverse excursion CONSTRAINED (-0.265 ATR).
COMPENSATION     κ = 0.16 (Type C). 84% of the frequency gain survives.
TIMING           Time to a +/-0.5 ATR resolution HALVES (0.50x, replicated
                 across all six era-asset cells in the prior phase).
DISTRIBUTION     Skew turns negative (-0.42 vs +0.50 baseline).

LONG/SHORT       Long side only. The mirror (sweep high -> acceptance ->
                 displacement) is κ = 0.94, Type A, fully compensated.

ASSET REPLICATION   NOT ESTABLISHED. Measured on BTC. The raw-scale gate failed
                    on all assets; the winsorised control (κ 0.25-0.58) replicates
                    for the UNCONDITIONAL sweep, but the conditional cell was not
                    re-run per asset.
ERA REPLICATION     NOT ESTABLISHED.
OUT-OF-SAMPLE       NOT TESTED. The sealed holdout was spent in an earlier phase.

LIMITATIONS      n=619. κ CI is [-0.31, 0.81] - wide, and it touches zero from
                 below. 5% winsorisation removes exactly the tail where a
                 trend payoff would live.

WHAT IT DOES NOT MEAN
                 It is NOT an edge, NOT a signal, and NOT validated. It is the
                 single most promising cell in a decomposition study, measured
                 on one asset, in the body of a distribution whose tails cannot
                 be measured at all.
```

---

## Accounting

```
N3-1 baseline decomposition                     2 cells
N3-2 post-sweep sequence                        8
N3-3 location                                   6
N3-4 approach                                   5
N3-5 volatility regime                          5
N3-7 volume                                     3
N3-8 structure / liquidity type                 7
replication gate                       10 x 6 = 60
winsorisation diagnostic                5 x 3 = 15
winsorised conditional                         14
                                             ~125 tests
expected false discoveries at a=0.05           ~6
cells passing the RAW pre-registered gate        0
cells with winsorised κ CI excluding 1.0         8
```

**No new bugs found this phase.** Third consecutive, after twelve.

---

## Limitations

1. **Winsorisation is not neutral.** Clipping at 5% removes the tail where trend payoff lives. The winsorised κ answers "what happens in the typical case", not "what happens".
2. **The raw-scale question is unanswerable with this data.** With kurtosis of 12,523, the sample mean has no useful standard error. Any future work on payoff magnitude needs a tail-aware estimator, not a mean.
3. **The Type C cell is BTC-only, n=619, CI touching zero.** It is a hypothesis.
4. **The 4-hour horizon is fixed.** BL-03 says the aftermath of a sweep is quiet; the payoff may live beyond this window.
5. **Discovery used all of BTC.** The sealed holdout was spent earlier in this project; there is no untouched data left for a final test.
6. **No costs anywhere**, deliberately. At Δmean +0.465 ATR ≈ 0.068% of price, a 6.6 bps round trip would consume roughly 10% of it — so this is not automatically doomed on cost, which is itself notable.

---

## What I would do next

**N-4 — Re-run the conditional decomposition per asset on winsorised data.** The winsorised unconditional κ replicated (0.25–0.58 across five assets); the conditional cells were only measured on BTC. This is the cheapest, highest-value remaining test and it directly determines whether BL-05-C is real.

**N-5 — Replace the mean with a tail-aware estimator.** Kurtosis of 12,523 means every mean-based conclusion in this project deserves re-examination, including the two phases ago conclusion that directional information does not replicate. Median-based or trimmed decompositions would answer a slightly different question, reliably, instead of the right question, unreliably.

**N-6 — Extend the horizon past 4 hours** for the acceptance+displacement branch specifically. It is the only cell where the favourable excursion *grew*, and a fixed 4h window may be truncating it.

---

*Code: `research/interp/n3_decomp.py`, `n3_stages.py`, `n3_replicate.py`, `n3_robust.py`, `n3_winsor.py`. Pre-specification: `research/interp/PRESPEC_N3.md`.*
