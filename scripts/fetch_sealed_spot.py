#!/usr/bin/env python3
"""ONE-TIME: fetch spot BTCUSDT for the sealed 2020-2022 window.
Run only when a hypothesis has been frozen in writing."""
import datetime as dt, io, os, pickle, urllib.request, zipfile
from concurrent.futures import ThreadPoolExecutor
ROOT="https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1m"
def fetch(ym,cache):
    f=os.path.join(cache,f"s-{ym}.pkl")
    if os.path.exists(f): return pickle.load(open(f,"rb"))
    try: raw=urllib.request.urlopen(f"{ROOT}/BTCUSDT-1m-{ym}.zip",timeout=180).read()
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
    cache="data/.cache/spot"; os.makedirs(cache,exist_ok=True)
    yms=[f"{y}-{m:02d}" for y in (2020,2021,2022) for m in range(1,13)]
    with ThreadPoolExecutor(8) as ex: res=list(ex.map(lambda m: fetch(m,cache), yms))
    rows=sorted([r for m in res for r in m])
    pickle.dump(rows,open("data/sealed_spot/BTCUSDT-1m.pkl","wb"))
    print(f"{len(rows):,} bars {dt.datetime.utcfromtimestamp(rows[0][0]/1000).date()} -> "
          f"{dt.datetime.utcfromtimestamp(rows[-1][0]/1000).date()}")
