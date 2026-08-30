#!/usr/bin/env python3
"""Real vs false breakouts, MTF alignment, and conditional path behaviour.

The user's explicit request: even if unconditional returns are near-random, is
there CONDITIONAL path structure? This measures MFE/MAE by structural state,
which is descriptive value independent of whether an edge exists.
"""
import sys, os, pickle, numpy as np
sys.path.insert(0,'research/struct'); sys.path.insert(0,'research/btc3')
import zigzag as Z, events as E
T,O,H,L,C,V,N=E.load("data/spot/BTCUSDT-1m.pkl")
def agg(mins):
    ms=mins*60000; key=T-(T%ms)
    _,st=np.unique(key,return_index=True); st=np.sort(st); en=np.append(st[1:],len(T))
    return dict(t=key[st],o=O[st],h=np.maximum.reduceat(H,st),l=np.minimum.reduceat(L,st),
                c=C[en-1],v=np.add.reduceat(V,st),i1m=st)
b5=agg(5); A5=Z.atr(b5['h'],b5['l'],b5['c'])
p5=Z.zigzag(b5['h'],b5['l'],A5,theta=3.0); S5=Z.structure_state(len(b5['c']),p5)
D5=Z.derived(b5['c'],b5['h'],b5['l'],A5,S5)
b60=agg(60); A60=Z.atr(b60['h'],b60['l'],b60['c'])
p60=Z.zigzag(b60['h'],b60['l'],A60,theta=3.0); S60=Z.structure_state(len(b60['c']),p60)
# map 1h trend onto the 5m grid, causally (use the 1h bar that has CLOSED)
h_idx=np.searchsorted(b60['t'], b5['t'], side='right')-2
h_idx=np.clip(h_idx,0,len(b60['c'])-1)
trend_1h=S60['trend'][h_idx]
c=b5['c']; n=len(c)
tr_up=S5['trend']==1; tr_dn=S5['trend']==-1
bos_up=(c>S5['last_sh']); bos_up[1:]&=~(c[:-1]>S5['last_sh'][:-1])
bos_dn=(c<S5['last_sl']); bos_dn[1:]&=~(c[:-1]<S5['last_sl'][:-1])

# ---- real vs false breakout: after a BOS up, does price ACCEPT (2 closes above)
# within 12 bars, or return inside?
K=12
acc=np.zeros(n,bool); fail=np.zeros(n,bool)
lvl=S5['last_sh']
for i in np.where(bos_up)[0]:
    if i+K+1>=n or not np.isfinite(lvl[i]): continue
    seg=c[i+1:i+1+K]
    two=np.any((seg[:-1]>lvl[i])&(seg[1:]>lvl[i]))
    back=np.any(seg<lvl[i])
    if two and not back: acc[i]=True
    elif back and not two: fail[i]=True
print(f"BOS-up events: {int(bos_up.sum()):,}   accepted {int(acc.sum()):,} "
      f"({acc.sum()/max(bos_up.sum(),1):.1%})   failed {int(fail.sum()):,} "
      f"({fail.sum()/max(bos_up.sum(),1):.1%})   ambiguous rest")
print("\nWhat distinguishes a REAL from a FALSE breakout, measured AT the breakout bar?")
vma=np.convolve(b5['v'],np.ones(20)/20,'full')[:n]
feat={'volume vs 20-bar avg':b5['v']/np.where(vma==0,np.nan,vma),
      'close location in bar':(c-b5['l'])/np.where(b5['h']-b5['l']==0,np.nan,b5['h']-b5['l']),
      'displacement (bar range / ATR)':(b5['h']-b5['l'])/A5,
      'trend efficiency':D5['efficiency'],
      'impulse size (ATR)':D5['imp_atr'],
      '5m trend = up':(S5['trend']==1).astype(float),
      '1h trend = up':(trend_1h==1).astype(float),
      'pullback depth':D5['pb_frac']}
print(f"  {'feature':<34}{'accepted':>11}{'failed':>10}{'diff':>10}{'Cohen d':>10}")
for k,v in feat.items():
    a=v[acc]; f=v[fail]; a=a[np.isfinite(a)]; f=f[np.isfinite(f)]
    if len(a)<50 or len(f)<50: continue
    s=np.sqrt(((len(a)-1)*a.var(ddof=1)+(len(f)-1)*f.var(ddof=1))/(len(a)+len(f)-2))
    print(f"  {k:<34}{a.mean():>11.3f}{f.mean():>10.3f}{a.mean()-f.mean():>+10.3f}"
          f"{(a.mean()-f.mean())/s if s>0 else np.nan:>+10.2f}")

# ---- conditional path behaviour: MFE/MAE in ATR by structural state, 48 bars fwd
FW=48
print(f"\n\nCONDITIONAL PATH BEHAVIOUR -- MFE/MAE over the next {FW} bars ({FW*5}min), in ATR")
print(f"  {'structural state':<38}{'n':>8}{'MFE':>8}{'MAE':>8}{'MFE/MAE':>9}"
      f"{'MFE-MAE':>9}{'P(MFE>2ATR)':>13}")
Hh=b5['h']; Ll=b5['l']
def path_stats(m, lbl):
    idx=np.where(m)[0]; idx=idx[(idx>200)&(idx<n-FW-2)]
    if len(idx)<200: return
    mfe=np.array([ (Hh[i+1:i+1+FW].max()-c[i])/A5[i] for i in idx])
    mae=np.array([ (c[i]-Ll[i+1:i+1+FW].min())/A5[i] for i in idx])
    ok=np.isfinite(mfe)&np.isfinite(mae)
    mfe,mae=mfe[ok],mae[ok]
    print(f"  {lbl:<38}{len(mfe):>8,}{np.median(mfe):>8.2f}{np.median(mae):>8.2f}"
          f"{np.median(mfe)/max(np.median(mae),1e-9):>9.2f}"
          f"{np.median(mfe)-np.median(mae):>+9.2f}{(mfe>2).mean():>13.1%}")
path_stats(np.ones(n,bool),"ALL BARS (baseline)")
path_stats(tr_up,"5m uptrend (HH+HL)")
path_stats(tr_dn,"5m downtrend (LH+LL)")
path_stats(S5['trend']==0,"5m no clear structure")
path_stats(bos_up,"BOS up (break of swing high)")
path_stats(acc,"BOS up -> ACCEPTED")
path_stats(fail,"BOS up -> FAILED")
path_stats(tr_up&(trend_1h==1),"5m up AND 1h up (aligned)")
path_stats(tr_up&(trend_1h==-1),"5m up BUT 1h down (conflict)")
path_stats(tr_up&bos_up&(trend_1h==1),"aligned + BOS up")
path_stats(D5['efficiency']>0.40,"high trend efficiency (>0.40)")
path_stats(D5['efficiency']<0.15,"low trend efficiency (<0.15)")
