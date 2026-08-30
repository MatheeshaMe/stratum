#!/usr/bin/env python3
"""PHASE 11 (derivatives at the breakout), 19 (A/B/C baselines), 17 (account sim)."""
import sys, os, pickle, numpy as np
sys.path.insert(0,'research/struct'); sys.path.insert(0,'research/btc3')
import zigzag as Z, backtest as BT, events as E
MAKER=1.5/1e4; TAKER=4.5/1e4; HALF=0.63/1e4
def boot(R,it=4000,seed=0):
    rg=np.random.default_rng(seed)
    return tuple(np.percentile([rg.choice(R,len(R)).mean() for _ in range(it)],[2.5,97.5]))
def load5(path):
    T,O,H,L,C,V,N=E.load(path)
    ms=5*60000; key=T-(T%ms)
    _,st=np.unique(key,return_index=True); st=np.sort(st); en=np.append(st[1:],len(T))
    b=dict(t=key[st],o=O[st],h=np.maximum.reduceat(H,st),l=np.minimum.reduceat(L,st),
           c=C[en-1],v=np.add.reduceat(V,st))
    A=Z.atr(b['h'],b['l'],b['c']); piv=Z.zigzag(b['h'],b['l'],A,theta=3.0)
    S=Z.structure_state(len(b['c']),piv)
    return b,A,S,Z.derived(b['c'],b['h'],b['l'],A,S)

b,A,S,D=load5("data/spot/BTCUSDT-1m.pkl")
c=b['c']; n=len(c)
tr_up=S['trend']==1; tr_dn=S['trend']==-1
bu=(c>S['last_sh']); bu[1:]&=~(c[:-1]>S['last_sh'][:-1])
bd=(c<S['last_sl']); bd[1:]&=~(c[:-1]<S['last_sl'][:-1])

# ---------------- PHASE 11: OI regime at the breakout -----------------------
print("="*94); print("PHASE 11 -- derivatives state AT the structural breakout (BTC, 2023-2026 coverage)")
print("="*94)
M=pickle.load(open("data/micro/metrics.pkl","rb"))
mt=np.array([r[0] for r in M]); oi=np.array([r[1] for r in M])
idx=np.searchsorted(mt,b['t'],side='right')-2      # last metrics row strictly before
ok=idx>=0
oi_al=np.full(n,np.nan); oi_al[ok]=oi[idx[ok]]
oi_al[oi_al<=0]=np.nan
oid=np.full(n,np.nan); oid[12:]=(oi_al[12:]-oi_al[:-12])/oi_al[:-12]
pd_=np.full(n,np.nan); pd_[12:]=(c[12:]-c[:-12])/c[:-12]
have=np.isfinite(oid)&np.isfinite(pd_)
print(f"  metrics coverage on the 5m grid: {have.mean():.1%} of bars\n")
print(f"  {'OI x price regime at breakout':<34}{'n':>7}{'win%':>8}{'EV R':>9}{'  95% CI':>22}{'PF':>7}")
for lbl,cond in (("price UP + OI UP (new longs)",(pd_>0)&(oid>0)),
                 ("price UP + OI DOWN (short cover)",(pd_>0)&(oid<0)),
                 ("price DN + OI UP (new shorts)",(pd_<0)&(oid>0)),
                 ("price DN + OI DOWN (long liq)",(pd_<0)&(oid<0))):
    m=have&cond
    tr=BT.run(b,A,S,D,tr_up&bu&m,tr_dn&bd&m,exit_mode="trail_struct")
    st=BT.stats(tr)
    if not st or st['n']<60: print(f"  {lbl:<34}{st['n'] if st else 0:>7}  too few"); continue
    R=np.array([t['R'] for t in tr]); lo,hi=boot(R)
    print(f"  {lbl:<34}{st['n']:>7}{st['win']:>8.1%}{st['ev']:>+9.3f}"
          f"   [{lo:+.3f},{hi:+.3f}]{st['pf']:>7.2f}")

# ---------------- PHASE 19: baselines A / B / C -----------------------------
print("\n"+"="*94); print("PHASE 19 -- A (indicator) vs B (structural rule) vs C (structural + ML)")
print("="*94)
def ema(x,p):
    k=2/(p+1); o=np.empty(len(x)); o[0]=x[0]
    for i in range(1,len(x)): o[i]=x[i]*k+o[i-1]*(1-k)
    return o
