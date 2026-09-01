#!/usr/bin/env python3
"""Phase 7 — ABLATION. Does the hierarchy actually stack?

The trader model says context compounds: regime, then location, then liquidity,
then approach. If that is true, EV should rise monotonically T0 -> T5 while n
falls. If EV is flat while n collapses, the context is costing sample without
buying information -- which is the signature of a story rather than a signal.
"""
import sys, os, pickle, numpy as np
sys.path.insert(0,'research/trader'); sys.path.insert(0,'research/btc3')
from run_discovery import run, boot, DISC, VALD, HELD

LADDER=["T0","T1","T2","T3","T4","T5","R1"]
NAMES={"T0":"zone alone","T1":"+ HTF regime aligned","T2":"+ HTF location (disc/prem)",
       "T3":"+ liquidity swept","T4":"+ decelerating approach","T5":"+ zone broke structure",
       "R1":"reversal at HTF extreme"}
D=pickle.load(open("/tmp/trader_disc.pkl","rb"))
print("PHASE 7 — ABLATION LADDER on DISCOVERY (BTC 1h)\n")
for entry,man in (("A","fix2"),("A","fix3"),("B","fix3"),("A","trailS")):
    print(f"  entry {entry}, management {man}")
    print(f"    {'thesis':<32}{'n':>6}{'win%':>7}{'EV R':>9}{'  95% CI':>22}{'PF':>7}{'dEV':>8}")
    prev=None
    for t in LADDER:
        M=D.get((t,entry,man))
        if M is None or len(M)<30:
            print(f"    {NAMES[t]:<32}{0 if M is None else len(M):>6}  too few"); continue
        R=M[:,0]; w=R>0; lo,hi=boot(R)
        d=(R.mean()-prev) if (prev is not None and t!="R1") else np.nan
        pf=R[w].sum()/max(-R[~w].sum(),1e-9)
        print(f"    {NAMES[t]:<32}{len(R):>6}{w.mean():>7.1%}{R.mean():>+9.3f}"
              f"   [{lo:+.3f},{hi:+.3f}]{pf:>7.2f}"
              f"{('  '+format(d,'+.3f')) if np.isfinite(d) else '':>8}")
        if t!="R1": prev=R.mean()
    print()

print("="*100)
print("VALIDATION 2022-01 .. 2024-12 — does anything survive?")
print("="*100)
V=run("data/spot/BTCUSDT-1m-full.pkl",*VALD)
pickle.dump(V,open("/tmp/trader_vald.pkl","wb"))
print(f"{'thesis':<6}{'entry':<7}{'mgmt':<9}{'disc EV':>10}{'disc n':>8}"
      f"{'valid EV':>11}{'valid n':>9}{'  valid 95% CI':>24}{'  sign held':>12}")
cand=[]
for k,M in sorted(D.items()):
    if len(M)<150: continue
    ed=M[:,0].mean()
    if ed<=0: continue
    MV=V.get(k)
    if MV is None or len(MV)<80:
        print(f"{k[0]:<6}{k[1]:<7}{k[2]:<9}{ed:>+10.3f}{len(M):>8}{'--':>11}{0 if MV is None else len(MV):>9}")
        continue
    R=MV[:,0]; lo,hi=boot(R)
    held = "YES" if R.mean()>0 else "no"
    print(f"{k[0]:<6}{k[1]:<7}{k[2]:<9}{ed:>+10.3f}{len(M):>8}{R.mean():>+11.3f}{len(R):>9}"
          f"   [{lo:+.3f},{hi:+.3f}]{held:>12}")
    if R.mean()>0: cand.append((k,ed,R.mean(),lo,hi,len(R)))
print(f"\ncandidates surviving discovery(n>=150, EV>0) AND validation sign: {len(cand)}")
for c in cand: print("   ",c[0],f"disc {c[1]:+.3f}  valid {c[2]:+.3f}  CI [{c[3]:+.3f},{c[4]:+.3f}]  n={c[5]}")
pickle.dump(cand,open("/tmp/trader_cand.pkl","wb"))
