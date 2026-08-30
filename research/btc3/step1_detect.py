#!/usr/bin/env python3
"""Step 1 -- detect +3% events under every definition, compare, choose."""
import sys, os, pickle, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import events as E

T,O,H,L,C,V,N = E.load("data/spot/BTCUSDT-1m.pkl")
n = len(C)
print(f"BTCUSDT spot 1m: {n:,} bars  "
      f"{np.datetime64(int(T[0]),'ms')} -> {np.datetime64(int(T[-1]),'ms')}")
gaps = np.where(np.diff(T) != 60000)[0]
print(f"data gaps: {len(gaps)}  (largest {np.diff(T)[gaps].max()/60000:.0f} minutes)\n")

def valid_lookback(W):
    v = np.zeros(n, bool)
    v[W:] = (T[W:] - T[:-W]) == W*60000
    return v

rows=[]
print(f"{'window':<8}{'method':<7}{'raw':>8}{'sep=W':>9}{'sep=24h':>9}"
      f"{'per year':>10}{'  median gap between events':>28}")
for wl, W in E.WINDOWS.items():
    vb = valid_lookback(W)
    for meth in ("C2C","L2H","O2H"):
        idx = E.detect(T,O,H,L,C,W,method=meth,gap_ok=vb)
        d1 = E.dedupe(idx, W); d2 = E.dedupe(idx, 1440)
        yrs = (T[-1]-T[0])/(365.25*86400*1000)
        med = np.median(np.diff(d2))/1440 if len(d2)>2 else np.nan
        print(f"{wl:<8}{meth:<7}{len(idx):>8,}{len(d1):>9,}{len(d2):>9,}"
              f"{len(d2)/yrs:>10.1f}{med:>22.1f} days")
        rows.append((wl,W,meth,idx,d1,d2))
pickle.dump({(r[0],r[2]):(r[1],r[3],r[4],r[5]) for r in rows},
            open("/tmp/btc3_events.pkl","wb"))

print("\nHow much do the three measurement methods overlap? (window = 1h, sep=24h)")
sets = {}
for wl,W,meth,idx,d1,d2 in rows:
    if wl!="1h": continue
    sets[meth]=set(d2)
for a in ("C2C","L2H","O2H"):
    for b in ("C2C","L2H","O2H"):
        if a>=b: continue
        # count b-events within 60 min of an a-event
        A=np.array(sorted(sets[a])); B=np.array(sorted(sets[b]))
        near=sum(1 for x in B if len(A) and np.min(np.abs(A-x))<=60)
        print(f"  {b:>4} events within 60m of a {a:<4} event: {near}/{len(B)} = {near/len(B):.0%}")
