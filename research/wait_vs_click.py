"""The operator's actual question, made measurable.

At the moment a situation appears you have three policies, not two:

    CLICK   enter now at the close
    WAIT    wait up to W bars for a written trigger; enter only if it prints
    PASS    never enter

WAIT is not free. Sometimes the trigger never prints and you get nothing;
sometimes it prints after the move already left. The honest comparison is
expected R per OPPORTUNITY (not per trade), net of cost, so a policy that
trades rarely is not flattered by its own selectivity.
"""
import sys, os, pickle, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import situations as S

MAKER, TAKER, HALF = 1.5/1e4, 4.5/1e4, 0.63/1e4
RT_COST = MAKER + TAKER + HALF          # maker in, taker out

def outcome_from(rows, b, st, i, side, k_atr, rr, horizon):
    """Triple barrier from bar i. Returns net R, or None if unusable."""
    H1 = np.array([]) ; # bound in caller for speed
    return None

def run_policy(rows, b, st, lab, bucket, side, k_atr=2.0, rr=1.5,
               horizon=36, wait_bars=6, trigger="close_back_through"):
    H1 = run_policy.H1; L1 = run_policy.L1; C1 = run_policy.C1
    c, h, l = b['c'], b['h'], b['l']; A = st['A']; i1 = b['i1m']; n = len(c)
    up, dn = st['up'], st['dn']
    res = {"click": [], "wait": [], "wait_no_trigger": 0, "opportunities": 0}

    def barrier(i_entry, entry_px, stop_d):
        j0 = i1[min(i_entry+1, n-1)]
        j1 = i1[min(i_entry+1+horizon, n-1)]
        if j1 <= j0: return None
        tgt = entry_px + side*stop_d*rr
        stp = entry_px - side*stop_d
        seg_h = H1[j0:j1]; seg_l = L1[j0:j1]
        if side > 0: w = seg_h >= tgt; s = seg_l <= stp
        else:        w = seg_l <= tgt; s = seg_h >= stp
        wi = np.argmax(w) if w.any() else 10**9
        si = np.argmax(s) if s.any() else 10**9
        if wi == 10**9 and si == 10**9:
            gross = side*(C1[j1-1] - entry_px)/stop_d      # mark out at vertical
        elif si <= wi: gross = -1.0                         # ties -> stop
        else:          gross = float(rr)
        cost = RT_COST * entry_px / stop_d
        return gross - cost

    cool = -1
    for i in range(80, n - horizon - wait_bars - 2):
        if lab[i] != bucket or i < cool: continue
        a = A[i]
        if not np.isfinite(a): continue
        stop_d = k_atr * a
        if stop_d/c[i] < 0.006: continue        # COST-1 stop floor
        res["opportunities"] += 1
        cool = i + horizon//3

        r = barrier(i, c[i], stop_d)
        if r is not None: res["click"].append(r)

        # WAIT: scan forward for the written trigger
        lvl = up[i] if side < 0 else dn[i]
        fired = None
        for j in range(i+1, i+1+wait_bars):
            if trigger == "close_back_through" and np.isfinite(lvl):
                if side < 0 and c[j] < lvl and h[j] >= lvl: fired = j; break
                if side > 0 and c[j] > lvl and l[j] <= lvl: fired = j; break
            elif trigger == "engulf":
                body = abs(c[j]-b['o'][j]); pb = abs(c[j-1]-b['o'][j-1])
                if body > pb and np.sign(c[j]-b['o'][j]) == side: fired = j; break
            elif trigger == "momentum_close":
                if side*(c[j] - c[i]) > 0.5*a: fired = j; break
        if fired is None:
            res["wait_no_trigger"] += 1
        else:
            aa = A[fired]; sd = k_atr*aa
            if sd/c[fired] >= 0.006:
                r2 = barrier(fired, c[fired], sd)
                if r2 is not None: res["wait"].append(r2)
            else:
                res["wait_no_trigger"] += 1
    return res

def summarise(tag, res):
    opp = res["opportunities"]
    cl = np.array(res["click"]); wa = np.array(res["wait"])
    if opp == 0 or len(cl) == 0: 
        print(f"  {tag:<26} no opportunities"); return None
    # expected R PER OPPORTUNITY -- waiting that never triggers earns 0
    ev_click = cl.mean()
    ev_wait  = (wa.sum()/opp) if len(wa) else 0.0
    trig_rate = len(wa)/opp
    print(f"  {tag:<26}{opp:>7}{ev_click:>+10.3f}{cl.mean():>9.3f}"
          f"{trig_rate:>9.1%}{(wa.mean() if len(wa) else 0):>+10.3f}{ev_wait:>+11.3f}"
          f"{'  WAIT' if ev_wait > ev_click else '  CLICK'}")
    return ev_click, ev_wait, trig_rate

if __name__ == "__main__":
    for period, path in (("IS  2025-26","data/is/BTCUSDT-1m.pkl"),
                         ("OOS 2023-24","data/oos/BTCUSDT-1m.pkl")):
        rows = pickle.load(open(path,"rb"))
        b = S.agg(rows,5); st = S.situations(b); lab = S.buckets(b,st)
        run_policy.H1 = np.array([r[2] for r in rows])
        run_policy.L1 = np.array([r[3] for r in rows])
        run_policy.C1 = np.array([r[4] for r in rows])
        print(f"\n{'='*104}\n{period}   barrier ±2 ATR, target 1.5R, horizon 3h, "
              f"wait window 6 bars, cost charged\n")
        print(f"  {'bucket / side / trigger':<26}{'opps':>7}{'EV click':>10}"
              f"{'(per tr)':>9}{'trig%':>9}{'EV|trig':>10}{'EV wait':>11}   better")
        print("  " + "-"*100)
        for bucket, side, sname in ((2,-1,"SHORT"), (1,-1,"SHORT"), (6,+1,"LONG"),
                                    (3,+1,"LONG"), (5,+1,"LONG")):
            for trig in ("close_back_through","momentum_close"):
                r = run_policy(rows,b,st,lab,bucket,side,trigger=trig)
                summarise(f"{S.BUCKET_NAMES[bucket][:12]} {sname} {trig[:9]}", r)
