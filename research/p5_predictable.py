#!/usr/bin/env python3
"""What IS predictable about BTC, if direction is not?

Direction has been tested to exhaustion: AUC 0.50-0.55, every bucket excess CI
spans zero, the unconditional process matches a driftless random walk to 0.8pp.

This asks the complementary question. For the same state vector and the same
purged CV, how predictable is:
    (a) DIRECTION   sign of the forward move          [known: ~nothing]
    (b) MAGNITUDE   realised volatility over the window
    (c) RESOLUTION  will this state resolve a +/-k ATR barrier at all?

If (b)/(c) are strongly predictable while (a) is not, the honest product is a
participation filter, not a signal generator -- and its value can be quantified
as the cost saved by not trading, not as EV earned by trading.
"""
import sys, os, pickle, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import situations as S
import ml_model as M
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.metrics import roc_auc_score, r2_score

def run(rows, tag, k_atr=7.0, horizon=96):
    X, _, _, _, b, st = M.build_matrix(rows, k_atr=k_atr, rr=1.5, horizon=horizon)
    c = b['c']; A = st['A']; n = len(c); i1 = b['i1m']
    H1 = np.array([r[2] for r in rows]); L1 = np.array([r[3] for r in rows])
    C1 = np.array([r[4] for r in rows])
    # forward targets, all strictly from t+1 onward
    y_dir = np.full(n, np.nan); y_mag = np.full(n, np.nan); y_res = np.full(n, np.nan)
    for i in range(60, n-1):
        a = A[i]
        if not np.isfinite(a): continue
        j0 = i1[i+1]; j1 = i1[min(i+1+horizon, n-1)]
        if j1 <= j0: continue
        seg_h = H1[j0:j1].max(); seg_l = L1[j0:j1].min(); end = C1[j1-1]
        y_dir[i] = 1.0 if end > c[i] else 0.0
        y_mag[i] = (seg_h - seg_l)/a                      # realised range in ATR
        y_res[i] = 1.0 if (seg_h >= c[i]+k_atr*a or seg_l <= c[i]-k_atr*a) else 0.0
    ok = np.isfinite(X).all(1) & np.isfinite(y_dir) & np.isfinite(y_mag)
    idx = np.where(ok)[0]
    print(f"\n{tag}   horizon {horizon} bars ({horizon*5}min), barrier {k_atr} ATR, n={ok.sum():,}")
    print(f"  {'target':<32}{'baseline':>12}{'model':>12}{'skill':>10}")
    for name, y, kind in (("(a) DIRECTION  sign of move", y_dir, "clf"),
                          ("(c) RESOLUTION reaches barrier", y_res, "clf"),
                          ("(b) MAGNITUDE  range in ATR", y_mag, "reg")):
        P = np.full(n, np.nan)
        for tr, te in M.purged_folds(n, idx, horizon):
            w = M.uniqueness_weights(tr, horizon, n)
            if kind == "clf":
                m = HistGradientBoostingClassifier(max_depth=4, max_iter=200,
                        learning_rate=0.05, min_samples_leaf=200, random_state=0)
                m.fit(X[tr], y[tr], sample_weight=w); P[te] = m.predict_proba(X[te])[:,1]
            else:
                m = HistGradientBoostingRegressor(max_depth=4, max_iter=200,
                        learning_rate=0.05, min_samples_leaf=200, random_state=0)
                m.fit(X[tr], y[tr], sample_weight=w); P[te] = m.predict(X[te])
        s = np.isfinite(P)
        if kind == "clf":
            auc = roc_auc_score(y[s], P[s])
            print(f"  {name:<32}{'AUC 0.500':>12}{f'AUC {auc:.3f}':>12}{auc-0.5:>+10.3f}")
        else:
            r2 = r2_score(y[s], P[s])
            print(f"  {name:<32}{'R2 0.000':>12}{f'R2 {r2:.3f}':>12}{r2:>+10.3f}")
    return

if __name__ == "__main__":
    for tag, p in (("EXPLORE 2025-26","data/is/BTCUSDT-1m.pkl"),
                   ("VALIDATE 2023-24","data/oos/BTCUSDT-1m.pkl")):
        run(pickle.load(open(p,"rb")), tag)
