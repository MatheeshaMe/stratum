#!/usr/bin/env python3
"""R-1 THIRD QUESTION + C4 control. Does the surviving information pay?

Part 1 (C4 fix): the magnitude x direction split run three ways -- OHLCV-only,
micro-only, combined -- on identical rows. If OHLCV alone produces the same
spread, microstructure adds nothing regardless of how good the combined split
looks on its own.

Part 2: convert every surviving event effect from ATR units into basis points
and compare it to the round-trip cost it must clear. This is the P1 hurdle
applied to R-1.
"""
import sys, os, pickle, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import situations as S, ml_model as M, r1_features as R1
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.metrics import roc_auc_score

COST = {"maker/maker": 3.0, "maker/taker": 6.63, "taker/taker": 10.26}   # bps RT

def oof(X, y, ok, hz, n, kind="clf"):
    idx = np.where(ok)[0]; P = np.full(n, np.nan)
    for tr, te in M.purged_folds(n, idx, hz):
        w = M.uniqueness_weights(tr, hz, n)
        C = HistGradientBoostingClassifier if kind=="clf" else HistGradientBoostingRegressor
        m = C(max_depth=4, max_iter=200, learning_rate=0.05,
              min_samples_leaf=200, l2_regularization=1.0, random_state=0)
        m.fit(X[tr], y[tr], sample_weight=w)
        P[te] = m.predict_proba(X[te])[:,1] if kind=="clf" else m.predict(X[te])
    return P

def main(hz=12):
    rows = pickle.load(open("data/explore_r1.pkl","rb"))
    b = S.agg(rows,5); st = S.situations(b); n = len(b['c'])
    A = st['A']; c = b['c']; i1 = b['i1m']
    C1 = np.array([r[4] for r in rows]); H1 = np.array([r[2] for r in rows])
    L1 = np.array([r[3] for r in rows])
    fwd = np.full(n, np.nan); rng = np.full(n, np.nan)
    for i in range(60, n-1):
        a = A[i]
        if not np.isfinite(a): continue
        j0=i1[i+1]; j1=i1[min(i+1+hz, n-1)]
        if j1<=j0: continue
        fwd[i]=(C1[j1-1]-c[i])/a; rng[i]=(H1[j0:j1].max()-L1[j0:j1].min())/a
    Xo,_,_,_,_,_ = M.build_matrix(rows, k_atr=7.0, rr=1.5, horizon=96)
    Xm, names = R1.build(b)
    core = [i for i,nm in enumerate(names) if not nm.startswith('book_')]
    ok = np.isfinite(Xo).all(1) & np.isfinite(Xm[:,core]).all(1) & np.isfinite(fwd) & np.isfinite(rng)
    y = (fwd>0).astype(float)
    print(f"\n{'='*104}\nC4 CONTROL -- magnitude x direction, three models, identical rows "
          f"(n={ok.sum():,}, {hz*5}min)\n{'='*104}")
    mag = oof(Xo, rng, ok, hz, n, kind="reg")
    P = {"OHLCV only": oof(Xo, y, ok, hz, n),
         "MICRO only": oof(Xm, y, ok, hz, n),
         "OHLCV+MICRO": oof(np.column_stack([Xo,Xm]), y, ok, hz, n)}
    m = ok & np.isfinite(mag)
    q80 = np.quantile(mag[m], 0.8)
    himag = m & (mag > q80)
    print(f"  {'model':<16}{'AUC(all)':>10}{'AUC(hi-mag)':>13}"
          f"{'P(up) top Q':>13}{'P(up) bot Q':>13}{'spread':>9}{'  meanRet spread':>17}")
    for lbl, p in P.items():
        mm = m & np.isfinite(p); hh = himag & np.isfinite(p)
        dq = np.quantile(p[hh], [0.2, 0.8])
        top = hh & (p>=dq[1]); bot = hh & (p<=dq[0])
        a_all = roc_auc_score(y[mm], p[mm]); a_hi = roc_auc_score(y[hh], p[hh])
        sp = (y[top].mean()-y[bot].mean())
        rsp = fwd[top].mean()-fwd[bot].mean()
        print(f"  {lbl:<16}{a_all:>10.4f}{a_hi:>13.4f}{y[top].mean():>13.1%}"
              f"{y[bot].mean():>13.1%}{sp:>+9.1%}{rsp:>+17.3f}")
    print("  spread = P(up) top quintile minus bottom quintile of that model's own score")
    print("  meanRet spread in ATR units. If OHLCV-only matches the combined model,")
    print("  microstructure contributes nothing.")

    # ---- Part 2: economics
    atr_bps = np.nanmedian(A/c)*1e4
    print(f"\n{'='*104}\nECONOMICS -- surviving effects vs the cost they must clear\n{'='*104}")
    print(f"  BTC 5m ATR = {atr_bps:.2f} bps of price (median over the exploratory window)")
    print(f"  round-trip cost: maker/maker {COST['maker/maker']}bps | "
          f"maker/taker {COST['maker/taker']}bps | taker/taker {COST['taker/taker']}bps\n")
    EFF = [("aggressive SELL flow, 30m", 0.049, "survives all controls"),
           ("top traders max SHORT, 30m", 0.060, "survives all controls"),
           ("book imb shock down, 30m", -0.042, "weak in 2nd half"),
           ("top traders max SHORT, 180m", 0.290, "CI spans zero"),
           ("funding extreme LOW, 180m", -0.320, "521 episodes, trend-like")]
    print(f"  {'effect':<32}{'ATR':>8}{'bps':>8}{'vs mm':>8}{'vs mt':>8}{'vs tt':>8}   note")
    for lbl, e, note in EFF:
        bps = abs(e)*atr_bps
        print(f"  {lbl:<32}{e:>+8.3f}{bps:>8.2f}"
              f"{bps/COST['maker/maker']:>8.2f}{bps/COST['maker/taker']:>8.2f}"
              f"{bps/COST['taker/taker']:>8.2f}   {note}")
    need = COST['maker/taker']/atr_bps
    print(f"\n  An effect must exceed {need:.3f} ATR to clear maker/taker cost alone.")
    print(f"  Largest effect surviving every control: 0.060 ATR "
          f"({0.060/need:.0%} of the hurdle).")

if __name__ == "__main__":
    main()
