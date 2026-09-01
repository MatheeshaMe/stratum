#!/usr/bin/env python3
"""Distribution audit, then the HELD-OUT test (touched once), then cross-asset."""
import sys, os, pickle, numpy as np, itertools
sys.path.insert(0,'research/trader'); sys.path.insert(0,'research/btc3')
from run_discovery import run, boot, DISC, VALD, HELD

D=pickle.load(open("/tmp/trader_disc.pkl","rb"))
V=pickle.load(open("/tmp/trader_vald.pkl","rb"))
print("DISTRIBUTION AUDIT — are the trailing-exit results carried by a few trades?\n")
print(f"{'cell':<22}{'set':<7}{'n':>6}{'EV':>8}{'top1 share':>12}{'top3 share':>12}"
      f"{'EV ex-top3':>12}{'max R':>8}{'medR':>8}")
for k in [("T1","A","trailS"),("T0","A","trailS"),("T1","A","fix3"),("T0","A","fix2")]:
    for lbl,S in (("disc",D),("valid",V)):
        M=S.get(k)
        if M is None or len(M)<50: continue
        R=np.sort(M[:,0])[::-1]
        tot=R.sum(); ex3=R[3:].mean()
        print(f"{'/'.join(k):<22}{lbl:<7}{len(R):>6}{R.mean():>+8.3f}"
              f"{R[0]/max(tot,1e-9):>11.0%}{R[:3].sum()/max(tot,1e-9):>12.0%}"
              f"{ex3:>+12.3f}{R[0]:>8.1f}{np.median(R):>+8.3f}")

print("\n" + "="*104)
print("HELD OUT 2025-01 .. 2026-07 — opened once, no tuning after this point")
print("="*104)
H=run("data/spot/BTCUSDT-1m-full.pkl",*HELD)
pickle.dump(H,open("/tmp/trader_held.pkl","wb"))
cand=pickle.load(open("/tmp/trader_cand.pkl","rb"))
print(f"{'thesis/entry/mgmt':<24}{'disc EV':>9}{'valid EV':>10}{'HELD n':>8}"
      f"{'HELD EV':>10}{'  95% CI':>22}{'  verdict':>10}")
passed=[]
for k,ed,vd,_,_,_ in cand:
    M=H.get(k)
    if M is None or len(M)<50:
        print(f"{'/'.join(k):<24}{ed:>+9.3f}{vd:>+10.3f}{0 if M is None else len(M):>8}"
              f"{'--':>10}{'':>22}{'too few':>10}")
        continue
    R=M[:,0]; lo,hi=boot(R)
    v="PASS" if lo>0 else ("sign ok" if R.mean()>0 else "FAIL")
    if lo>0: passed.append(k)
    print(f"{'/'.join(k):<24}{ed:>+9.3f}{vd:>+10.3f}{len(R):>8}{R.mean():>+10.3f}"
          f"   [{lo:+.3f},{hi:+.3f}]{v:>10}")
print(f"\nheld-out cells with CI above zero: {len(passed)} of {len(cand)}")

print("\n" + "="*104)
print("CROSS-ASSET — full period, structure transferred without retuning")
print("="*104)
ASSETS=[("ETH","data/alt/ETHUSDT-1m.pkl"),("SOL","data/alt/SOLUSDT-1m.pkl"),
        ("XRP","data/alt/XRPUSDT-1m.pkl"),("DOGE","data/alt/DOGEUSDT-1m.pkl")]
KEYS=[("T1","A","fix3"),("T1","A","fix2"),("T0","A","fix2"),("T1","A","trailS")]
print(f"{'asset':<8}" + "".join(f"{'/'.join(k):>24}" for k in KEYS))
pool={k:[] for k in KEYS}
for sym,p in ASSETS:
    if not os.path.exists(p): continue
    Ra=run(p,0,10**15)
    row=f"{sym:<8}"
    for k in KEYS:
        M=Ra.get(k)
        if M is None or len(M)<80: row+=f"{'--':>24}"; continue
        R=M[:,0]; lo,hi=boot(R); pool[k].append(R)
        row+=f"{R.mean():>+9.3f} n={len(R):<4}{'*' if lo>0 else ' ':>2}      "[:24]
    print(row)
print()
for k in KEYS:
    if not pool[k]: continue
    R=np.concatenate(pool[k]); lo,hi=boot(R)
    print(f"  POOLED alts {'/'.join(k):<20} n={len(R):>5}  EV {R.mean():>+7.3f}  "
          f"CI [{lo:+.3f},{hi:+.3f}]{'  <<<' if lo>0 else ''}")
