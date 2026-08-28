#!/usr/bin/env python3
"""Fetch BTCUSDT USD-M perp 1m klines from Binance Data Vision.

Free, no API key, no account. Monthly files where available, daily for the
current month. Verifies the published .CHECKSUM for every archive.

    python3 scripts/fetch_binance.py --from 2023-01 --to 2026-08
"""
import argparse, datetime as dt, hashlib, io, os, pickle, sys, urllib.request, zipfile

ROOT = "https://data.binance.vision/data/futures/um"

def _get(url, timeout=120):
    return urllib.request.urlopen(url, timeout=timeout).read()

def _verify(raw, url):
    """Binance publishes <file>.CHECKSUM containing 'sha256  filename'."""
    try:
        want = _get(url + ".CHECKSUM", timeout=30).decode().split()[0]
    except Exception:
        return None                      # checksum absent -> caller decides
    return hashlib.sha256(raw).hexdigest() == want

def _parse(raw):
    z = zipfile.ZipFile(io.BytesIO(raw))
    out = []
    for line in z.open(z.namelist()[0]).read().decode().splitlines():
        p = line.split(",")
        if not p[0].isdigit():           # some months carry a header row
            continue
        # openTime, o, h, l, c, volume, ..., numberOfTrades
        out.append((int(p[0]), float(p[1]), float(p[2]), float(p[3]),
                    float(p[4]), float(p[5]), int(float(p[8]))))
    return out

def fetch_month(sym, ym, cache):
    f = os.path.join(cache, f"{sym}-{ym}.pkl")
    if os.path.exists(f):
        return pickle.load(open(f, "rb")), "cached"
    url = f"{ROOT}/monthly/klines/{sym}/1m/{sym}-1m-{ym}.zip"
    try:
        raw = _get(url)
    except Exception:
        return None, "absent"
    ok = _verify(raw, url)
    if ok is False:
        raise SystemExit(f"CHECKSUM MISMATCH: {url}")
    rows = _parse(raw)
    pickle.dump(rows, open(f, "wb"))
    return rows, ("ok" if ok else "ok (no checksum published)")

def fetch_day(sym, day, cache):
    f = os.path.join(cache, f"{sym}-{day}.pkl")
    if os.path.exists(f):
        return pickle.load(open(f, "rb")), "cached"
    url = f"{ROOT}/daily/klines/{sym}/1m/{sym}-1m-{day}.zip"
    try:
        raw = _get(url, timeout=60)
    except Exception:
        return None, "absent"
    ok = _verify(raw, url)
    if ok is False:
        raise SystemExit(f"CHECKSUM MISMATCH: {url}")
    rows = _parse(raw)
    pickle.dump(rows, open(f, "wb"))
    return rows, ("ok" if ok else "ok (no checksum published)")

def months(a, b):
    y, m = map(int, a.split("-")); Y, M = map(int, b.split("-"))
    while (y, m) <= (Y, M):
        yield f"{y:04d}-{m:02d}"
        m += 1
        if m == 13: y, m = y + 1, 1

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="BTCUSDT")
    ap.add_argument("--from", dest="frm", default="2023-01")
    ap.add_argument("--to", dest="to", default=dt.date.today().strftime("%Y-%m"))
    ap.add_argument("--out", default="data/bars/venue=binance")
    ap.add_argument("--cache", default="data/.cache/binance")
    a = ap.parse_args()

    os.makedirs(a.cache, exist_ok=True)
    os.makedirs(a.out, exist_ok=True)
    rows = []

    for ym in months(a.frm, a.to):
        r, status = fetch_month(a.symbol, ym, a.cache)
        if r:
            rows += r
            print(f"  {ym}  {len(r):>6} bars  [{status}]")
            continue
        # monthly not published yet -> fall back to daily
        print(f"  {ym}  monthly absent, trying daily...")
        y, m = map(int, ym.split("-"))
        d = dt.date(y, m, 1)
        got = 0
        while d.month == m and d <= dt.date.today():
            r, _ = fetch_day(a.symbol, d.isoformat(), a.cache)
            if r:
                rows += r; got += len(r)
            d += dt.timedelta(days=1)
        print(f"  {ym}  {got:>6} bars  [daily]")

    if not rows:
        sys.exit("no data fetched")

    rows.sort()
    # gap report -- 1m bars should be contiguous
    gaps = [(rows[i-1][0], rows[i][0]) for i in range(1, len(rows))
            if rows[i][0] - rows[i-1][0] != 60_000]
    out = os.path.join(a.out, f"{a.symbol}-1m.pkl")
    pickle.dump(rows, open(out, "wb"))

    t0 = dt.datetime.utcfromtimestamp(rows[0][0] / 1000)
    t1 = dt.datetime.utcfromtimestamp(rows[-1][0] / 1000)
    print(f"\n{len(rows):,} 1m bars  {t0:%Y-%m-%d} -> {t1:%Y-%m-%d}")
    print(f"gaps: {len(gaps)}")
    for g in gaps[:10]:
        print(f"  {dt.datetime.utcfromtimestamp(g[0]/1000)} -> "
              f"{dt.datetime.utcfromtimestamp(g[1]/1000)}")
    print(f"written: {out}")

if __name__ == "__main__":
    main()
