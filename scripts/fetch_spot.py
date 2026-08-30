#!/usr/bin/env python3
"""Binance SPOT BTCUSDT 1m klines. Free, no key. Skips the sealed window."""
import datetime as dt, hashlib, io, os, pickle, sys, urllib.request, zipfile
from concurrent.futures import ThreadPoolExecutor
ROOT="https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1m"
SEALED=(dt.date(2020,1,1), dt.date(2022,12,31))
def months(a,b):
    y,m=map(int,a.split("-")); Y,M=map(int,b.split("-"))
    while (y,m)<=(Y,M):
        yield f"{y:04d}-{m:02d}"
        m+=1
        if m==13: y,m=y+1,1
def fetch(ym, cache):
    d=dt.date(int(ym[:4]),int(ym[5:]),1)
    if SEALED[0]<=d<=SEALED[1]: return ("SEALED",[])
    f=os.path.join(cache,f"s-{ym}.pkl")
    if os.path.exists(f): return ("cached",pickle.load(open(f,"rb")))
    try: raw=urllib.request.urlopen(f"{ROOT}/BTCUSDT-1m-{ym}.zip",timeout=180).read()
    except Exception: return ("absent",[])
    try:
        want=urllib.request.urlopen(f"{ROOT}/BTCUSDT-1m-{ym}.zip.CHECKSUM",timeout=30).read().decode().split()[0]
        if hashlib.sha256(raw).hexdigest()!=want: sys.exit(f"CHECKSUM MISMATCH {ym}")
    except SystemExit: raise
    except Exception: pass
    z=zipfile.ZipFile(io.BytesIO(raw)); out=[]
    for line in z.open(z.namelist()[0]).read().decode().splitlines():
        p=line.split(",")
        if not p[0].strip().strip('"').isdigit(): continue
        t=int(p[0])
        if t>1e14: t//=1000                       # some months ship microseconds
        out.append((t,float(p[1]),float(p[2]),float(p[3]),float(p[4]),
                    float(p[5]),int(float(p[8]))))
    pickle.dump(out,open(f,"wb")); return ("ok",out)
if __name__=="__main__":
    cache="data/.cache/spot"; os.makedirs(cache,exist_ok=True); os.makedirs("data/spot",exist_ok=True)
    yms=list(months("2017-08","2026-08"))
    with ThreadPoolExecutor(8) as ex: res=list(ex.map(lambda m: fetch(m,cache), yms))
    rows=[]; skipped=[]
    for ym,(status,r) in zip(yms,res):
        if status=="SEALED": skipped.append(ym); continue
        rows+=r
    rows.sort()
    pickle.dump(rows,open("data/spot/BTCUSDT-1m.pkl","wb"))
    print(f"{len(rows):,} 1m spot bars")
    print(f"range {dt.datetime.utcfromtimestamp(rows[0][0]/1000)} -> "
          f"{dt.datetime.utcfromtimestamp(rows[-1][0]/1000)}")
    print(f"sealed months skipped: {len(skipped)} ({skipped[0]}..{skipped[-1]})")
    gaps=sum(1 for i in range(1,len(rows)) if rows[i][0]-rows[i-1][0]!=60000)
    print(f"non-contiguous joins: {gaps} (expect ~1 at the sealed-window seam)")
