#!/usr/bin/env python3
"""Action-value table -> policy -> validation, with the three controls."""
import sys, os, pickle, numpy as np, collections
sys.path.insert(0,'research/policy'); sys.path.insert(0,'research/btc3')
import engine as EN, events as E

def ms(s): return int(np.datetime64(s).astype('datetime64[ms]').astype(np.int64))
DISC=(ms('2017-08-01'),ms('2022-01-01'))
VALD=(ms('2022-01-01'),ms('2025-01-01'))
HELD=(ms('2025-01-01'),ms('2026-08-01'))

def prep(path,tf=60):
    T,O,H,L,C,V,N=E.load(path)
    b=EN.agg(T,O,H,L,C,V,N,tf)
    return b, EN.market_state(b)

def sample_all(b,ctx,lo,hi,manage="target"):
    """All action triggers in a window -> (state, action, R, side, t, rr)."""
    n=len(b['c']); rows=[]
    for i in range(600,n-130):
        t=b['t'][i]
        if not (lo<=t<hi): continue
        s=int(ctx['state'][i])
        for a in EN.ACTIONS:
            if a=="WAIT": continue
            trig=EN.action_trigger(a,b,ctx,i)
            if trig is None: continue
            side,entry,cost=trig
            r=EN.run_trade(b,ctx,i,side,entry,cost,manage=manage)
            if r is None: continue
            rows.append((s,EN.ACTIONS.index(a),r['R'],side,t,r['rr'],r['bars']))
    return np.array(rows) if rows else np.zeros((0,7))

def boot(R,it=3000,seed=0):
    if len(R)<20: return (np.nan,np.nan)
    rg=np.random.default_rng(seed)
    return tuple(np.percentile([rg.choice(R,len(R)).mean() for _ in range(it)],[2.5,97.5]))

def value_table(M,min_n=40):
    """(state, action) -> (n, EV, lo, hi)."""
    V={}
    for s in np.unique(M[:,0]).astype(int):
        for a in np.unique(M[:,1]).astype(int):
            m=(M[:,0]==s)&(M[:,1]==a)
            if m.sum()<min_n: continue
            R=M[m,2]; lo,hi=boot(R)
            V[(s,a)]=(int(m.sum()),R.mean(),lo,hi)
    return V

def greedy_policy(V):
    pol={}
    for (s,a),(n,ev,lo,hi) in V.items():
        if s not in pol or ev>pol[s][1]: pol[s]=(a,ev)
    return {s:(a if ev>0 else -1) for s,(a,ev) in pol.items()}   # -1 = WAIT

def shrunk_policy(V,global_best_a,global_best_ev):
    """Deviate from the global best action only where the state's advantage
    clears its own confidence interval."""
    pol={}
    for (s,a),(n,ev,lo,hi) in V.items():
        if lo>max(global_best_ev,0.0):
            if s not in pol or ev>pol[s][1]: pol[s]=(a,ev)
    out={}
    for s in {k[0] for k in V}:
        out[s]=pol[s][0] if s in pol else (global_best_a if global_best_ev>0 else -1)
    return out

def apply_policy(M,pol):
    """Score a policy on a sample matrix."""
    keep=[]
    for row in M:
        s,a=int(row[0]),int(row[1])
        if pol.get(s,-1)==a: keep.append(row[2])
    return np.array(keep)

if __name__=="__main__":
    b,ctx=prep("data/spot/BTCUSDT-1m-full.pkl")
    print("sampling action triggers (BTC 1h, dynamic stop + dynamic liquidity target)...")
    D=sample_all(b,ctx,*DISC); V_=sample_all(b,ctx,*VALD); H=sample_all(b,ctx,*HELD)
    pickle.dump((D,V_,H),open("/tmp/pol_samples.pkl","wb"))
    print(f"  discovery {len(D):,}  validation {len(V_):,}  holdout {len(H):,}\n")

    print("UNCONDITIONAL ACTION VALUES on DISCOVERY (the constant-action baselines)")
    print(f"  {'action':<10}{'n':>7}{'EV R':>9}{'  95% CI':>22}{'medRR':>8}{'win%':>7}")
    best_a,best_ev=-1,-9
    for ai,a in enumerate(EN.ACTIONS):
        if a=="WAIT": continue
        m=D[:,1]==ai
        if m.sum()<40: continue
        R=D[m,2]; lo,hi=boot(R)
        print(f"  {a:<10}{int(m.sum()):>7}{R.mean():>+9.3f}   [{lo:+.3f},{hi:+.3f}]"
              f"{np.median(D[m,5]):>8.2f}{(R>0).mean():>7.1%}")
        if R.mean()>best_ev: best_a,best_ev=ai,R.mean()
    print(f"  {'WAIT':<10}{'--':>7}{0.0:>+9.3f}")
    print(f"\n  best constant action on discovery: "
          f"{EN.ACTIONS[best_a] if best_ev>0 else 'WAIT'} at {max(best_ev,0):+.3f} R")

    VT=value_table(D)
    G=greedy_policy(VT); S=shrunk_policy(VT,best_a,best_ev)
    print(f"\n  greedy policy covers {len(G)} states, "
          f"{sum(1 for v in G.values() if v>=0)} of them trading")
    print(f"  shrunk policy deviates from the constant action in "
          f"{sum(1 for s,v in S.items() if v!=best_a)} states")

    rng=np.random.default_rng(0)
    print(f"\n{'='*96}\nPOLICY COMPARISON\n{'='*96}")
    print(f"  {'policy':<26}{'set':<12}{'n':>7}{'EV R':>9}{'  95% CI':>22}{'totR':>9}")
    def rep(lbl,setlbl,R):
        if len(R)<30: print(f"  {lbl:<26}{setlbl:<12}{len(R):>7}  too few"); return
        lo,hi=boot(R)
        print(f"  {lbl:<26}{setlbl:<12}{len(R):>7}{R.mean():>+9.3f}"
              f"   [{lo:+.3f},{hi:+.3f}]{R.sum():>+9.1f}{'  <<<' if lo>0 else ''}")
    for setlbl,M in (("discovery",D),("validation",V_)):
        rep("constant best action",setlbl,M[M[:,1]==best_a,2])
        rep("greedy state policy",setlbl,apply_policy(M,G))
        rep("shrunk state policy",setlbl,apply_policy(M,S))
        # permuted-state control: shuffle state labels, refit greedy on discovery
        perm=D.copy(); perm[:,0]=rng.permutation(perm[:,0])
        Gp=greedy_policy(value_table(perm))
        rep("permuted-state control",setlbl,apply_policy(M,Gp))
        print()
    pickle.dump((VT,G,S,best_a,best_ev),open("/tmp/pol_policy.pkl","wb"))
