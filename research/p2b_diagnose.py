#!/usr/bin/env python3
"""Is the mildly-positive gross R at wide stops an EDGE or just DRIFT?

Decisive test: an edge is direction-agnostic structure. Drift is not.
  - If LONG gross R is positive and SHORT is the mirror image, it is drift.
  - If a bucket beats the UNCONDITIONAL baseline on both sides, it is structure.
Everything is measured against the unconditional 'every bar' baseline, which is
the only honest control.
"""
import sys, os, pickle, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import situations as S
from p2_surface import realised_R, block_ci, COSTS

def diagnose(rows, tag):
    b = S.agg(rows,5); st = S.situations(b); lab = S.buckets(b,st)
    realised_R.H1 = np.array([r[2] for r in rows])
    realised_R.L1 = np.array([r[3] for r in rows])
    realised_R.C1 = np.array([r[4] for r in rows])
    c = b['c']; A = st['A']
    # period drift, for reference
    yrs = (b['t'][-1]-b['t'][0])/(365.25*86400*1000)
    drift = (c[-1]/c[0])**(1/yrs) - 1
    print(f"\n{'='*104}\n{tag}   BTC {c[0]:,.0f} -> {c[-1]:,.0f} over {yrs:.2f}y "
          f"= {drift:+.1%}/yr annualised drift\n{'='*104}")
    print(f"{'config':<34}{'n':>8}{'LONG gross':>12}{'SHORT gross':>13}"
          f"{'sum(L+S)':>11}{'  interpretation':>18}")
    for k, rr in ((7,1.5),(14,1.5),(14,3.0),(20,1.5),(20,3.0)):
        hz = int(max(36, 4*k*k))
        stop_pct = k*A/c
        RL,uL = realised_R(rows,b,st,k,hz,+1,rr)
        RS,uS = realised_R(rows,b,st,k,hz,-1,rr)
        okm = np.isfinite(RL)&np.isfinite(RS)&(stop_pct>=0.006)&(stop_pct<=0.05)
        for bid, nm in [(None,"ALL BARS (baseline)")] + [(x,S.BUCKET_NAMES[x][:20]) for x in (1,2,4,6)]:
            m = okm if bid is None else (okm & (lab==bid))
            if m.sum() < 150: continue
            gl, gs = RL[m].mean(), RS[m].mean()
            tot = gl+gs
            # a real edge shows as one side >> baseline; drift shows as gl = -gs
            interp = "drift (L=-S)" if abs(tot) < 0.02 else ("net long bias" if tot>0 else "net short bias")
            print(f"  k={k:<3}rr={rr:<4}{nm:<22}{m.sum():>8}{gl:>+12.3f}{gs:>+13.3f}"
                  f"{tot:>+11.3f}   {interp}")
        print()

    # the only comparison that matters: bucket MINUS baseline, same side
    print(f"\n  EXCESS over the unconditional baseline (this is the edge, if any)")
    print(f"  {'config':<30}{'bucket':<22}{'side':<7}{'excess R':>10}{'  95% CI':>22}")
    for k, rr in ((14,1.5),(14,3.0),(20,3.0)):
        hz = int(max(36, 4*k*k)); stop_pct = k*A/c
        for side in (+1,-1):
            R,_ = realised_R(rows,b,st,k,hz,side,rr)
            okm = np.isfinite(R)&(stop_pct>=0.006)&(stop_pct<=0.05)
            base = R[okm].mean()
            for bid in (1,2,3,4,6):
                m = okm & (lab==bid)
                if m.sum() < 150: continue
                ex = R[m].mean() - base
                lo,hi = block_ci(R[m]-base, block=min(hz,60))
                sig = "  <<<" if lo>0 or hi<0 else ""
                print(f"  k={k} rr={rr:<4}{'':<18}{S.BUCKET_NAMES[bid][:20]:<22}"
                      f"{'LONG' if side>0 else 'SHORT':<7}{ex:>+10.3f}"
                      f"   [{lo:+.3f},{hi:+.3f}]{sig}")

if __name__ == "__main__":
    diagnose(pickle.load(open("data/is/BTCUSDT-1m.pkl","rb")), "EXPLORE 2025-01..2026-07")
