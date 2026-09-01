# Pre-specification — written before any thesis was scored

## Data splits (fixed, no tuning on the held-out set)

| set | window | use |
|---|---|---|
| DISCOVERY | 2017-08 → 2021-12 | thesis selection, entry/management choice |
| VALIDATION | 2022-01 → 2024-12 | confirm or kill |
| **HELD OUT** | **2025-01 → 2026-07** | **touched once, at the end** |
| cross-asset | ETH, SOL, XRP, DOGE | full period, structural transfer test |

## Theses (pre-specified, hierarchy applied top-down)

| id | thesis | context conditions |
|---|---|---|
| **T0** | zone touch alone (baseline) | none |
| **T1** | + regime alignment | HTF trend agrees with zone side |
| **T2** | + HTF location | demand in discount (range_pos<0.5) / supply in premium (>0.5) |
| **T3** | + liquidity event | sell-side swept before a demand touch / buy-side before supply |
| **T4** | + approach quality | approach decelerating (app_decel < 1.0) |
| **T5** | full stack | T4 + the zone's departure broke structure |
| **R1** | reversal at extreme | zone at HTF extreme (range_pos>0.85 / <0.15) + liquidity swept + AGAINST HTF trend |

## Entry models
A blind limit at proximal edge · B rejection candle → market · C sweep+reversal → market
D local CHoCH → pullback limit · E momentum continuation → market

## Management
fixed 2R/3R/5R · trail 2.5 ATR · trail structural · all with the stop live on the entry bar

## Pass criteria for any thesis
1. Positive net EV on DISCOVERY with n ≥ 150
2. Sign holds on VALIDATION
3. Ablation shows the added component contributes (removing it degrades EV)
4. Survives on HELD OUT with a CI excluding zero
5. Positive on ≥ 3 of 5 assets

## Expected false discoveries
7 theses × 5 entry models × 5 management modes = 175 cells on discovery.
At α = 0.05 that is ~9 expected false positives. Discovery significance alone
means nothing; the held-out and ablation steps carry the weight.
