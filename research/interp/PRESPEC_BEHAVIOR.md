# Pre-specification — conditional behaviour discovery

Written before any conditional statistic was computed. §22 requires replication
criteria be fixed in advance.

## What counts as a REPLICATED relationship

A relationship enters the behavioural library only if **all** hold:

1. **Effect size.** The conditional statistic differs from its unconditional
   baseline by a margin that is economically legible, stated per class:
   - DIRECTION: |Δ P(up)| ≥ 2.0 pp, or |Δ P(+1ATR before −1ATR)| ≥ 2.0 pp
   - MAGNITUDE: ratio to baseline outside [0.92, 1.08]
   - TIMING: median bars-to-threshold ratio outside [0.85, 1.15]
   - PATH: variance ratio outside [0.90, 1.10] or |Δ skew| ≥ 0.15
2. **Sample.** n ≥ 500 conditional observations in each replication cell.
3. **Era replication.** Same sign / same side of baseline in BTC pre-2022 and
   BTC 2022-onwards.
4. **Asset replication.** Same sign / same side in ≥ 3 of 4 alts (ETH, SOL, XRP, DOGE).
5. **Uncertainty.** Block-bootstrap 95% CI excludes the baseline in the pooled
   sample, block length = the forward horizon.

Anything meeting 1–2 but failing 3–5 is recorded as **OBSERVED, NOT REPLICATED**
and explicitly labelled as such in the library.

## Multiple-comparison discipline

Testing is staged, not brute force:
- **Stage A** marginal effects of ~100 binary observations (already done)
- **Stage B** the sweep decomposition tree — pre-specified, 12 branches
- **Stage C** location × event interactions — 6 events × 3 locations, pre-specified
- **Stage D** approach × location — 3 approach modes × 3 locations
- **Stage E** incremental information over a structure+location baseline

Expected false discoveries are reported per stage. A relationship surviving only
Stage A significance is not library-eligible.

## What is explicitly NOT in scope this phase

No entries, stops, targets, R:R, sizing, policy, or backtest. No transaction
costs, because nothing is traded. Layer 3 (decision) is out of scope by
instruction; this phase is Layer 1 (observation) + Layer 2 (behaviour).

## Long/short

Every relationship is computed separately for upward and downward forward
behaviour. Symmetry is never assumed and is reported when found.
