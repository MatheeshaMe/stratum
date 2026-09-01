#!/usr/bin/env python3
"""Phases 4-6 on DISCOVERY only (2017-08 .. 2021-12). No held-out data touched."""
import sys, os, pickle, numpy as np
sys.path.insert(0,'research/trader'); sys.path.insert(0,'research/btc3')
import setups as SU, features as FT, events as E

def ms(s): return int(np.datetime64(s).astype('datetime64[ms]').astype(np.int64))
DISC=(ms('2017-08-01'),ms('2022-01-01'))
VALD=(ms('2022-01-01'),ms('2025-01-01'))
HELD=(ms('2025-01-01'),ms('2026-08-01'))

def prep(path,tf=60):
    T,O,H,L,C,V,N=E.load(path)
    b=SU.agg(T,O,H,L,C,V,N,tf)
    ctx,piv=SU.build_context(b)
    Z=SU.find_zones(b,ctx['A'])
    TE=SU.zone_touches(Z,b,ctx['A'])
    return b,ctx,Z,TE

def thesis_mask(ctx,e):
    """Returns dict of thesis_id -> bool, evaluated with data at bar e['i']."""
    i=e['i']; s=e['side']
    htf=ctx['htf'][i]; rp=ctx['range_pos'][i]
    swept = ctx['sweep_lo'][max(i-6,0):i+1].max() if s>0 else ctx['sweep_hi'][max(i-6,0):i+1].max()
    dec=ctx['app_decel'][i]
    loc_ok = (rp<0.5) if s>0 else (rp>0.5)
    ext_ok = (rp<0.15) if s>0 else (rp>0.85)
    t1=(htf==s)
    t2=t1 and np.isfinite(rp) and loc_ok
    t3=t2 and bool(swept)
    t4=t3 and np.isfinite(dec) and dec<1.0
    t5=t4 and e['bos']==1
    r1=(np.isfinite(rp) and ext_ok) and bool(swept) and (htf==-s)
    return dict(T0=True,T1=t1,T2=t2,T3=t3,T4=t4,T5=t5,R1=r1)

def run(path,lo,hi,models=("A","B","C","D","E"),
        mans=(("fix2",dict(mode="fixed",rr=2.0)),("fix3",dict(mode="fixed",rr=3.0)),
              ("fix5",dict(mode="fixed",rr=5.0)),("trailA",dict(mode="trail_atr",rr=None)),
              ("trailS",dict(mode="trail_struct",rr=None)))):
    b,ctx,Z,TE=prep(path)
    A=ctx['A']; n=len(b['c']); res={}
    for e in TE:
        i=e['i']
        if i<600 or i>=n-130: continue
        if not (lo<=b['t'][i]<hi): continue
        if e['touch']!=0: continue
        th=thesis_mask(ctx,e)
        for m in models:
            sig=SU.entry_signal(m,b,ctx,e)
            if sig is None: continue
            ei,epx,cost=sig
            if ei>=n-130: continue
            stop = e['dist']-0.25*A[ei] if e['side']>0 else e['dist']+0.25*A[ei]
            for mname,mkw in mans:
                r=SU.manage(b,ctx,ei,e['side'],epx,stop,cost=cost,maxb=120,**mkw)
                if r is None: continue
                for tid,ok in th.items():
                    if not ok: continue
                    res.setdefault((tid,m,mname),[]).append(
                        (r['R'],e['side'],b['t'][i],r['mfe'],r['mae'],r['bars']))
    return {k:np.array(v) for k,v in res.items()}

def boot(R,it=3000,seed=0):
    rg=np.random.default_rng(seed)
    return tuple(np.percentile([rg.choice(R,len(R)).mean() for _ in range(it)],[2.5,97.5]))

if __name__=="__main__":
    D=run("data/spot/BTCUSDT-1m-full.pkl",*DISC)
    pickle.dump(D,open("/tmp/trader_disc.pkl","wb"))
    print("DISCOVERY 2017-08 .. 2021-12  (BTC 1h)\n")
    print(f"{'thesis':<6}{'entry':<7}{'mgmt':<9}{'n':>6}{'win%':>7}{'EV R':>9}"
          f"{'  95% CI':>22}{'PF':>7}{'medMFE':>8}")
    rows=[]
    for k,M in sorted(D.items()):
        if len(M)<60: continue
        R=M[:,0]; w=R>0; lo,hi=boot(R)
        pf=R[w].sum()/max(-R[~w].sum(),1e-9)
        rows.append((R.mean(),k,len(R),w.mean(),lo,hi,pf,np.median(M[:,3])))
    rows.sort(reverse=True)
    for ev,k,nn,wr,lo,hi,pf,mfe in rows[:28]:
        f="  <<<" if lo>0 else ""
        print(f"{k[0]:<6}{k[1]:<7}{k[2]:<9}{nn:>6}{wr:>7.1%}{ev:>+9.3f}"
              f"   [{lo:+.3f},{hi:+.3f}]{pf:>7.2f}{mfe:>8.2f}{f}")
    print(f"\ncells scored: {len(rows)}   with CI above zero: "
          f"{sum(1 for r in rows if r[4]>0)}   expected by chance ~{0.05*len(rows):.0f}")
