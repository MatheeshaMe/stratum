#!/usr/bin/env python3
"""Binance spot 1m for additional symbols. Skips the sealed 2020-2022 window."""
import datetime as dt, io, os, pickle, sys, urllib.request, zipfile
from concurrent.futures import ThreadPoolExecutor
SEALED=(dt.date(2020,1,1), dt.date(2022,12,31))
def months(a,b):
    y,m=map(int,a.split("-")); Y,M=map(int,b.split("-"))
    while (y,m)<=(Y,M):
        yield f"{y:04d}-{m:02d}"
        m+=1
        if m==13: y,m=y+1,1
def fetch(sym,ym,cache):
    d=dt.date(int(ym[:4]),int(ym[5:]),1)
    if SEALED[0]<=d<=SEALED[1]: return []
    f=os.path.join(cache,f"{sym}-{ym}.pkl")
    if os.path.exists(f): return pickle.load(open(f,"rb"))
    u=f"https://data.binance.vision/data/spot/monthly/klines/{sym}/1m/{sym}-1m-{ym}.zip"
    try: raw=urllib.request.urlopen(u,timeout=180).read()
    except Exception: return []
    z=zipfile.ZipFile(io.BytesIO(raw)); out=[]
    for line in z.open(z.namelist()[0]).read().decode().splitlines():
        p=line.split(",")
        if not p[0].strip().strip('"').isdigit(): continue
        t=int(p[0])
        if t>1e14: t//=1000
        out.append((t,float(p[1]),float(p[2]),float(p[3]),float(p[4]),float(p[5]),int(float(p[8]))))
    pickle.dump(out,open(f,"wb")); return out
if __name__=="__main__":
    cache="data/.cache/alt"; os.makedirs(cache,exist_ok=True); os.makedirs("data/alt",exist_ok=True)
    for sym,start in (("ETHUSDT","2017-08"),("SOLUSDT","2023-01"),
                      ("XRPUSDT","2018-05"),("DOGEUSDT","2019-07")):
        yms=list(months(start,"2026-08"))
        with ThreadPoolExecutor(8) as ex: res=list(ex.map(lambda m: fetch(sym,m,cache), yms))
        rows=sorted([r for m in res for r in m])
        if not rows: print(f"{sym}: none"); continue
        pickle.dump(rows,open(f"data/alt/{sym}-1m.pkl","wb"))
        print(f"{sym}: {len(rows):,} bars "
              f"{dt.datetime.utcfromtimestamp(rows[0][0]/1000).date()} -> "
              f"{dt.datetime.utcfromtimestamp(rows[-1][0]/1000).date()}", flush=True)
