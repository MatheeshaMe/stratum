"""R-1 microstructure / positioning features, aligned to the 5m situation grid.

DISCIPLINE
  * Every microstructure series is LAGGED BY ONE 5m BAR before use. The raw
    metrics/bookDepth timestamps are snapshots whose exact intra-bar placement
    is not guaranteed; lagging removes any possibility of reading data from
    inside the bar we are trying to predict. This costs information and is the
    correct trade.
  * Nothing here touches the sealed 2020-2022 window.

FAMILIES
  OI      level, delta(1/6/36), acceleration, and the OI x price interaction
          (new longs / short covering / new shorts / long liquidation)
  FLOW    taker buy/sell volume ratio and its z-score  (aggressive flow)
  POSN    top-trader long/short ratio by account count and by position size
  BOOK    cumulative depth imbalance at +/-1%, 2%, 5%; depth deltas; total depth
  CARRY   funding rate, funding z-score, funding delta
"""
import numpy as np, pickle

def _align(ts_grid, rows, ncol):
    """Merge an irregular series onto the 5m grid, forward-fill, then LAG 1 bar."""
    if not rows: return np.full((len(ts_grid), ncol), np.nan)
    src_ts = np.array([r[0] for r in rows], dtype=np.int64)
    src = np.array([r[1:1+ncol] for r in rows], dtype=float)
    idx = np.searchsorted(src_ts, ts_grid, side="right") - 1   # last value AT or BEFORE
    out = np.full((len(ts_grid), ncol), np.nan)
    ok = idx >= 0
    out[ok] = src[idx[ok]]
    out[1:] = out[:-1]; out[0] = np.nan                        # LAG one 5m bar
    return out

def _z(x, w=288):
    out = np.full(len(x), np.nan)
    for i in range(w, len(x)):
        s = x[i-w:i]
        m, sd = np.nanmean(s), np.nanstd(s)
        out[i] = (x[i]-m)/sd if sd > 0 else 0.0
    return out

def _d(x, k):
    out = np.full(len(x), np.nan); out[k:] = x[k:] - x[:-k]; return out

def build(b, micro_dir="data/micro"):
    """b = 5m bar dict from situations.agg. Returns (X, names)."""
    ts = b['t']; c = b['c']; n = len(ts)
    M = pickle.load(open(f"{micro_dir}/metrics.pkl","rb"))
    D = pickle.load(open(f"{micro_dir}/bookdepth.pkl","rb"))
    F = pickle.load(open(f"{micro_dir}/funding.pkl","rb"))

    m = _align(ts, M, 6)     # oi, oi_val, tt_cnt_ls, tt_sum_ls, cnt_ls, taker_ls
    d = _align(ts, D, 10)    # bid1..bid5, ask1..ask5 (notional)
    f = _align(ts, [(r[0], r[1]) for r in F], 1)[:,0]

    oi      = m[:,0].copy(); oi[oi <= 0] = np.nan     # exchange reports 0 on outages
    tt_cnt  = m[:,2].copy(); tt_sum = m[:,3].copy()
    cnt_ls  = m[:,4].copy(); taker  = m[:,5].copy()
    for _v in (tt_cnt, tt_sum, cnt_ls, taker): _v[_v <= 0] = np.nan
    bid = d[:,0:5]; ask = d[:,5:10]

    ret1  = np.concatenate([[np.nan], np.diff(c)/c[:-1]])
    ret6  = np.concatenate([[np.nan]*6, (c[6:]-c[:-6])/c[:-6]])

    def imb(k):
        bb, aa = bid[:,k], ask[:,k]
        s = bb+aa
        return np.where(s>0, (bb-aa)/np.where(s==0,1,s), np.nan)

    feats, names = [], []
    def add(v, nm): feats.append(np.asarray(v, dtype=float)); names.append(nm)

    # --- OI -------------------------------------------------------------
    add(_z(oi), "oi_z")
    for k in (1,6,36):
        add(_d(oi,k)/np.where(oi==0,np.nan,oi)*100, f"oi_d{k}_pct")
    add(_d(_d(oi,6),6)/np.where(oi==0,np.nan,oi)*100, "oi_accel_pct")
    # the positioning read OHLCV cannot see
    oid6 = _d(oi,6)/np.where(oi==0,np.nan,oi)
    add(np.sign(ret6)*np.sign(oid6), "oi_price_regime")   # +1 new positions, -1 covering
    add(ret6*oid6*1e4, "oi_price_interact")
    add(np.where((ret6>0)&(oid6>0), 1.0, 0.0), "new_longs")
    add(np.where((ret6>0)&(oid6<0), 1.0, 0.0), "short_cover")
    add(np.where((ret6<0)&(oid6>0), 1.0, 0.0), "new_shorts")
    add(np.where((ret6<0)&(oid6<0), 1.0, 0.0), "long_liq")

    # --- FLOW -----------------------------------------------------------
    add(taker, "taker_ls_ratio")
    add(np.log(np.where(taker>0, taker, np.nan)), "taker_ls_log")
    add(_z(taker), "taker_ls_z")
    add(_d(taker,6), "taker_ls_d6")

    # --- POSITIONING ----------------------------------------------------
    add(tt_cnt, "toptrader_cnt_ls"); add(_z(tt_cnt), "toptrader_cnt_ls_z")
    add(tt_sum, "toptrader_sum_ls"); add(_z(tt_sum), "toptrader_sum_ls_z")
    add(_d(tt_sum,36), "toptrader_sum_ls_d36")
    add(cnt_ls, "global_cnt_ls"); add(_z(cnt_ls), "global_cnt_ls_z")
    add(tt_sum - cnt_ls, "smart_dumb_spread")     # top traders vs the crowd

    # --- BOOK -----------------------------------------------------------
    for k, lbl in ((0,"1pct"),(1,"2pct"),(4,"5pct")):
        v = imb(k); add(v, f"book_imb_{lbl}"); add(_z(v), f"book_imb_{lbl}_z")
        add(_d(v,6), f"book_imb_{lbl}_d6")
    tot = bid.sum(1)+ask.sum(1)
    add(_z(tot), "book_depth_z")
    add(_d(tot,6)/np.where(tot==0,np.nan,tot), "book_depth_d6")
    add(imb(0)-imb(4), "book_imb_slope")          # near-vs-far book tilt

    # --- CARRY ----------------------------------------------------------
    add(f*1e4, "funding_bps"); add(_z(f), "funding_z"); add(_d(f,96)*1e4, "funding_d96")

    X = np.column_stack(feats)
    return X, names
