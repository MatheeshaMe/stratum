"""R-3 path-barrier engine. Absolute-% barriers, first passage on 1m bars.

For every 5m entry this computes the first-passage time to each level in a grid
of target and stop percentages, so any (stop, target, horizon) cell can be
scored without re-walking the path.

Conventions, all conservative:
  * barriers are measured from the entry CLOSE
  * a bar that touches both barriers resolves to the STOP
  * unresolved at the horizon is marked out at the close, not charged a stop
  * entry at t is evaluated from t+1 onward (no same-bar fills)
"""
import numpy as np

STOPS   = np.array([0.05,0.10,0.15,0.20,0.30,0.40,0.50,0.75,1.00])/100
TARGETS = np.array([0.10,0.15,0.20,0.30,0.40,0.50,0.75,1.00,1.50])/100
HORIZONS = [5,15,30,60,120]           # minutes
HMAX = max(HORIZONS)
NEVER = np.int32(10**6)

def first_passage(rows, entry_idx, side=+1, chunk=20000):
    """Returns (tp_time, sl_time) int arrays of shape (n_entries, n_levels).

    side=+1 LONG : target above entry, stop below
    side=-1 SHORT: target below entry, stop above
    Times are in minutes after the entry bar; NEVER if not reached within HMAX.
    """
    H = np.asarray([r[2] for r in rows], dtype=np.float64)
    L = np.asarray([r[3] for r in rows], dtype=np.float64)
    C = np.asarray([r[4] for r in rows], dtype=np.float64)
    n = len(entry_idx)
    tp = np.full((n, len(TARGETS)), NEVER, dtype=np.int32)
    sl = np.full((n, len(STOPS)),   NEVER, dtype=np.int32)
    for a in range(0, n, chunk):
        e = entry_idx[a:a+chunk]
        keep = e + HMAX + 1 < len(C)
        e = e[keep]
        if len(e) == 0: continue
        off = np.arange(1, HMAX+1)
        idx = e[:,None] + off[None,:]
        px  = C[e][:,None]
        rh  = np.maximum.accumulate(H[idx], axis=1) / px      # running max, relative
        rl  = np.minimum.accumulate(L[idx], axis=1) / px      # running min, relative
        sl_a = slice(a, a+len(e))
        if side > 0:
            up, dn = rh, rl
            up_lv, dn_lv = 1+TARGETS, 1-STOPS
            up_hit = lambda k: up >= up_lv[k]
            dn_hit = lambda k: dn <= dn_lv[k]
        else:
            up, dn = rl, rh
            up_lv, dn_lv = 1-TARGETS, 1+STOPS
            up_hit = lambda k: up <= up_lv[k]
            dn_hit = lambda k: dn >= dn_lv[k]
        for k in range(len(TARGETS)):
            m = up_hit(k); any_ = m.any(1)
            t = m.argmax(1) + 1
            tp[sl_a][:len(e)]                       # (no-op, keep shape clear)
            tp[a:a+len(e), k] = np.where(any_, t, NEVER)
        for k in range(len(STOPS)):
            m = dn_hit(k); any_ = m.any(1)
            t = m.argmax(1) + 1
            sl[a:a+len(e), k] = np.where(any_, t, NEVER)
    return tp, sl

def markout(rows, entry_idx, horizon):
    """Return at the vertical barrier, as a fraction of entry price."""
    C = np.asarray([r[4] for r in rows], dtype=np.float64)
    e = entry_idx
    j = np.minimum(e + horizon, len(C)-1)
    return C[j]/C[e] - 1.0

def score_cell(tp_t, sl_t, mo, si, ti, horizon, side, stop, target, cost):
    """Outcome and net return (% of notional) for one (stop, target, horizon)."""
    t = tp_t[:, ti]; s = sl_t[:, si]
    tp_ok = t <= horizon; sl_ok = s <= horizon
    win  = tp_ok & (t < s)          # ties -> stop
    lose = sl_ok & ~win
    unres = ~win & ~lose
    ret = np.where(win, target, np.where(lose, -stop, side*mo))
    return win, lose, unres, ret - cost
