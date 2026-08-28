"""Situation vector + triple-barrier outcome scanner for Stratum.

Labels every 5m close with a structural situation (ATR units, never dollars),
then measures what actually happened next using the triple-barrier method.

Design notes that matter:
  * Outcomes use TRIPLE BARRIERS (upper / lower / vertical) resolved on 1m bars.
    Same-bar ambiguity always resolves against you.
  * Barriers are in ATR units so a "situation" is comparable across regimes.
  * Every outcome is reported against the UNCONDITIONAL BASE RATE. A situation
    that matches the base rate contains no information, however clean its table.
"""
import math, numpy as np

# ---------------------------------------------------------------- aggregation
def agg(rows, mins):
    ms = mins * 60000
    t = np.array([r[0] for r in rows], dtype=np.int64)
    o = np.array([r[1] for r in rows]); h = np.array([r[2] for r in rows])
    l = np.array([r[3] for r in rows]); c = np.array([r[4] for r in rows])
    v = np.array([r[5] for r in rows]); n = np.array([r[6] for r in rows])
    key = t - (t % ms)
    _, start = np.unique(key, return_index=True)
    start = np.sort(start)
    end = np.append(start[1:], len(t))
    O = o[start]; C = c[end - 1]; T = key[start]
    H = np.maximum.reduceat(h, start); L = np.minimum.reduceat(l, start)
    V = np.add.reduceat(v, start); N = np.add.reduceat(n, start)
    return dict(t=T, o=O, h=H, l=L, c=C, v=V, n=N, i1m=start)

def wilder(x, p):
    out = np.full(len(x), np.nan)
    if len(x) <= p: return out
    s = x[:p].mean(); out[p-1] = s
    for i in range(p, len(x)):
        s = (s*(p-1) + x[i]) / p; out[i] = s
    return out

def atr14(b):
    h, l, c = b['h'], b['l'], b['c']
    pc = np.roll(c, 1); pc[0] = c[0]
    tr = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))
    return wilder(tr, 14)

def ema(x, n):
    k = 2/(n+1); out = np.empty(len(x)); out[0] = x[0]
    for i in range(1, len(x)): out[i] = x[i]*k + out[i-1]*(1-k)
    return out

def rsi14(c, p=14):
    d = np.diff(c, prepend=c[0])
    up = wilder(np.clip(d, 0, None), p); dn = wilder(-np.clip(d, None, 0), p)
    rs = up / np.where(dn == 0, 1e-12, dn)
    return 100 - 100/(1+rs)

# ------------------------------------------------------------------- levels
def level_series(b, A, L=3, R=3, cluster_atr=0.25, ttl=400, rebuild=4, min_band_bps=25):
    """As-of level store. Pivot at i is only knowable at i+R -- enforced."""
    h, l, c = b['h'], b['l'], b['c']
    n = len(c)
    swh = []; swl = []; CH = []; CL = []
    up = np.full(n, np.nan); dn = np.full(n, np.nan)
    upt = np.zeros(n, dtype=np.int32); dnt = np.zeros(n, dtype=np.int32)
    for i in range(60, n):
        a = A[i]
        if not np.isfinite(a): continue
        p = i - R
        if p > L:
            if h[p] == h[p-L:p+R+1].max(): swh.append((p, h[p]))
            if l[p] == l[p-L:p+R+1].min(): swl.append((p, l[p]))
        if i % rebuild == 0:
            band = max(cluster_atr*a, min_band_bps/1e4*c[i])   # COST-4 floor
            def bld(sws):
                out = []
                for ix, pr in sws[-300:]:
                    if i - ix > ttl: continue
                    hit = None
                    for cc in out:
                        if abs(pr - cc[0]) <= band: hit = cc; break
                    if hit:
                        hit[0] = (hit[0]*hit[1] + pr)/(hit[1]+1); hit[1] += 1
                        hit[2] = max(hit[2], ix)
                    else: out.append([pr, 1, ix])
                return out
            CH = bld(swh); CL = bld(swl)
        # nearest cluster above / below the current close
        a_up = [x for x in CH + CL if x[0] > c[i]]
        a_dn = [x for x in CH + CL if x[0] < c[i]]
        if a_up:
            x = min(a_up, key=lambda z: z[0] - c[i]); up[i] = x[0]; upt[i] = x[1]
        if a_dn:
            x = max(a_dn, key=lambda z: z[0] - c[i]); dn[i] = x[0]; dnt[i] = x[1]
    return up, dn, upt, dnt

