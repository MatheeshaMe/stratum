#!/usr/bin/env python3
"""Replication gate — pre-specified criteria from PRESPEC_BEHAVIOR.md."""
import sys, os, pickle, numpy as np
sys.path.insert(0,'research/interp'); sys.path.insert(0,'research/btc3')
import observe as OB, behavior as BH, tree as TR, events as E

BRANCHES=["lo_raw","lo_reclaim_disp","lo_reclaim_nodisp","lo_accept_disp","lo_accept_nodisp",
          "hi_raw","hi_reclaim_disp","hi_reclaim_nodisp","hi_accept_disp","hi_accept_nodisp"]
KEYS=["d_mean","d_pup","d_upfirst_1.0","r_mfe","r_mae","r_range","r_t_0.5","r_sd","d_skew"]

def analyse(T,O,H,L,C,V,label,tsplit=None):
    bb,al,_,_=OB.build(T,O,H,L,C,V,base_tf="5m")
    idx,F=BH.forward_block(bb,al["5m.atr"],FWD=48,stride=1)
    tree=TR.build_tree(bb,al,tf="15m",W=12,disp_atr=0.5)
    pos=np.zeros(len(bb['c']),np.int64)-1; pos[idx]=np.arange(len(idx))
    t_of=bb['t'][idx]
    out={}
    wins=[("all",np.ones(len(idx),bool))]
    if tsplit is not None:
        wins=[("early",t_of<tsplit),("late",t_of>=tsplit)]
    for wn,wm in wins:
        base=BH.profile(F,wm)
        if base is None: continue
        for br in BRANCHES:
            sel=pos[np.where(tree[br])[0]]; sel=sel[sel>=0]
            m=np.zeros(len(idx),bool); m[sel]=True; m&=wm
            if m.sum()<300: continue
            p=BH.profile(F,m,base)
            if p: out[(label,wn,br)]=p
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
    pickle.dump(R,open("/tmp/interp_repl.pkl","wb"))
    CELLS=[("BTC","early"),("BTC","late"),("ETH","all"),("SOL","all"),("XRP","all"),("DOGE","all")]
    THR={"d_mean":0.0,"d_pup":0.02,"d_upfirst_1.0":0.02,
         "r_mfe":(0.92,1.08),"r_mae":(0.92,1.08),"r_range":(0.92,1.08),
         "r_t_0.5":(0.85,1.15),"r_sd":(0.90,1.10),"d_skew":0.15}
    for key in KEYS:
        print(f"\n{'='*118}\n{key}\n{'='*118}")
        print(f"{'branch':<22}" + "".join(f"{c[0]+'/'+c[1][:3]:>13}" for c in CELLS)
              + f"{'  replicates?':>14}")
        for br in BRANCHES:
            row=f"{br:<22}"; vals=[]
            for lab,wn in CELLS:
                p=R.get((lab,wn,br))
                if p is None or key not in p: row+=f"{'--':>13}"; continue
                v=p[key]; vals.append(v); row+=f"{v:>13.3f}"
            verdict=""
            if len(vals)>=5:
                t=THR[key]
                if isinstance(t,tuple):
                    outside=[v for v in vals if v<t[0] or v>t[1]]
                    same=all(v<t[0] for v in outside) or all(v>t[1] for v in outside)
                    if len(outside)>=5 and same: verdict="REPLICATED"
                else:
                    big=[v for v in vals if abs(v)>=t]
                    same=all(np.sign(v)==np.sign(vals[0]) for v in vals)
                    if same and len(big)>=4: verdict="REPLICATED"
                    elif same: verdict="sign holds"
            print(row+f"{verdict:>14}")
