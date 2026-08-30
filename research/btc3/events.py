"""BTC +3% event detection and feature construction.

Event definitions (each a separate class, never mixed):

  C2C   close-to-close   : first bar t with close[t]/close[t-W] - 1 >= +3%
  L2H   trailing-low     : first bar t with high[t]/min(low[t-W..t]) - 1 >= +3%
  O2H   open-to-high     : first bar t with high[t]/open[t-W] - 1 >= +3%

W in {5, 15, 60, 240, 1440} minutes.

T0 is the minute the threshold is first crossed. The reference point T_ref =
T0 - W is where the move began. Precursor features are measured at T_ref
(strictly before the move); state features are measured at T0.

Everything is causal: no feature at time x uses data after x.
"""
import numpy as np

WINDOWS = {"5m":5, "15m":15, "1h":60, "4h":240, "24h":1440}

def load(path):
    import pickle
    r = pickle.load(open(path,"rb"))
    return (np.array([x[0] for x in r], dtype=np.int64),
            np.array([x[1] for x in r]), np.array([x[2] for x in r]),
            np.array([x[3] for x in r]), np.array([x[4] for x in r]),
            np.array([x[5] for x in r]), np.array([x[6] for x in r], dtype=np.int64))

def rolling_min(x, w):
    from numpy.lib.stride_tricks import sliding_window_view
    out = np.full(len(x), np.nan)
    if len(x) >= w: out[w-1:] = sliding_window_view(x, w).min(1)
    return out

def rolling_max(x, w):
    from numpy.lib.stride_tricks import sliding_window_view
    out = np.full(len(x), np.nan)
    if len(x) >= w: out[w-1:] = sliding_window_view(x, w).max(1)
    return out

def detect(T,O,H,L,C, W, method="C2C", thresh=0.03, gap_ok=None):
    """Return indices where the +3% condition first becomes true (rising edge)."""
    n = len(C)
    if method == "C2C":
        ref = np.full(n, np.nan); ref[W:] = C[:-W]
        cond = (C/ref - 1.0) >= thresh
    elif method == "L2H":
        rl = rolling_min(L, W)
        cond = (H/rl - 1.0) >= thresh
    elif method == "O2H":
        ref = np.full(n, np.nan); ref[W:] = O[:-W]
        cond = (H/ref - 1.0) >= thresh
    else:
        raise ValueError(method)
    cond = np.nan_to_num(cond, nan=0).astype(bool)
    # rising edge only -- a continuously-true stretch is ONE crossing
    edge = cond.copy(); edge[1:] &= ~cond[:-1]
    idx = np.where(edge)[0]
    if gap_ok is not None:                      # drop events spanning a data gap
        idx = idx[gap_ok[idx]]
    return idx

def dedupe(idx, min_sep):
    """Keep the first event, then require min_sep minutes before the next."""
    if len(idx) == 0: return idx
    out = [idx[0]]
    for i in idx[1:]:
        if i - out[-1] >= min_sep: out.append(i)
    return np.array(out)

# ------------------------------------------------------------------ indicators
def ema(x, n):
    k = 2/(n+1); o = np.empty(len(x)); o[0] = x[0]
    for i in range(1, len(x)): o[i] = x[i]*k + o[i-1]*(1-k)
    return o

def wilder(x, p):
    o = np.full(len(x), np.nan)
    if len(x) <= p: return o
    s = x[:p].mean(); o[p-1] = s
    for i in range(p, len(x)): s = (s*(p-1)+x[i])/p; o[i] = s
    return o

def rsi(C, p=14):
    d = np.diff(C, prepend=C[0])
    up = wilder(np.clip(d,0,None), p); dn = wilder(-np.clip(d,None,0), p)
    return 100 - 100/(1 + up/np.where(dn==0,1e-12,dn))

def mfi(H,L,C,V, p=14):
    tp = (H+L+C)/3; mf = tp*V
    d = np.diff(tp, prepend=tp[0])
    pos = np.where(d>0, mf, 0.0); neg = np.where(d<0, mf, 0.0)
    from numpy.lib.stride_tricks import sliding_window_view
    o = np.full(len(C), np.nan)
    if len(C) >= p:
        ps = sliding_window_view(pos,p).sum(1); ns = sliding_window_view(neg,p).sum(1)
        o[p-1:] = 100 - 100/(1 + ps/np.where(ns==0,1e-12,ns))
    return o

def atr(H,L,C,p=14):
    pc = np.roll(C,1); pc[0]=C[0]
    tr = np.maximum(H-L, np.maximum(np.abs(H-pc), np.abs(L-pc)))
    return wilder(tr,p)
