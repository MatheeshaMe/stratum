#!/usr/bin/env python3
"""R-3 -- measure the deviation-from-martingale surface, then condition on states.

Step 1  UNCONDITIONAL. For every (stop, target, horizon) cell measure
        P(target first | resolved) and compare with the martingale value
        S/(S+T). The DEVIATION is the only place an edge can live.
Step 2  Net EV per cell, cost inside the search, three execution scenarios.
"""
import sys, os, pickle, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r3_paths as P

COST = {"maker/maker":0.030/100, "maker/taker":0.0663/100, "taker/taker":0.1026/100}

def main(path="data/explore_r1.pkl", stride=5):
    rows = pickle.load(open(path,"rb"))
    n1 = len(rows)
    entry = np.arange(60, n1 - P.HMAX - 2, stride)
    print(f"R-3 path surface: {len(entry):,} entries "
          f"(every {stride}m over {n1:,} 1m bars, 2023-01..2026-07, non-sealed)")
    out = {}
    for side, sname in ((+1,"LONG"), (-1,"SHORT")):
        tp, sl = P.first_passage(rows, entry, side=side)
        out[sname] = (tp, sl)
        print(f"\n{'='*112}\n{sname}: P(target first | resolved) MINUS martingale S/(S+T),"
              f" in probability points\n{'='*112}")
        for hz in (30, 120):
            print(f"\n  horizon {hz}m")
            hdr = "stop / target"
            print(f"  {hdr:<14}" + "".join(f"{t*100:>8.2f}%" for t in P.TARGETS))
            for si, s in enumerate(P.STOPS):
                row = f"  {s*100:>6.2f}%{'':<7}"
                for ti, t in enumerate(P.TARGETS):
                    a = tp[:, ti]; b = sl[:, si]
                    w = (a <= hz) & (a < b); l = (b <= hz) & ~w
                    res = w | l
                    if res.sum() < 500: row += f"{'-':>8}"; continue
                    p = w.sum()/res.sum()
                    dev = (p - s/(s+t))*100
                    row += f"{dev:>+8.2f}"
                print(row)
        mo = {hz: P.markout(rows, entry, hz) for hz in P.HORIZONS}
        print(f"\n  NET EV per trade (% of notional), maker/taker, horizon 120m")
        hdr = "stop / target"
        print(f"  {hdr:<14}" + "".join(f"{t*100:>8.2f}%" for t in P.TARGETS))
        best = None
        for si, s in enumerate(P.STOPS):
            row = f"  {s*100:>6.2f}%{'':<7}"
            for ti, t in enumerate(P.TARGETS):
                w,l,u,r = P.score_cell(tp, sl, mo[120], si, ti, 120, side,
                                        s, t, COST["maker/taker"])
                ev = r.mean()*100
                row += f"{ev:>+8.4f}"
                if best is None or ev > best[0]: best = (ev, s, t, w.mean(), u.mean())
            print(row)
        print(f"  best cell: EV {best[0]:+.4f}%  stop {best[1]*100:.2f}% "
              f"target {best[2]*100:.2f}%  P(win) {best[3]:.1%}  unresolved {best[4]:.1%}")
    pickle.dump({k:(v[0],v[1]) for k,v in out.items()}, open("/tmp/r3_fp.pkl","wb"))
    np.save("/tmp/r3_entry.npy", entry)

if __name__ == "__main__":
    main()
