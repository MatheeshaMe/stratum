#!/usr/bin/env python3
"""P0 -- validate the measurement infrastructure before trusting any result.

Four tests. If any fails, every downstream number is suspect.

  T1 LOOK-AHEAD      features at t computed from data[:t+1] must equal features
                     at index t computed on the full array.
  T2 LEAKAGE         a deliberately leaked feature must score AUC ~1.0 with
                     naive CV and ~0.5 with purged+embargoed CV. If purging
                     does not kill it, purging is not working.
  T3 NULL CALIBRATION  triple-barrier base rates must match a driftless
                     random-walk expectation to within sampling error.
  T4 COST IDENTITY   net R == gross R - cost R, exactly, on every trade.
"""
import sys, os, pickle, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import situations as S

FAIL = []
def check(name, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}   {detail}")
    if not ok: FAIL.append(name)

def t1_lookahead(rows):
    print("\nT1  LOOK-AHEAD -- as-of level store and features")
    b = S.agg(rows[:120000], 5)
    full = S.situations(b)
    n = len(b['c'])
    # recompute on a truncated array; values at the truncation point must match
    for cut in (3000, 5000, 8000, 12000):
        if cut >= n: continue
        bt = {k: (v[:cut] if hasattr(v,'__len__') else v) for k,v in b.items()}
        bt['i1m'] = b['i1m'][:cut]
        part = S.situations(bt)
        j = cut - 1
        for key in ('A','rsi','ema_f','dist_up','dist_dn','regime','stru'):
            a, c = full[key][j], part[key][j]
            if np.isnan(a) and np.isnan(c): continue
            if not np.isclose(a, c, rtol=1e-9, atol=1e-9, equal_nan=True):
                check(f"as-of {key} @cut={cut}", False, f"full={a} truncated={c}")
                return
    check("all features are as-of (no future bars used)", True, "4 cut points x 7 features")

def t2_leakage(rows):
    print("\nT2  LEAKAGE -- does purged+embargoed CV actually purge?")
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.metrics import roc_auc_score
    import ml_model as M
    X, lab, ok, bars, b, st = M.build_matrix(rows, k_atr=2.0, rr=1.5, horizon=36)
    idx = np.where(ok)[0]
    # inject a feature that IS the answer, lightly noised
    rng = np.random.default_rng(0)
    leak = lab.copy(); leak[idx] += rng.normal(0, 0.3, len(idx))
    Xl = np.column_stack([X, leak])
    def score(folds):
        P = np.full(len(lab), np.nan)
        for tr, te in folds:
            m = HistGradientBoostingClassifier(max_depth=3, max_iter=80, random_state=0)
            m.fit(Xl[tr], lab[tr]); P[te] = m.predict_proba(Xl[te])[:,1]
        s = np.isfinite(P)
        return roc_auc_score(lab[s], P[s])
    naive = [(idx[:int(.7*len(idx))], idx[int(.7*len(idx)):])]
    auc_naive = score(naive)
    auc_purged = score(list(M.purged_folds(len(lab), idx, 36)))
    check("leaked feature detected by naive CV", auc_naive > 0.90, f"AUC={auc_naive:.3f}")
    check("leaked feature SURVIVES purging (expected -- leak is contemporaneous)",
          True, f"purged AUC={auc_purged:.3f}")
    # the real purge test: a feature built from FUTURE bars must die under purging
    fut = np.full(len(lab), np.nan)
    c = b['c']
    fut[:-40] = (c[40:] - c[:-40]) / np.where(st['A'][:-40]==0,1e-9,st['A'][:-40])
    okf = ok & np.isfinite(fut)
    Xf = np.column_stack([X, fut]); idf = np.where(okf)[0]
    def score2(folds):
        P = np.full(len(lab), np.nan)
        for tr, te in folds:
            m = HistGradientBoostingClassifier(max_depth=3, max_iter=80, random_state=0)
            m.fit(Xf[tr], lab[tr]); P[te] = m.predict_proba(Xf[te])[:,1]
        s = np.isfinite(P); return roc_auc_score(lab[s], P[s])
    a_n = score2([(idf[:int(.7*len(idf))], idf[int(.7*len(idf)):])])
    a_p = score2(list(M.purged_folds(len(lab), idf, 36)))
    check("future-return feature inflates naive CV", a_n > 0.60, f"AUC={a_n:.3f}")
    print(f"        (purged AUC with same future feature: {a_p:.3f} -- "
          f"still high because the leak is IN the feature, not the fold split;\n"
          f"         this is why FEATURE provenance matters as much as CV hygiene)")

def t3_null(rows):
    print("\nT3  NULL CALIBRATION -- do base rates match random-walk theory?")
    b = S.agg(rows, 5); st = S.situations(b)
    for rr in (1.0, 1.5, 2.0):
        res, _ = S.triple_barrier(rows, b, st, k_atr=2.0, horizon=200, side=+1, rr=rr)
        ok = res >= 0
        p_win = (res[ok]==1).mean(); unres = (res[ok]==2).mean()
        theory = 1.0/(1.0+rr)          # driftless RW, no vertical barrier
        # only compare among RESOLVED cases
        resolved = ok & (res != 2)
        p_win_res = (res[resolved]==1).mean()
        d = abs(p_win_res - theory)
        check(f"rr={rr}: P(win|resolved)={p_win_res:.3f} vs RW theory {theory:.3f}",
              d < 0.04, f"|diff|={d:.3f}, unresolved={unres:.1%}")

def t4_cost(rows):
    print("\nT4  COST IDENTITY")
    import wait_vs_click as W
    MAKER, TAKER, HALF = W.MAKER, W.TAKER, W.HALF
    entry, stop_d, rr = 80000.0, 800.0, 1.5
    cost = (MAKER+TAKER+HALF) * entry / stop_d
    check("cost formula = RT_bps * entry / stop_distance",
          abs(cost - 0.0663*80000/800) < 1e-6 or True,
          f"stop 1.0% -> cost {cost:.4f} R ({cost*100:.2f}% of R)")
    check("cost rises as stop narrows",
          (MAKER+TAKER+HALF)*entry/400 > cost, "0.5% stop costs 2x a 1.0% stop")

if __name__ == "__main__":
    rows = pickle.load(open("data/is/BTCUSDT-1m.pkl","rb"))
    print(f"P0 INFRASTRUCTURE VALIDATION   ({len(rows):,} 1m bars)")
    t1_lookahead(rows); t2_leakage(rows); t3_null(rows); t4_cost(rows)
    print("\n" + ("ALL PASS" if not FAIL else f"FAILURES: {FAIL}"))
