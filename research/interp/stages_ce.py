#!/usr/bin/env python3
"""Stage C — does an event's MEANING change by location? (§9)
   Stage E — is the event redundant given structure + location? (§20)"""
import sys, os, pickle, numpy as np
sys.path.insert(0,'research/interp')
import behavior as BH, tree as TR

bb,al=pickle.load(open("/tmp/interp_obs.pkl","rb"))
idx,F,base=pickle.load(open("/tmp/interp_fwd1.pkl","rb"))
pos=np.zeros(len(bb['c']),np.int64)-1; pos[idx]=np.arange(len(idx))
tree=TR.build_tree(bb,al,tf="15m",W=12,disp_atr=0.5)

rp=al["4h.range_pos"][idx]
htf=al["4h.trend"][idx]
LOC={"discount (<0.33)":(np.isfinite(rp))&(rp<0.33),
     "mid (0.33-0.67)":(np.isfinite(rp))&(rp>=0.33)&(rp<0.67),
     "premium (>0.67)":(np.isfinite(rp))&(rp>0.67)}
HTF={"HTF bullish":htf==1,"HTF bearish":htf==-1}

def grid_of(flag):
    m=np.zeros(len(idx),bool)
    sel=pos[np.where(flag)[0]]; sel=sel[sel>=0]; m[sel]=True
    return m

EVENTS={"sweep low (raw)":grid_of(tree["lo_raw"]),
        "sweep low -> reclaim":grid_of(tree["lo_reclaim_disp"]|tree["lo_reclaim_nodisp"]),
        "sweep low -> acceptance":grid_of(tree["lo_accept_disp"]|tree["lo_accept_nodisp"]),
        "sweep high (raw)":grid_of(tree["hi_raw"]),
        "sweep high -> reclaim":grid_of(tree["hi_reclaim_disp"]|tree["hi_reclaim_nodisp"]),
        "sweep high -> acceptance":grid_of(tree["hi_accept_disp"]|tree["hi_accept_nodisp"]),
        "rejection candle (5m)":grid_of((al["5m.wick_dn"]>0.5)&(al["5m.body_frac"]<0.4))}

print("STAGE C — does the same event mean different things at different LOCATIONS?")
print(f"baseline: P(up) {base['p_up']:.1%}  P(+1 1st) {base['upfirst_1.0']:.1%}  "
      f"MFE {base['mfe']:.2f}  range {base['range']:.2f}  t½ {base['t_0.5']:.0f}\n")
for ename,em in EVENTS.items():
    print(f"  {ename}")
    print(f"    {'location':<20}{'n':>7}{'Δmean':>8}{'ΔP(up)':>9}{'ΔP(+1 1st)':>12}"
          f"{'MFE x':>8}{'rng x':>7}{'t½ x':>7}{'Δskew':>8}")
    for lname,lm in LOC.items():
        m=em&lm
        if m.sum()<300: print(f"    {lname:<20}{int(m.sum()):>7}  too few"); continue
        b2=BH.profile(F,lm)                 # location-matched baseline
        p=BH.profile(F,m,b2)
        if p is None: continue
        print(f"    {lname:<20}{p['n']:>7,}{p['d_mean']:>+8.3f}{p['d_pup']:>+9.1%}"
              f"{p['d_upfirst_1.0']:>+12.1%}{p['r_mfe']:>8.2f}{p['r_range']:>7.2f}"
              f"{p['r_t_0.5']:>7.2f}{p['d_skew']:>+8.2f}")
    print()

print("\nSTAGE E — INCREMENTAL INFORMATION over structure + location")
print("Does adding the event change the profile of a context that already knows")
print("HTF trend and range position? If not, the event is redundant.\n")
print(f"  {'context':<44}{'n':>8}{'P(up)':>8}{'P(+1 1st)':>11}{'MFE':>7}{'range':>7}{'t½':>6}")
for hname,hm in HTF.items():
    for lname,lm in LOC.items():
        ctx=hm&lm
        if ctx.sum()<2000: continue
        pc=BH.profile(F,ctx)
        print(f"  {hname+' + '+lname:<44}{pc['n']:>8,}{pc['p_up']:>8.1%}"
              f"{pc['upfirst_1.0']:>11.1%}{pc['mfe']:>7.2f}{pc['range']:>7.2f}{pc['t_0.5']:>6.0f}")
        for ename,em in EVENTS.items():
            if "raw" in ename or "rejection" in ename: continue
            m=ctx&em
            if m.sum()<200: continue
            pe=BH.profile(F,m,pc)
            flag=""
            if abs(pe['d_pup'])>=0.02 or abs(pe['d_upfirst_1.0'])>=0.02 \
               or pe['r_range']<0.92 or pe['r_range']>1.08 \
               or pe['r_t_0.5']<0.85 or pe['r_t_0.5']>1.15: flag="  <-- adds info"
            print(f"      + {ename:<40}{pe['n']:>8,}{pe['p_up']:>8.1%}"
                  f"{pe['upfirst_1.0']:>11.1%}{pe['mfe']:>7.2f}{pe['range']:>7.2f}"
                  f"{pe['t_0.5']:>6.0f}{flag}")
        print()
