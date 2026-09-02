#!/usr/bin/env python3
"""N-3 replication gate for the Type B compensation-break candidates."""
import sys, os, pickle, numpy as np
sys.path.insert(0,'research/interp'); sys.path.insert(0,'research/btc3')
import observe as OB, behavior as BH, tree as TR, n3_decomp as N3, events as E

def analyse(T,O,H,L,C,V,label,tsplit=None):
    bb,al,_,_=OB.build(T,O,H,L,C,V,base_tf="5m")
    idx,F=BH.forward_block(bb,al["5m.atr"],FWD=48,stride=1)
    tr=TR.build_tree(bb,al,tf="15m",W=12,disp_atr=0.5)
    pos=np.zeros(len(bb['c']),np.int64)-1; pos[idx]=np.arange(len(idx))
    def g(flag):
        m=np.zeros(len(idx),bool); s=pos[np.where(flag)[0]]; s=s[s>=0]; m[s]=True; return m
    fr=F["fret"]; t_of=bb['t'][idx]
    LOW=g(tr["lo_raw"]); HIGH=g(tr["hi_raw"])
    appe=al["5m.app_eff"][idx]; appv=al["5m.app_vel"][idx]
    expn=al["5m.expansion"][idx]; relv=al["5m.rel_vol"][idx]
    htf=al["4h.trend"][idx]; eqlo=al["15m.equal_lo"][idx]; rp=al["4h.range_pos"][idx]
    def q(x,m,p):
        v=x[m]; v=v[np.isfinite(v)]
        return np.nanquantile(v,p) if len(v)>200 else np.nan
    CAND={
      "low + compressed before":      (LOW&(expn<q(expn,LOW,0.33)), +1),
      "low + fast approach":          (LOW&(appv>q(appv,LOW,0.67)), +1),
      "low + HTF bullish":            (LOW&(htf==1), +1),
      "low + equal lows":             (LOW&(eqlo==1), +1),
      "low + low relative volume":    (LOW&(relv<q(relv,LOW,0.33)), +1),
      "low + efficient approach":     (LOW&(appe>q(appe,LOW,0.67)), +1),
      "low (unconditional control)":  (LOW, +1),
      "high + HTF bearish":           (HIGH&(htf==-1), -1),
      "high @ premium":               (HIGH&(rp>=0.67), -1),
      "high (unconditional control)": (HIGH, -1),
    }
    out={}
    wins=[("all",np.ones(len(idx),bool))]
    if tsplit is not None: wins=[("early",t_of<tsplit),("late",t_of>=tsplit)]
    for wn,wm in wins:
        for name,(m,side) in CAND.items():
            mm=m&wm
            if mm.sum()<300: continue
            y = fr if side>0 else -fr
            r=N3.decompose(y[mm], y[wm])
            if not r: continue
            lo,hi=N3.kappa_ci(y[mm],y[wm],iters=500)
            out[(label,wn,name)]=(r,lo,hi)
    return out

if __name__=="__main__":
    R={}
    T,O,H,L,C,V,N=E.load("data/spot/BTCUSDT-1m-full.pkl")
    sp=int(np.datetime64('2022-01-01').astype('datetime64[ms]').astype(np.int64))
    R.update(analyse(T,O,H,L,C,V,"BTC",tsplit=sp)); print("BTC done",flush=True)
    for sym,p in (("ETH","data/alt/ETHUSDT-1m.pkl"),("SOL","data/alt/SOLUSDT-1m.pkl"),
                  ("XRP","data/alt/XRPUSDT-1m.pkl"),("DOGE","data/alt/DOGEUSDT-1m.pkl")):
        if not os.path.exists(p): continue
        T2,O2,H2,L2,C2,V2,N2=E.load(p)
        R.update(analyse(T2,O2,H2,L2,C2,V2,sym)); print(f"{sym} done",flush=True)
    pickle.dump(R,open("/tmp/n3_repl.pkl","wb"))
    CELLS=[("BTC","early"),("BTC","late"),("ETH","all"),("SOL","all"),("XRP","all"),("DOGE","all")]
    NAMES=["low (unconditional control)","low + compressed before","low + fast approach",
           "low + HTF bullish","low + equal lows","low + low relative volume",
           "low + efficient approach","high (unconditional control)","high + HTF bearish",
           "high @ premium"]
    print(f"\n{'='*120}\nKAPPA across cells  (κ<0.75 = compensation partly breaks; "
          f"κ>1 = over-compensation)\n{'='*120}")
    print(f"{'candidate':<30}" + "".join(f"{c[0]+'/'+c[1][:3]:>13}" for c in CELLS)
          + f"{'  FREQ>0 all?':>14}{'  band held?':>13}")
    for nm in NAMES:
        row=f"{nm:<30}"; ks=[]; freqs=[]
        for lab,wn in CELLS:
            v=R.get((lab,wn,nm))
            if v is None: row+=f"{'--':>13}"; continue
            r,lo,hi=v; ks.append(r['kappa']); freqs.append(r['FREQ'])
            row+=f"{r['kappa']:>12.2f}{'*' if (lo>1 or hi<1) else ' '}"
        fa="yes" if freqs and all(f>0 for f in freqs) else "NO"
        band=""
        if len(ks)>=5 and all(np.isfinite(k) for k in ks):
            if all(k<0.75 for k in ks): band="B/C all"
            elif all(k>=0.75 for k in ks): band="A all"
        print(row+f"{fa:>14}{band:>13}")
    print("\n  * = κ 95% CI excludes 1.0 in that cell")
    print(f"\n{'='*120}\nΔmean across cells (ATR, thesis direction)\n{'='*120}")
    print(f"{'candidate':<30}" + "".join(f"{c[0]+'/'+c[1][:3]:>13}" for c in CELLS))
    for nm in NAMES:
        row=f"{nm:<30}"
        for lab,wn in CELLS:
            v=R.get((lab,wn,nm))
            row += f"{'--':>13}" if v is None else f"{v[0]['d_mean']:>+13.3f}"
        print(row)
