"""Calibrated situation model -- the ML layer, built so it cannot flatter itself.

What this model is NOT: a price predictor. It never outputs a direction or a
target. It outputs ONE number: P(target before stop | this situation), and it
is judged on whether that number is HONEST (calibration), not on whether it
is high (accuracy).

Three defences against the usual self-deception:

  1. PURGED, EMBARGOED, FORWARD-ONLY CV. Folds are contiguous in time. Training
     samples whose forward window overlaps the test fold are dropped (purge),
     plus an embargo gap. Without this, overlapping labels leak the answer.
  2. SAMPLE WEIGHTS BY UNIQUENESS. Overlapping triple-barrier labels are not
     independent. Concurrent labels get down-weighted so 5,000 overlapping
     bars do not count as 5,000 observations.
  3. THE HONEST BASELINE. Every score is reported against the base rate. A
     model that cannot beat "always predict the base rate" is reported as
     having no edge, in those words.
"""
import sys, os, pickle, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import situations as S
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import roc_auc_score, brier_score_loss

FEATS = ["dist_up","dist_dn","ext","rsi","vz","regime","stru",
         "up_touch","dn_touch","atr_pct","atr_z","hour","dow",
         "ret_1","ret_6","ret_36","rng_ratio","vol_ratio","body_frac","wick_up","wick_dn"]

def build_matrix(rows, k_atr=2.0, rr=1.5, horizon=36, side=+1):
    b = S.agg(rows, 5); st = S.situations(b)
    c,h,l,o,v = b['c'],b['h'],b['l'],b['o'],b['v']; A = st['A']; n = len(c)
    atr_pct = A/c
    atr_z = np.full(n, np.nan)
    for i in range(200, n):
        w = atr_pct[i-200:i]; s = np.nanstd(w)
        atr_z[i] = (atr_pct[i]-np.nanmean(w))/(s if s>0 else 1e-12)
    ret = lambda k: np.concatenate([np.full(k,np.nan), (c[k:]-c[:-k])/A[k:]])
    rng = (h-l)/np.where(A==0,1e-12,A)
    rng_ratio = rng/np.concatenate([[np.nan], np.convolve(rng,np.ones(20)/20,'full')[:n-1]])
    vma = np.convolve(v,np.ones(20)/20,'full')[:n]
    vol_ratio = v/np.where(vma==0,1e-12,vma)
    body = np.abs(c-o); tot = np.where((h-l)==0,1e-12,h-l)
    hours = ((b['t']//3600000)%24).astype(float)
    dow = ((b['t']//86400000+4)%7).astype(float)
    X = np.column_stack([
        st['dist_up'], st['dist_dn'], st['ext'], st['rsi'], st['vz'],
        st['regime'], st['stru'], st['up_touch'], st['dn_touch'],
        atr_pct*100, atr_z, hours, dow,
        ret(1), ret(6), ret(36), rng_ratio, vol_ratio,
        body/tot, (h-np.maximum(o,c))/tot, (np.minimum(o,c)-l)/tot])
    y, bars = S.triple_barrier(rows, b, st, k_atr=k_atr, horizon=horizon, side=side, rr=rr)
    # binary: did the target get hit before the stop? vertical counts as a miss
    lab = np.where(y==1, 1, 0).astype(float); lab[y<0] = np.nan
    ok = np.isfinite(X).all(1) & np.isfinite(lab) & (atr_pct*k_atr >= 0.006)
    return X, lab, ok, bars, b, st

def purged_folds(n, ok_idx, horizon, n_folds=5, embargo=None):
    """Contiguous forward folds; purge train samples overlapping the test window."""
    embargo = embargo if embargo is not None else horizon*3
    edges = np.linspace(0, n, n_folds+1).astype(int)
    for f in range(1, n_folds):                 # fold 0 is train-only warmup
        te_lo, te_hi = edges[f], edges[f+1]
        te = ok_idx[(ok_idx >= te_lo) & (ok_idx < te_hi)]
        tr = ok_idx[(ok_idx < te_lo - horizon - embargo) |
                    (ok_idx >= te_hi + embargo)]
        if len(te) < 500 or len(tr) < 2000: continue
        yield tr, te

def uniqueness_weights(idx, horizon, n):
    """Down-weight overlapping labels: a bar covered by many concurrent forward
    windows carries less independent information."""
    cnt = np.zeros(n+horizon+2)
    for i in idx: cnt[i:i+horizon] += 1
    w = np.array([ (1.0/np.maximum(cnt[i:i+horizon],1)).mean() for i in idx ])
    return w/w.mean()

def reliability(p, y, bins=10):
    out = []
    qs = np.quantile(p, np.linspace(0,1,bins+1))
    for i in range(bins):
        m = (p >= qs[i]) & (p <= qs[i+1] if i==bins-1 else p < qs[i+1])
        if m.sum() < 50: continue
        out.append((p[m].mean(), y[m].mean(), int(m.sum())))
    return out

def evaluate(rows, tag, side=+1, k_atr=2.0, rr=1.5, horizon=36):
    X, lab, ok, bars, b, st = build_matrix(rows, k_atr, rr, horizon, side)
    n = len(lab); ok_idx = np.where(ok)[0]
    base = lab[ok].mean()
    P = np.full(n, np.nan)
    for tr, te in purged_folds(n, ok_idx, horizon):
        w = uniqueness_weights(tr, horizon, n)
        clf = HistGradientBoostingClassifier(
            max_depth=4, max_iter=250, learning_rate=0.05,
            min_samples_leaf=200, l2_regularization=1.0, random_state=0)
        cal = CalibratedClassifierCV(clf, method="isotonic", cv=3)
        cal.fit(X[tr], lab[tr], sample_weight=w)
        P[te] = cal.predict_proba(X[te])[:,1]
    m = np.isfinite(P)
    p, y = P[m], lab[m]
    auc = roc_auc_score(y, p); br = brier_score_loss(y, p)
    br_base = brier_score_loss(y, np.full(len(y), base))
    sname = "LONG" if side>0 else "SHORT"
    print(f"\n{tag} {sname}  target {rr}R before {k_atr}ATR stop, {horizon*5}min horizon")
    print(f"  n={len(y):,}  base rate={base:.1%}  AUC={auc:.4f}  "
          f"Brier={br:.4f} vs base {br_base:.4f}  skill={1-br/br_base:+.2%}")
    print(f"  {'model p':>10}{'actual':>10}{'n':>9}   calibration")
    for pm, ym, cnt in reliability(p, y):
        bar = "#"*int(ym*60)
        print(f"  {pm:>10.1%}{ym:>10.1%}{cnt:>9,}   {bar}")
    # what a threshold policy would actually earn, net of cost
    print(f"  {'threshold':>10}{'trades':>9}{'hit%':>8}{'EV R/trade':>12}{'EV R/opp':>11}")
    for th in (0.35, 0.40, 0.45, 0.50):
        sel = p >= th
        if sel.sum() < 30: continue
        hit = y[sel].mean()
        ev = hit*rr - (1-hit)*1.0 - 0.05      # vertical exit charged as a full stop (conservative)
        print(f"  {th:>10.2f}{sel.sum():>9,}{hit:>8.1%}{ev:>+12.3f}"
              f"{ev*sel.sum()/len(y):>+11.4f}")
    return auc, base

if __name__ == "__main__":
    for tag, path in (("IS  2025-26","data/is/BTCUSDT-1m.pkl"),
                      ("OOS 2023-24","data/oos/BTCUSDT-1m.pkl")):
        rows = pickle.load(open(path,"rb"))
        for side in (+1, -1):
            evaluate(rows, tag, side=side)
