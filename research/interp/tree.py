#!/usr/bin/env python3
"""Stage B — the sweep decomposition tree (§7).

           sweep_lo (poke below a pool, close back inside)
                          |
        +-----------------+------------------+
        |                 |                  |
    RECLAIM           ACCEPTANCE          NEITHER
   (2 closes back    (2 closes below     (unresolved
    above the pool)   the pool)           within W)
        |                 |
   +----+----+       +----+----+
   |         |       |         |
 DISPLACE  NO DISP  DISPLACE  NO DISP

Each branch fires on the bar it RESOLVES, and forward behaviour is measured from
that bar. Mirror tree for sweep_hi. 12 branches, pre-specified.
"""
import sys, os, pickle, numpy as np
sys.path.insert(0,'research/interp')
import behavior as BH

def build_tree(bb, al, tf="1h", W=12, disp_atr=1.0):
    """Returns dict branch_name -> boolean array on the 5m base grid."""
    C,H,L,O=bb['c'],bb['h'],bb['l'],bb['o']; n=len(C)
    A=al["5m.atr"]
    sw_lo=al[f"{tf}.sweep_lo"]; sw_hi=al[f"{tf}.sweep_hi"]
    pool_lo=al[f"{tf}.pool_lo"]; pool_hi=al[f"{tf}.pool_hi"]
    out={k:np.zeros(n,bool) for k in
         ("lo_reclaim_disp","lo_reclaim_nodisp","lo_accept_disp","lo_accept_nodisp",
          "lo_neither","hi_reclaim_disp","hi_reclaim_nodisp","hi_accept_disp",
          "hi_accept_nodisp","hi_neither","lo_raw","hi_raw")}
    # rising edges of the sweep flag = one event per episode
    for side,flag,pool,pre in ((+1,sw_lo,pool_lo,"lo"),(-1,sw_hi,pool_hi,"hi")):
        edge=(flag==1); edge[1:]&=~(flag[:-1]==1)
        for k in np.where(edge)[0]:
            if k<10 or k+W+2>=n: continue
            p=pool[k]
            if not np.isfinite(p): continue
            out[f"{pre}_raw"][k]=True
            resolved=False
            for j in range(k+1,min(k+1+W,n-1)):
                if side>0:
                    rec = C[j]>p and C[j-1]>p
                    acc = C[j]<p and C[j-1]<p
                    d   = (C[j]-C[k])
                else:
                    rec = C[j]<p and C[j-1]<p
                    acc = C[j]>p and C[j-1]>p
                    d   = (C[k]-C[j])
                a=A[j]
                if not np.isfinite(a) or a<=0: continue
                if rec:
                    key=f"{pre}_reclaim_" + ("disp" if d>disp_atr*a else "nodisp")
                    out[key][j]=True; resolved=True; break
                if acc:
                    dd = (C[k]-C[j]) if side>0 else (C[j]-C[k])
                    key=f"{pre}_accept_" + ("disp" if dd>disp_atr*a else "nodisp")
                    out[key][j]=True; resolved=True; break
            if not resolved: out[f"{pre}_neither"][min(k+W,n-1)]=True
    return out

if __name__=="__main__":
    bb,al=pickle.load(open("/tmp/interp_obs.pkl","rb"))
    idx,F,base=pickle.load(open("/tmp/interp_fwd.pkl","rb"))
    T=build_tree(bb,al,tf="1h")
    pickle.dump(T,open("/tmp/interp_tree.pkl","wb"))
    pos=np.zeros(len(bb['c']),np.int64)-1; pos[idx]=np.arange(len(idx))
    print("STAGE B — SWEEP DECOMPOSITION TREE (1h pools, resolution within 12 bars)")
    print(f"forward window 4h, ATR units. Baseline n={base['n']:,}\n")
    hdr=(f"{'branch':<24}{'n':>7}{'Δmean':>8}{'ΔP(up)':>9}{'ΔP(+1 1st)':>12}"
         f"{'MFE x':>8}{'MAE x':>8}{'range x':>9}{'t½ x':>7}{'sd x':>7}{'Δskew':>8}")
    print(hdr); print("-"*len(hdr))
    rows={}
    for k,v in T.items():
        m=np.zeros(len(idx),bool)
        sel=pos[np.where(v)[0]]; sel=sel[sel>=0]
        if len(sel)<200: 
            print(f"{k:<24}{len(sel):>7}   too few"); continue
        m[sel]=True
        p=BH.profile(F,m,base)
        if p is None: continue
        rows[k]=p
        print(f"{k:<24}{p['n']:>7,}{p['d_mean']:>+8.3f}{p['d_pup']:>+9.1%}"
              f"{p['d_upfirst_1.0']:>+12.1%}{p['r_mfe']:>8.2f}{p['r_mae']:>8.2f}"
              f"{p['r_range']:>9.2f}{p['r_t_0.5']:>7.2f}{p['r_sd']:>7.2f}{p['d_skew']:>+8.2f}")
    pickle.dump(rows,open("/tmp/interp_tree_rows.pkl","wb"))
    print("\n  Δmean/ΔP in ATR and percentage points vs baseline; x = ratio to baseline")
    print("  t½ x = median bars to a +/-0.5 ATR touch, relative to baseline")