# ------------------------------------------------------------ situation table
def situations(b, cfg=None):
    cfg = cfg or {}
    A = atr14(b); c = b['c']; h = b['h']; l = b['l']; v = b['v']
    ef = ema(c, 20); es = ema(c, 50)
    r = rsi14(c)
    vm = np.convolve(v, np.ones(20)/20, mode='full')[:len(v)]
    vsd = np.array([v[max(0,i-19):i+1].std() for i in range(len(v))])
    vz = (v - vm) / np.where(vsd == 0, 1e-12, vsd)
    up, dn, upt, dnt = level_series(b, A, **{k: cfg[k] for k in cfg if k in
                                    ('L','R','cluster_atr','ttl','rebuild','min_band_bps')})
    with np.errstate(invalid='ignore'):
        dist_up = (up - c) / A            # ATR to next cluster above
        dist_dn = (c - dn) / A            # ATR to next cluster below
        ext     = (c - ef) / A            # extension from fast EMA
    regime = np.where((c > ef) & (ef > es), 1, np.where((c < ef) & (ef < es), -1, 0))
    # structure: higher highs/lows over the last 20 bars vs the 20 before
    stru = np.zeros(len(c), dtype=np.int8)
    for i in range(40, len(c)):
        hh = h[i-20:i].max() > h[i-40:i-20].max()
        ll = l[i-20:i].min() > l[i-40:i-20].min()
        stru[i] = 1 if (hh and ll) else (-1 if (not hh and not ll) else 0)
    return dict(A=A, ema_f=ef, ema_s=es, rsi=r, vz=vz, up=up, dn=dn,
                up_touch=upt, dn_touch=dnt, dist_up=dist_up, dist_dn=dist_dn,
                ext=ext, regime=regime, stru=stru)

# ------------------------------------------------- triple barrier on 1m bars
def triple_barrier(rows, b, S, k_atr=2.0, horizon=12, side=+1, rr=1.0):
    """From each 5m close, first touch of +/- k*ATR or the vertical barrier.

    Resolved on 1m bars. Both barriers inside one 1m bar -> the LOSS.
    Returns 0=loss first, 1=win first, 2=vertical (still inside).
    """
    H1 = np.array([r[2] for r in rows]); L1 = np.array([r[3] for r in rows])
    i1 = b['i1m']; c = b['c']; A = S['A']; n = len(c)
    out = np.full(n, -1, dtype=np.int8)
    bars_to = np.full(n, -1, dtype=np.int32)
    for i in range(60, n - horizon - 1):
        a = A[i]
        if not np.isfinite(a): continue
        entry = c[i]; d = k_atr * a
        # target sits at rr * stop distance -- the label MUST match the payoff
        upb = entry + side*d*rr; lob = entry - side*d
        j0 = i1[i+1]; j1 = i1[min(i+1+horizon, n-1)]
        seg_h = H1[j0:j1]; seg_l = L1[j0:j1]
        if side > 0: win_hit = seg_h >= upb; los_hit = seg_l <= lob
        else:        win_hit = seg_l <= upb; los_hit = seg_h >= lob
        wi = np.argmax(win_hit) if win_hit.any() else 10**9
        li = np.argmax(los_hit) if los_hit.any() else 10**9
        if wi == 10**9 and li == 10**9: out[i] = 2; bars_to[i] = horizon
        elif li <= wi: out[i] = 0; bars_to[i] = li          # ties -> loss
        else:          out[i] = 1; bars_to[i] = wi
    return out, bars_to

# --------------------------------------------------------------- buckets
def buckets(b, S, touch_atr=0.30, near_atr=0.50):
    """B1..B6 per the product spec. One primary bucket per bar.
    Priority: B2 > B1 > B6 > B3 > B5 > B4."""
    c = b['c']; h = b['h']; l = b['l']; A = S['A']; n = len(c)
    du, dd = S['dist_up'], S['dist_dn']
    r = S['rsi']; reg = S['regime']; vz = S['vz']
    ut, dt_ = S['up_touch'], S['dn_touch']
    lab = np.zeros(n, dtype=np.int8)          # 0 = unclassified
    for i in range(60, n):
        if not np.isfinite(A[i]): continue
        at_res = np.isfinite(du[i]) and du[i] <= touch_atr
        at_sup = np.isfinite(dd[i]) and dd[i] <= touch_atr
        # B2 failed high: at resistance touched >=2x, weak volume, below fast EMA
        if at_res and ut[i] >= 2 and vz[i] < 0 and c[i] < S['ema_f'][i]: lab[i] = 2; continue
        # B1 underside retest: below a level that price recently closed under
        if at_res and reg[i] <= 0 and c[i] < S['ema_s'][i]: lab[i] = 1; continue
        # B6 accept break: two closes beyond, first pause
        if i > 2 and np.isfinite(dd[i]) and dd[i] > 1.5 and reg[i] > 0 \
           and c[i-1] > S['ema_f'][i-1] and c[i-2] > S['ema_f'][i-2]: lab[i] = 6; continue
        # B3 range low hold: at support, wick below, close back inside
        if at_sup and l[i] < (S['dn'][i] if np.isfinite(S['dn'][i]) else -1) \
           and c[i] > (S['dn'][i] if np.isfinite(S['dn'][i]) else 1e18): lab[i] = 3; continue
        # B5 stretch into shelf
        if (at_sup and r[i] < 35) or (at_res and r[i] > 65): lab[i] = 5; continue
        # B4 range mid: not near either wall
        if np.isfinite(du[i]) and np.isfinite(dd[i]) and du[i] > near_atr and dd[i] > near_atr:
            lab[i] = 4
    return lab

BUCKET_NAMES = {0:"unclassified", 1:"B1 underside_retest", 2:"B2 failed_high",
                3:"B3 range_low_hold", 4:"B4 range_mid",
                5:"B5 stretch_into_shelf", 6:"B6 accept_break"}
