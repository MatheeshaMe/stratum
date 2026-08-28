#!/usr/bin/env python3
"""R-1 SECOND + FIFTH QUESTIONS.

Q2  Resolution is already strongly predictable (AUC ~0.77). So condition on
    states the model expects to MOVE, and ask whether microstructure resolves
    direction there. Direction across all states is the wrong denominator --
    most states go nowhere and dilute any signal.

Q5  magnitude x direction. Does 'high expected movement + strong directional
    microstructure' produce an asymmetric conditional distribution, as opposed
    to merely a higher win rate?

Reports the full conditional distribution, never a bare win rate.
"""
import sys, os, pickle, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import situations as S, ml_model as M, r1_features as R1
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.metrics import roc_auc_score

def oof(X, y, ok, horizon, n, kind="clf", seed=0):
    idx = np.where(ok)[0]; P = np.full(n, np.nan)
    for tr, te in M.purged_folds(n, idx, horizon):
        w = M.uniqueness_weights(tr, horizon, n)
        C = (HistGradientBoostingClassifier if kind=="clf" else HistGradientBoostingRegressor)
        m = C(max_depth=4, max_iter=200, learning_rate=0.05,
              min_samples_leaf=200, l2_regularization=1.0, random_state=seed)
        m.fit(X[tr], y[tr], sample_weight=w)
        P[te] = m.predict_proba(X[te])[:,1] if kind=="clf" else m.predict(X[te])
    return P

def forward(b, rows, horizon):
    c = b['c']; A = forward.A; i1 = b['i1m']; n = len(c)
    H1, L1, C1 = forward.H1, forward.L1, forward.C1
    fwd_ret = np.full(n, np.nan); rng = np.full(n, np.nan)
    mfe_l = np.full(n, np.nan); mae_l = np.full(n, np.nan)
    for i in range(60, n-1):
        a = A[i]
        if not np.isfinite(a): continue
        j0 = i1[i+1]; j1 = i1[min(i+1+horizon, n-1)]
        if j1 <= j0: continue
        hi = H1[j0:j1].max(); lo = L1[j0:j1].min(); end = C1[j1-1]
        fwd_ret[i] = (end - c[i])/a
        rng[i] = (hi-lo)/a
        mfe_l[i] = (hi - c[i])/a
        mae_l[i] = (c[i] - lo)/a
    return fwd_ret, rng, mfe_l, mae_l

def run(rows, tag, horizon=12):
    b = S.agg(rows,5); st = S.situations(b); n = len(b['c'])
    forward.A = st['A']
    forward.H1 = np.array([r[2] for r in rows]); forward.L1 = np.array([r[3] for r in rows])
    forward.C1 = np.array([r[4] for r in rows])
    Xo,_,_,_,_,_ = M.build_matrix(rows, k_atr=7.0, rr=1.5, horizon=96)
    Xm, names = R1.build(b)
    Xc = np.column_stack([Xo, Xm])
    fwd, rng, mfe, mae = forward(b, rows, horizon)
    core = [i for i,nm in enumerate(names) if not nm.startswith('book_')]
    cov = np.isfinite(Xm[:, core]).all(1) & np.isfinite(Xo).all(1)
    ok = cov & np.isfinite(fwd) & np.isfinite(rng)
    print(f"\n{'='*100}\n{tag}   horizon {horizon*5}min   n={ok.sum():,}\n{'='*100}")

    # magnitude model (OHLCV is already known to be good at this)
    mag = oof(Xo, rng, ok, horizon, n, kind="reg")
    ydir = (fwd > 0).astype(float)
    dir_o = oof(Xo, ydir, ok, horizon, n)
    dir_c = oof(Xc, ydir, ok, horizon, n)

    m = ok & np.isfinite(mag) & np.isfinite(dir_c)
    q = np.quantile(mag[m], [0.5, 0.8, 0.9])
    print(f"\nQ2  directional AUC by EXPECTED-MAGNITUDE tercile")
    print(f"  {'expected magnitude':<26}{'n':>9}{'AUC OHLCV':>12}{'AUC +micro':>12}{'delta':>9}")
    bands = [("all states", m),
             ("bottom 50% (quiet)", m & (mag <= q[0])),
             ("top 50%", m & (mag > q[0])),
             ("top 20%", m & (mag > q[1])),
             ("top 10% (biggest moves)", m & (mag > q[2]))]
    for lbl, mm in bands:
        if mm.sum() < 2000: continue
        a = roc_auc_score(ydir[mm], dir_o[mm]); c = roc_auc_score(ydir[mm], dir_c[mm])
        print(f"  {lbl:<26}{mm.sum():>9,}{a:>12.4f}{c:>12.4f}{c-a:>+9.4f}")

    print(f"\nQ5  magnitude x direction -- full conditional distribution")
    print(f"  {'cell':<34}{'n':>8}{'P(up)':>8}{'medRet':>9}{'meanRet':>9}"
          f"{'MFE':>8}{'MAE':>8}{'MFE-MAE':>9}")
    hi_mag = m & (mag > q[1])
    dq = np.quantile(dir_c[hi_mag], [0.2, 0.8])
    cells = [("ALL states (baseline)", m),
             ("high magnitude, any direction", hi_mag),
             ("high magnitude + bullish micro", hi_mag & (dir_c >= dq[1])),
             ("high magnitude + bearish micro", hi_mag & (dir_c <= dq[0])),
             ("low magnitude (control)", m & (mag <= q[0]))]
    for lbl, mm in cells:
        if mm.sum() < 500: continue
        print(f"  {lbl:<34}{mm.sum():>8,}{(fwd[mm]>0).mean():>8.1%}"
              f"{np.median(fwd[mm]):>+9.3f}{fwd[mm].mean():>+9.3f}"
              f"{np.median(mfe[mm]):>8.2f}{np.median(mae[mm]):>8.2f}"
              f"{np.median(mfe[mm])-np.median(mae[mm]):>+9.2f}")
    print("  (Ret/MFE/MAE in ATR units, long-side convention)")
    return dict(mag=mag, dir_o=dir_o, dir_c=dir_c, fwd=fwd, rng=rng, ok=ok,
                mfe=mfe, mae=mae, b=b, st=st)

if __name__ == "__main__":
    run(pickle.load(open("data/explore_r1.pkl","rb")), "R1-EXPLORE 2023-01..2026-07 (merged, non-sealed)")