e9,e20=ema(c,9),ema(c,20)
xu=(e9>e20); xu[1:]&=~(e9[:-1]>e20[:-1])
xd=(e9<e20); xd[1:]&=~(e9[:-1]<e20[:-1])
rows=[]
trA=BT.run(b,A,S,D,xu,xd,exit_mode="trail_struct"); rows.append(("A  EMA9/20 cross",trA))
trB=BT.run(b,A,S,D,tr_up&bu,tr_dn&bd,exit_mode="trail_struct"); rows.append(("B  trend + BOS",trB))
trB2=BT.run(b,A,S,D,tr_up&bu&(D['efficiency']>0.35),tr_dn&bd&(D['efficiency']>0.35),
            exit_mode="trail_struct"); rows.append(("B2 + efficiency filter",trB2))
MODELS,MT,TT,SD,SY,Y=pickle.load(open("/tmp/p4_models.pkl","rb"))
P=MODELS[2.0]; s=np.isfinite(P)&(SY=="BTC")
sel=s&(P>=np.quantile(P[np.isfinite(P)],0.8))
rows.append(("C  + ML path model (top 20%)",[{'R':x} for x in MT[sel]]))
print(f"  {'baseline':<30}{'n':>7}{'win%':>8}{'EV R':>9}{'  95% CI':>22}{'PF':>7}{'totR':>9}")
for lbl,tr in rows:
    R=np.array([t['R'] for t in tr])
    if len(R)<50: continue
    w=R>0; lo,hi=boot(R)
    print(f"  {lbl:<30}{len(R):>7}{w.mean():>8.1%}{R.mean():>+9.3f}   [{lo:+.3f},{hi:+.3f}]"
          f"{R[w].sum()/max(-R[~w].sum(),1e-9):>7.2f}{R.sum():>+9.1f}")

# ---------------- PHASE 17: account simulation ------------------------------
print("\n"+"="*94); print("PHASE 17 -- $20 account simulation")
print("="*94)
sealedR=None
if os.path.exists("data/sealed_spot/BTCUSDT-1m.pkl"):
    b2,A2,S2,D2=load5("data/sealed_spot/BTCUSDT-1m.pkl")
    c2=b2['c']
    u2=S2['trend']==1; d2=S2['trend']==-1
    bu2=(c2>S2['last_sh']); bu2[1:]&=~(c2[:-1]>S2['last_sh'][:-1])
    bd2=(c2<S2['last_sl']); bd2[1:]&=~(c2[:-1]<S2['last_sl'][:-1])
    t2=BT.run(b2,A2,S2,D2,u2&bu2&(D2['efficiency']>0.35),d2&bd2&(D2['efficiency']>0.35),
              exit_mode="trail_struct")
    sealedR=np.array([t['R'] for t in t2])
POOLS={"discovery 2017-19+2023-26 (BTC)":np.array([t['R'] for t in trB2]),
       "sealed 2020-2022 (BTC)":sealedR}
for lbl,R in POOLS.items():
    if R is None: continue
    print(f"\n  pool: {lbl}   n={len(R)}  EV {R.mean():+.4f}R  win {(R>0).mean():.1%}")
    print(f"  {'risk/trade':<12}{'median $':>12}{'p25':>10}{'p75':>10}{'p5':>10}{'p95':>11}"
          f"{'medDD':>8}{'P(ruin)':>9}")
    for rf in (0.02,0.05,0.10,0.20):
        rng=np.random.default_rng(0); N=200; fin=[]; dds=[]; ruin=0
        for _ in range(20000):
            s2=rng.choice(R,N,replace=True)
            eq=20*np.cumprod(1+s2*rf)
            pk=np.maximum.accumulate(eq); dd=((pk-eq)/pk).max()
            fin.append(eq[-1]); dds.append(dd)
            if eq.min()<2: ruin+=1
        fin=np.array(fin)
        print(f"  {rf:<12.0%}{np.median(fin):>12,.2f}{np.percentile(fin,25):>10,.2f}"
              f"{np.percentile(fin,75):>10,.2f}{np.percentile(fin,5):>10,.2f}"
              f"{np.percentile(fin,95):>11,.2f}{np.median(dds):>8.1%}{ruin/20000:>9.2%}")
    print(f"    ({N} trades ~ {N/ (len(R)/ (9 if 'discovery' in lbl else 3)):.1f} years at the observed rate)")
