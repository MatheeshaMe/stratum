#!/usr/bin/env python3
"""§22 — which observations distinguish future market behaviour?

The question is NOT 'does this have positive EV'. It is 'does conditioning on
this observation change the forward DISTRIBUTION'. A distribution can differ in
variance, skew or tail with an identical mean, and for a trader that is
information -- it changes sizing, target selection and whether to participate.

Four kinds of information are measured separately:
  DIRECTIONAL  mean forward return shifts          -> tells you which way
  MAGNITUDE    |forward return| / realised range   -> tells you how far
  SHAPE        skew and tail mass                  -> tells you the payoff form
  TIMING       bars to resolve a +/-1 ATR barrier  -> tells you how long

Everything is in ATR units so regimes are comparable. Block bootstrap
throughout, because observations are autocorrelated.
"""
import sys, os, pickle, numpy as np
sys.path.insert(0,'research/interp'); sys.path.insert(0,'research/btc3')
import observe as OB, events as E
from numpy.lib.stride_tricks import sliding_window_view

FWD=48                      # 4h on a 5m base grid
def block_ci(x, block=FWD, iters=1500, seed=0):
    x=x[np.isfinite(x)]
    if len(x)<50: return (np.nan,np.nan)
    rg=np.random.default_rng(seed); nb=int(np.ceil(len(x)/block)); m=np.empty(iters)
    for k in range(iters):
        st=rg.integers(0,len(x),nb)
        s=np.concatenate([np.take(x,np.arange(i,i+block),mode='wrap') for i in st])[:len(x)]
        m[k]=s.mean()
    return np.percentile(m,2.5),np.percentile(m,97.5)

def forward_stats(b, A):
    C,H,L=b['c'],b['h'],b['l']; n=len(C)
    fret=np.full(n,np.nan); frange=np.full(n,np.nan); ttr=np.full(n,np.nan)
    Hs=sliding_window_view(H,FWD); Ls=sliding_window_view(L,FWD)
    m=n-FWD-1
    fret[:m]=(C[FWD+1:FWD+1+m]-C[:m])/A[:m]
    frange[:m]=(Hs[1:1+m].max(1)-Ls[1:1+m].min(1))/A[:m]
    # bars to resolve a +/-1 ATR barrier
    for i in range(0,m,1):
        a=A[i]
        if not np.isfinite(a) or a<=0: continue
        up=np.argmax(H[i+1:i+1+FWD]>=C[i]+a) if (H[i+1:i+1+FWD]>=C[i]+a).any() else 10**6
        dn=np.argmax(L[i+1:i+1+FWD]<=C[i]-a) if (L[i+1:i+1+FWD]<=C[i]-a).any() else 10**6
        r=min(up,dn)
        ttr[i]=r if r<10**6 else FWD
    return fret, frange, ttr

if __name__=="__main__":
    T,O,H,L,C,V,N=E.load("data/spot/BTCUSDT-1m-full.pkl")
    CACHE="/tmp/interp_obs.pkl"
    if os.path.exists(CACHE):
        bb,al=pickle.load(open(CACHE,"rb"))
    else:
        bb,al,_,_=OB.build(T,O,H,L,C,V,base_tf="5m")
        pickle.dump((bb,al),open(CACHE,"wb"))
    A=al["5m.atr"]; n=len(bb['c'])
    fret,frange,ttr=forward_stats(bb,A)
    ok=np.isfinite(fret)&np.isfinite(frange)&np.isfinite(A)&(A>0)
    ok[:2000]=False
    base_mu=fret[ok].mean(); base_sd=fret[ok].std()
    base_absmu=np.abs(fret[ok]).mean(); base_rng=np.median(frange[ok])
    base_tail=(np.abs(fret[ok])>2).mean(); base_ttr=np.median(ttr[ok])
    print(f"BASELINE over {ok.sum():,} bars (forward {FWD*5/60:.0f}h, ATR units)")
    print(f"  mean {base_mu:+.4f}  sd {base_sd:.3f}  |mean| {base_absmu:.3f}  "
          f"median range {base_rng:.2f}  P(|move|>2ATR) {base_tail:.1%}  "
          f"median bars-to-1ATR {base_ttr:.0f}\n")

    events={k:v for k,v in al.items()
            if v.dtype.kind in "ib" and set(np.unique(v[ok])[:3]).issubset({0,1})}
    rows=[]
    for k,v in events.items():
        m=ok&(v==1)
        if m.sum()<400: continue
        fr=fret[m]; rg=frange[m]; tt=ttr[m]
        d_mu=fr.mean()-base_mu
        lo,hi=block_ci(fret[m]-base_mu)
        rows.append(dict(name=k,n=int(m.sum()),
            d_mu=d_mu, mu_lo=lo, mu_hi=hi,
            sd_ratio=fr.std()/base_sd,
            absmu_ratio=np.abs(fr).mean()/base_absmu,
            rng_ratio=np.median(rg)/base_rng,
            tail_ratio=((np.abs(fr)>2).mean())/max(base_tail,1e-9),
            ttr_ratio=np.median(tt)/max(base_ttr,1e-9),
            skew=float(((fr-fr.mean())**3).mean()/max(fr.std()**3,1e-9))))
    pickle.dump(rows,open("/tmp/interp_div.pkl","wb"))
    print(f"binary observations with n>=400: {len(rows)}\n")
    print("="*112)
    print("DIRECTIONAL INFORMATION — does the MEAN shift? (ranked by |shift|)")
    print("="*112)
    print(f"{'observation':<42}{'n':>8}{'Δmean':>9}{'  95% CI':>22}{'sig':>5}")
    ds=sorted(rows,key=lambda r:-abs(r['d_mu']))
    nsig=0
    for r in ds[:14]:
        s="*" if (r['mu_lo']>0 or r['mu_hi']<0) else ""
        if s: nsig+=1
        print(f"{r['name']:<42}{r['n']:>8,}{r['d_mu']:>+9.4f}"
              f"   [{r['mu_lo']:+.4f},{r['mu_hi']:+.4f}]{s:>5}")
    tot_sig=sum(1 for r in rows if r['mu_lo']>0 or r['mu_hi']<0)
    print(f"\n  observations with a significant MEAN shift: {tot_sig} of {len(rows)}"
          f"   (expected by chance ~{0.05*len(rows):.0f})")
    print(f"  largest |Δmean| anywhere: {abs(ds[0]['d_mu']):.4f} ATR")
    print("\n" + "="*112)
    print("MAGNITUDE INFORMATION — does the SIZE of the move change?")
    print("="*112)
    print(f"{'observation':<42}{'n':>8}{'|mean| x':>10}{'sd x':>8}{'range x':>10}"
          f"{'tail x':>9}{'bars-to-1ATR x':>16}")
    for r in sorted(rows,key=lambda r:-r['rng_ratio'])[:12]:
        print(f"{r['name']:<42}{r['n']:>8,}{r['absmu_ratio']:>10.2f}{r['sd_ratio']:>8.2f}"
              f"{r['rng_ratio']:>10.2f}{r['tail_ratio']:>9.2f}{r['ttr_ratio']:>16.2f}")
    print("\n  (x = ratio to the unconditional baseline; 1.00 means no information)")
