#!/usr/bin/env python3
"""R-1 microstructure/positioning fetcher -- Binance USD-M BTCUSDT, free, no key.

EXPLORATORY WINDOW ONLY. Default 2023-01-01 .. today.
The sealed holdout (2020-01-01 .. 2022-12-31) is NOT fetched by this script and
must not be. See research/HYPOTHESIS_REGISTRY.md.

Datasets
  metrics      5m: open interest, top-trader long/short (accounts & positions),
               taker buy/sell volume ratio                      -> positioning
  bookDepth    30s: cumulative depth at +/-1..5% of mid          -> book pressure
  fundingRate  8h: realised funding                              -> carry/crowding
"""
import argparse, datetime as dt, io, os, pickle, sys, urllib.request, zipfile
from concurrent.futures import ThreadPoolExecutor

ROOT = "https://data.binance.vision/data/futures/um"
SEALED = (dt.date(2020,1,1), dt.date(2022,12,31))

def guard(d):
    if SEALED[0] <= d <= SEALED[1]:
        sys.exit(f"REFUSED: {d} is inside the sealed holdout {SEALED[0]}..{SEALED[1]}")

def get(url, timeout=120):
    try: return urllib.request.urlopen(url, timeout=timeout).read()
    except Exception: return None

def days(a, b):
    d = a
    while d <= b:
        yield d; d += dt.timedelta(days=1)

# ---------------------------------------------------------------- metrics
def metrics_day(day, cache):
    f = os.path.join(cache, f"m-{day}.pkl")
    if os.path.exists(f): return pickle.load(open(f,"rb"))
    raw = get(f"{ROOT}/daily/metrics/BTCUSDT/BTCUSDT-metrics-{day}.zip", 60)
    if raw is None: return []
    z = zipfile.ZipFile(io.BytesIO(raw)); out = []
    for line in z.open(z.namelist()[0]).read().decode().splitlines():
        p = line.split(",")
        if p[0].startswith("create"): continue
        try:
            ts = int(dt.datetime.strptime(p[0], "%Y-%m-%d %H:%M:%S")
                     .replace(tzinfo=dt.timezone.utc).timestamp()*1000)
            out.append((ts, float(p[2]), float(p[3]), float(p[4]),
                        float(p[5]), float(p[6]), float(p[7])))
        except Exception: continue
    pickle.dump(out, open(f,"wb")); return out

# -------------------------------------------------------------- bookDepth
def depth_day(day, cache):
    """Aggregate 30s snapshots -> 5m buckets, mean notional per level."""
    f = os.path.join(cache, f"d-{day}.pkl")
    if os.path.exists(f): return pickle.load(open(f,"rb"))
    raw = get(f"{ROOT}/daily/bookDepth/BTCUSDT/BTCUSDT-bookDepth-{day}.zip", 120)
    if raw is None: return []
    z = zipfile.ZipFile(io.BytesIO(raw))
    acc = {}
    for line in z.open(z.namelist()[0]).read().decode().splitlines():
        p = line.split(",")
        if p[0].startswith("time"): continue
        try:
            ts = int(dt.datetime.strptime(p[0], "%Y-%m-%d %H:%M:%S")
                     .replace(tzinfo=dt.timezone.utc).timestamp()*1000)
            lvl = int(p[1]); ntl = float(p[3])
        except Exception: continue
        k = ts - (ts % 300000)
        a = acc.setdefault(k, {})
        s = a.setdefault(lvl, [0.0, 0])
        s[0] += ntl; s[1] += 1
    out = []
    for k in sorted(acc):
        a = acc[k]
        if len(a) < 10: continue
        row = [k] + [a[l][0]/a[l][1] for l in (-1,-2,-3,-4,-5,1,2,3,4,5)]
        out.append(tuple(row))
    pickle.dump(out, open(f,"wb")); return out

# ------------------------------------------------------------ fundingRate
def funding_month(ym, cache):
    f = os.path.join(cache, f"f-{ym}.pkl")
    if os.path.exists(f): return pickle.load(open(f,"rb"))
    raw = get(f"{ROOT}/monthly/fundingRate/BTCUSDT/BTCUSDT-fundingRate-{ym}.zip", 60)
    if raw is None: return []
    z = zipfile.ZipFile(io.BytesIO(raw)); out = []
    for line in z.open(z.namelist()[0]).read().decode().splitlines():
        p = line.split(",")
        if not p[0].strip().isdigit(): continue
        out.append((int(p[0]), float(p[2])))
    pickle.dump(out, open(f,"wb")); return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="frm", default="2023-01-01")
    ap.add_argument("--to", dest="to", default=dt.date.today().isoformat())
    ap.add_argument("--out", default="data/micro")
    ap.add_argument("--cache", default="data/.cache/micro")
    ap.add_argument("--workers", type=int, default=12)
    a = ap.parse_args()
    d0 = dt.date.fromisoformat(a.frm); d1 = dt.date.fromisoformat(a.to)
    guard(d0); guard(d1)
    os.makedirs(a.out, exist_ok=True); os.makedirs(a.cache, exist_ok=True)
    dl = [d.isoformat() for d in days(d0, d1)]
    print(f"exploratory window {d0} .. {d1}  ({len(dl)} days)")
    print(f"sealed holdout {SEALED[0]} .. {SEALED[1]}  NOT FETCHED")

    with ThreadPoolExecutor(a.workers) as ex:
        met = list(ex.map(lambda d: metrics_day(d, a.cache), dl))
    M = sorted([r for day in met for r in day])
    print(f"  metrics    {len(M):>8,} rows  ({sum(1 for d in met if d)}/{len(dl)} days)")
    pickle.dump(M, open(os.path.join(a.out,"metrics.pkl"),"wb"))

    with ThreadPoolExecutor(a.workers) as ex:
        dep = list(ex.map(lambda d: depth_day(d, a.cache), dl))
    D = sorted([r for day in dep for r in day])
    print(f"  bookDepth  {len(D):>8,} 5m rows ({sum(1 for d in dep if d)}/{len(dl)} days)")
    pickle.dump(D, open(os.path.join(a.out,"bookdepth.pkl"),"wb"))

    yms = sorted({d[:7] for d in dl})
    with ThreadPoolExecutor(6) as ex:
        fu = list(ex.map(lambda m: funding_month(m, a.cache), yms))
    F = sorted([r for m in fu for r in m])
    print(f"  funding    {len(F):>8,} rows")
    pickle.dump(F, open(os.path.join(a.out,"funding.pkl"),"wb"))

if __name__ == "__main__":
    main()
