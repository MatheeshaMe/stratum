import sys,pickle,numpy as np
sys.path.insert(0,'research/interp')
import n3_decomp as N3, tree as TR
bb,al=pickle.load(open("/tmp/interp_obs.pkl","rb"))
idx,F,base=pickle.load(open("/tmp/interp_fwd1.pkl","rb"))
pos=np.zeros(len(bb['c']),np.int64)-1; pos[idx]=np.arange(len(idx))
T=TR.build_tree(bb,al,tf="15m",W=12,disp_atr=0.5)
fr=F["fret"]
lo5,hi5=np.nanquantile(fr[np.isfinite(fr)],[0.05,0.95])
frw=np.clip(fr,lo5,hi5)
def g(flag):
    m=np.zeros(len(idx),bool); s=pos[np.where(flag)[0]]; s=s[s>=0]; m[s]=True; return m
LOW=g(T["lo_raw"]); HIGH=g(T["hi_raw"])
rp=al["4h.range_pos"][idx]; vp=al["5m.vol_pct"][idx]; htf=al["4h.trend"][idx]
appv=al["5m.app_vel"][idx]; expn=al["5m.expansion"][idx]; relv=al["5m.rel_vol"][idx]
eqlo=al["15m.equal_lo"][idx]; appe=al["5m.app_eff"][idx]
def q(x,m,p):
    v=x[m]; v=v[np.isfinite(v)]; return np.nanquantile(v,p) if len(v)>200 else np.nan
CAND=[("low (control)",LOW,+1),
      ("low + compressed before",LOW&(expn<q(expn,LOW,0.33)),+1),
      ("low + fast approach",LOW&(appv>q(appv,LOW,0.67)),+1),
      ("low + HTF bullish",LOW&(htf==1),+1),
      ("low + equal lows",LOW&(eqlo==1),+1),
      ("low + low rel volume",LOW&(relv<q(relv,LOW,0.33)),+1),
      ("low + efficient approach",LOW&(appe>q(appe,LOW,0.67)),+1),
      ("low + discount",LOW&(rp<0.33),+1),
      ("low + premium",LOW&(rp>=0.67),+1),
      ("low + acceptance+disp",g(T["lo_accept_disp"]),+1),
      ("low + reclaim+disp",g(T["lo_reclaim_disp"]),+1),
      ("high (control)",HIGH,-1),
      ("high + HTF bearish",HIGH&(htf==-1),-1),
      ("high + acceptance+disp",g(T["hi_accept_disp"]),-1)]
print("WINSORISED (5%) DECOMPOSITION — BTC. κ<0.75 = compensation partly breaks\n")
print(f"  {'condition':<30}{'n':>7}{'ΔP(dir)':>9}{'Δu':>8}{'Δd':>8}{'FREQ':>8}"
      f"{'PAYOFF':>9}{'Δmean':>8}{'κ':>7}{'type':>6}{'  κ 95% CI':>16}")
for lbl,m,side in CAND:
    if m.sum()<300: continue
    y=frw if side>0 else -frw
    r=N3.decompose(y[m],y)
    if not r: continue
    ci=N3.kappa_ci(y[m],y,iters=800)
    star="*" if (ci[0]>1 or ci[1]<1) else " "
    print(f"  {lbl:<30}{r['n']:>7,}{r['d_p']:>+9.1%}{r['d_u']:>+8.3f}{r['d_d']:>+8.3f}"
          f"{r['FREQ']:>+8.3f}{r['PAYOFF']:>+9.3f}{r['d_mean']:>+8.3f}{r['kappa']:>7.2f}"
          f"{r['type']:>6}   [{ci[0]:.2f},{ci[1]:.2f}]{star}")
