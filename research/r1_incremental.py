#!/usr/bin/env python3
"""R-1 FIRST QUESTION -- does microstructure add DIRECTIONAL information
beyond the OHLCV/situation representation?

Three models, identical purged+embargoed CV, identical uniqueness weights:
    A  OHLCV-only      (the 21-feature situation vector)
    B  MICRO-only      (OI / flow / positioning / book / carry)
    C  OHLCV + MICRO

The decisive quantity is AUC(C) - AUC(A). If that is not materially positive
and stable, the feature family is rejected -- regardless of how good B looks on
its own, because B may simply be rediscovering what A already knows.

Also reports per-feature univariate AUC so a single strong variable cannot hide
inside an ensemble.
"""
import sys, os, pickle, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import situations as S, ml_model as M, r1_features as R1
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

def forward_dir(b, rows, horizon):
    """Sign of the forward move, strictly from t+1 onward."""
    c = b['c']; i1 = b['i1m']; n = len(c)
    C1 = forward_dir.C1
    y = np.full(n, np.nan)
    for i in range(60, n-1):
        j1 = i1[min(i+1+horizon, n-1)]
        if j1 <= i1[i+1]: continue
        y[i] = 1.0 if C1[j1-1] > c[i] else 0.0
    return y

def cv_auc(X, y, ok, horizon, n, seed=0, max_iter=200):
    idx = np.where(ok)[0]; P = np.full(n, np.nan)
    for tr, te in M.purged_folds(n, idx, horizon):
        w = M.uniqueness_weights(tr, horizon, n)
        clf = HistGradientBoostingClassifier(max_depth=4, max_iter=max_iter,
                learning_rate=0.05, min_samples_leaf=200,
                l2_regularization=1.0, random_state=seed)
        clf.fit(X[tr], y[tr], sample_weight=w)
        P[te] = clf.predict_proba(X[te])[:,1]
    s = np.isfinite(P)
    return roc_auc_score(y[s], P[s]), s.sum()

def run(rows, tag, horizons=(1,3,6,12,36)):
    b = S.agg(rows,5); st = S.situations(b)
    forward_dir.C1 = np.array([r[4] for r in rows])
    Xo, _, _, _, _, _ = M.build_matrix(rows, k_atr=7.0, rr=1.5, horizon=96)
    Xm, names = R1.build(b)
    n = len(b['c'])
    Xc = np.column_stack([Xo, Xm])
    cov = np.isfinite(Xm).all(1)
    print(f"\n{'='*96}\n{tag}   n5m={n:,}   microstructure coverage {cov.mean():.1%}"
          f"   ({Xm.shape[1]} micro features)\n{'='*96}")
    print(f"{'horizon':<12}{'n':>9}{'A OHLCV':>10}{'B MICRO':>10}{'C BOTH':>10}"
          f"{'C-A':>9}{'  verdict'}")
    out = {}
    for hz in horizons:
        y = forward_dir(b, rows, hz)
        ok = np.isfinite(y) & np.isfinite(Xo).all(1) & cov
        if ok.sum() < 5000: continue
        a,_ = cv_auc(Xo, y, ok, hz, n)
        bb,_ = cv_auc(Xm, y, ok, hz, n)
        c,cn = cv_auc(Xc, y, ok, hz, n)
        inc = c-a
        v = "INCREMENTAL" if inc > 0.01 else ("marginal" if inc > 0.003 else "none")
        print(f"{hz*5:>3}min{'':<7}{cn:>9,}{a:>10.4f}{bb:>10.4f}{c:>10.4f}"
              f"{inc:>+9.4f}   {v}")
        out[hz] = (a,bb,c)
    return b, st, Xo, Xm, names, out

def univariate(b, rows, Xm, names, horizon=6):
    y = forward_dir(b, rows, horizon)
    print(f"\n  univariate directional AUC at {horizon*5}min "
          f"(|AUC-0.5| > 0.01 is worth a second look)")
    res = []
    for j, nm in enumerate(names):
        m = np.isfinite(Xm[:,j]) & np.isfinite(y)
        if m.sum() < 20000: continue
        try: a = roc_auc_score(y[m], Xm[m,j])
        except Exception: continue
        res.append((abs(a-0.5), a, nm, int(m.sum())))
    res.sort(reverse=True)
    for d,a,nm,cnt in res[:14]:
        flag = "  <<<" if d > 0.01 else ""
        print(f"    {nm:<26}{a:>8.4f}{a-0.5:>+9.4f}{cnt:>10,}{flag}")
    return res

if __name__ == "__main__":
    rows = pickle.load(open("data/is/BTCUSDT-1m.pkl","rb"))
    b, st, Xo, Xm, names, out = run(rows, "EXPLORE 2025-01..2026-08")
    univariate(b, rows, Xm, names)
