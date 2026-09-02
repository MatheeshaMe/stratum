#!/usr/bin/env python3
"""N-3 staged conditioning. Short-side conditions are measured on -fret so the
frequency effect is always 'the thesis direction', making kappa comparable."""
import sys, os, pickle, numpy as np
sys.path.insert(0,'research/interp')
import n3_decomp as N3, tree as TR, behavior as BH

bb,al=pickle.load(open("/tmp/interp_obs.pkl","rb"))
idx,F,base=pickle.load(open("/tmp/interp_fwd1.pkl","rb"))
pos=np.zeros(len(bb['c']),np.int64)-1; pos[idx]=np.arange(len(idx))
T=TR.build_tree(bb,al,tf="15m",W=12,disp_atr=0.5)
fr=F["fret"]
def g(flag):
    m=np.zeros(len(idx),bool); s=pos[np.where(flag)[0]]; s=s[s>=0]; m[s]=True; return m

# context arrays on the forward grid
rp   = al["4h.range_pos"][idx]
vp   = al["5m.vol_pct"][idx]
htf  = al["4h.trend"][idx]
appe = al["5m.app_eff"][idx]
appv = al["5m.app_vel"][idx]
relv = al["5m.rel_vol"][idx]
eqlo = al["15m.equal_lo"][idx]; eqhi = al["15m.equal_hi"][idx]
expn = al["5m.expansion"][idx]

LOW=g(T["lo_raw"]); HIGH=g(T["hi_raw"])
def q(x,m,p): 
    v=x[m]; v=v[np.isfinite(v)]
    return np.nanquantile(v,p) if len(v)>200 else np.nan

def run(stage, rows):
    print(f"\n{'='*118}\n{stage}\n{'='*118}")
    print(f"  {'condition':<40}{'n':>7}{'ΔP(dir)':>9}{'Δu':>8}{'Δd':>8}"
          f"{'FREQ':>8}{'PAYOFF':>9}{'Δmean':>8}{'κ':>7}{'type':>6}{'  κ 95% CI':>16}")
    out={}
    for lbl,m,side in rows:
        if m.sum()<300: print(f"  {lbl:<40}{int(m.sum()):>7}  too few"); continue
        y  = fr if side>0 else -fr
        r=N3.decompose(y[m], y)
        if not r: print(f"  {lbl:<40}{int(m.sum()):>7}  n/a"); continue
        lo,hi=N3.kappa_ci(y[m],y,iters=600)
        out[lbl]=(r,lo,hi)
        print(f"  {lbl:<40}{r['n']:>7,}{r['d_p']:>+9.1%}{r['d_u']:>+8.3f}{r['d_d']:>+8.3f}"
              f"{r['FREQ']:>+8.3f}{r['PAYOFF']:>+9.3f}{r['d_mean']:>+8.3f}"
              f"{r['kappa']:>7.2f}{r['type']:>6}   [{lo:.2f},{hi:.2f}]")
    return out

ALL={}
ALL["N3-1"]=run("N3-1  BASELINE (thesis-direction frame)",
    [("sweep low  -> long thesis",LOW,+1),("sweep high -> short thesis",HIGH,-1)])

ALL["N3-2"]=run("N3-2  POST-SWEEP SEQUENCE",
    [("low -> reclaim + displacement",g(T["lo_reclaim_disp"]),+1),
     ("low -> reclaim, no displacement",g(T["lo_reclaim_nodisp"]),+1),
     ("low -> acceptance + displacement",g(T["lo_accept_disp"]),+1),
     ("low -> acceptance, no displacement",g(T["lo_accept_nodisp"]),+1),
     ("high -> reclaim + displacement",g(T["hi_reclaim_disp"]),-1),
     ("high -> reclaim, no displacement",g(T["hi_reclaim_nodisp"]),-1),
     ("high -> acceptance + displacement",g(T["hi_accept_disp"]),-1),
     ("high -> acceptance, no displacement",g(T["hi_accept_nodisp"]),-1)])

ALL["N3-3"]=run("N3-3  LOCATION (4h range position)",
    [("low @ discount (<0.33)",LOW&(rp<0.33),+1),
     ("low @ mid",LOW&(rp>=0.33)&(rp<0.67),+1),
     ("low @ premium (>0.67)",LOW&(rp>=0.67),+1),
     ("high @ discount (<0.33)",HIGH&(rp<0.33),-1),
     ("high @ mid",HIGH&(rp>=0.33)&(rp<0.67),-1),
     ("high @ premium (>0.67)",HIGH&(rp>=0.67),-1)])

ae_lo,ae_hi=q(appe,LOW,0.33),q(appe,LOW,0.67)
av_hi=q(appv,LOW,0.67); ex_lo,ex_hi=q(expn,LOW,0.33),q(expn,LOW,0.67)
ALL["N3-4"]=run("N3-4  APPROACH INTO THE SWEEP",
    [("low, efficient approach (top tercile)",LOW&(appe>ae_hi),+1),
     ("low, choppy approach (bottom tercile)",LOW&(appe<ae_lo),+1),
     ("low, fast approach (top tercile vel)",LOW&(appv>av_hi),+1),
     ("low, compressed before (bottom expansion)",LOW&(expn<ex_lo),+1),
     ("low, expanding before (top expansion)",LOW&(expn>ex_hi),+1)])

ALL["N3-5"]=run("N3-5  VOLATILITY REGIME",
    [("low, vol pct < 0.33",LOW&(vp<0.33),+1),
     ("low, vol pct 0.33-0.67",LOW&(vp>=0.33)&(vp<0.67),+1),
     ("low, vol pct > 0.67",LOW&(vp>=0.67),+1),
     ("high, vol pct < 0.33",HIGH&(vp<0.33),-1),
     ("high, vol pct > 0.67",HIGH&(vp>=0.67),-1)])

rv_lo,rv_hi=q(relv,LOW,0.33),q(relv,LOW,0.67)
ALL["N3-7"]=run("N3-7  VOLUME AT THE SWEEP",
    [("low, rel volume bottom tercile",LOW&(relv<rv_lo),+1),
     ("low, rel volume top tercile",LOW&(relv>rv_hi),+1),
     ("high, rel volume top tercile",HIGH&(relv>q(relv,HIGH,0.67)),-1)])

ALL["N3-8"]=run("N3-8  HTF STRUCTURE AGREEMENT / LIQUIDITY TYPE",
    [("low + HTF bullish (agrees)",LOW&(htf==1),+1),
     ("low + HTF bearish (conflicts)",LOW&(htf==-1),+1),
     ("high + HTF bearish (agrees)",HIGH&(htf==-1),-1),
     ("high + HTF bullish (conflicts)",HIGH&(htf==1),-1),
     ("low @ EQUAL lows (clustered)",LOW&(eqlo==1),+1),
     ("low @ isolated low",LOW&(eqlo==0),+1),
     ("high @ EQUAL highs (clustered)",HIGH&(eqhi==1),-1)])
pickle.dump(ALL,open("/tmp/n3_stages.pkl","wb"))
