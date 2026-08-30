#!/usr/bin/env python3
"""E2/E3 -- how often does BTC actually deliver the required move, and does the
path get there before the stop? Measured, not assumed.

Entries every 15 minutes across 2017-2026 spot (sealed 2020-2022 excluded).
For each entry, first passage to a grid of +target / -stop pairs on 1m bars,
both LONG and SHORT, resolved to the LOSS on same-bar ties.
"""
import sys, os, pickle, numpy as np
sys.path.insert(0, "research/btc3")
import events as E

T,O,H,L,C,V,N = E.load("data/spot/BTCUSDT-1m.pkl")
n=len(C)
IND=pickle.load(open("/tmp/btc3_ind.pkl","rb")) if os.path.exists("/tmp/btc3_ind.pkl") else None
HMAX=1440
STRIDE=15
ent=np.arange(20161, n-HMAX-2, STRIDE)
contig=(T[np.minimum(ent+HMAX,n-1)]-T[ent])==HMAX*60000
ent=ent[contig]
print(f"entries: {len(ent):,} (every {STRIDE}m, {np.datetime64(int(T[ent[0]]),'ms')} "
      f"-> {np.datetime64(int(T[ent[-1]]),'ms')})")

# leverage -> BTC move for +3% account
LEVS=[(1,3.0),(2,1.5),(5,0.6),(10,0.3),(20,0.15),(40,0.075)]
COST={"maker/maker":0.030,"maker/taker":0.0663,"taker/taker":0.1026}   # % of notional

def first_passage(ent, tgts, stps, side, chunk=4000):
    """Returns tp[n,len(tgts)], sl[n,len(stps)] first-passage minutes (or BIG)."""
    BIG=np.int32(10**6)
    tp=np.full((len(ent),len(tgts)),BIG,dtype=np.int32)
    sl=np.full((len(ent),len(stps)),BIG,dtype=np.int32)
    off=np.arange(1,HMAX+1)
    for a in range(0,len(ent),chunk):
        e=ent[a:a+chunk]; idx=e[:,None]+off[None,:]; px=C[e][:,None]
        rh=np.maximum.accumulate(H[idx],axis=1)/px
        rl=np.minimum.accumulate(L[idx],axis=1)/px
        for k,t in enumerate(tgts):
            m=(rh>=1+t/100) if side>0 else (rl<=1-t/100)
            tp[a:a+len(e),k]=np.where(m.any(1), m.argmax(1)+1, BIG)
        for k,s in enumerate(stps):
            m=(rl<=1-s/100) if side>0 else (rh>=1+s/100)
            sl[a:a+len(e),k]=np.where(m.any(1), m.argmax(1)+1, BIG)
    return tp,sl

TGT=[l[1] for l in LEVS]
FP={}
for side,sn in ((+1,"LONG"),(-1,"SHORT")):
    FP[sn]=first_passage(ent,TGT,TGT,side)
    print(f"  {sn} first-passage computed")

print(f"\n{'='*112}")
print("OPPORTUNITY AVAILABILITY -- P(reach the +3%-account target at all) and")
print("P(reach it BEFORE an equal-sized adverse move), by leverage and time limit")
print(f"{'='*112}")
for side,sn in (("LONG","LONG"),("SHORT","SHORT")):
    tp,sl=FP[sn]
    print(f"\n  {sn}")
    print(f"  {'lev':<6}{'BTC tgt':>9}" + "".join(f"{f'{m}m':>19}" for m in (5,15,30,60,240,1440)))
    print(f"  {'':<6}{'':>9}" + "".join(f"{'P(hit)  P(1st)':>19}" for _ in range(6)))
    for k,(Lv,t) in enumerate(LEVS):
        row=f"  {Lv:>3}x{'':<2}{t:>8.3f}%"
        for lim in (5,15,30,60,240,1440):
            hit=(tp[:,k]<=lim)
            first=hit & (tp[:,k]<sl[:,k])
            row+=f"{hit.mean():>11.1%}{first.mean():>8.1%}"
        print(row)
print("\n  P(hit)  = target touched within the limit, ignoring the adverse path")
print("  P(1st)  = target touched BEFORE an equal-sized adverse move (a 1:1 trade)")

print(f"\n\n{'='*112}\nNET EXPECTANCY of a 1:1 trade at each leverage, cost inside")
print(f"{'='*112}")
print(f"  {'lev':<6}{'BTC tgt':>9}{'time':>7}{'P(win)':>9}{'P(loss)':>9}{'P(open)':>9}"
      f"{'gross %acct':>13}{'cost %acct':>12}{'NET %acct':>11}{'  per side':>12}")
for side,sn in (("LONG","LONG"),("SHORT","SHORT")):
    tp,sl=FP[sn]
    for k,(Lv,t) in enumerate(LEVS):
        for lim in (60,240,1440):
            win=(tp[:,k]<=lim)&(tp[:,k]<sl[:,k])
            los=(sl[:,k]<=lim)&~win
            opn=~win&~los
            # unresolved marked out at the limit
            j=np.minimum(ent+lim,n-1)
            mo=(C[j]/C[ent]-1)*100*(1 if sn=="LONG" else -1)
            gross=np.where(win,t,np.where(los,-t,mo))*Lv
            cost=COST["maker/taker"]*Lv
            net=gross-cost
            if lim==240:
                print(f"  {Lv:>3}x{'':<2}{t:>8.3f}%{lim:>6}m{win.mean():>9.1%}"
                      f"{los.mean():>9.1%}{opn.mean():>9.1%}{gross.mean():>+13.4f}"
                      f"{cost:>12.4f}{net.mean():>+11.4f}{sn:>12}")
pickle.dump({'ent':ent,'FP':FP,'TGT':TGT,'LEVS':LEVS},open("/tmp/acct_fp.pkl","wb"))
