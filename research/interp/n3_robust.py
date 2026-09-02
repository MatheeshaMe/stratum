import sys,pickle,numpy as np
sys.path.insert(0,'research/interp'); sys.path.insert(0,'research/btc3')
import observe as OB, behavior as BH, tree as TR, n3_decomp as N3, events as E
def load(p):
    T,O,H,L,C,V,N=E.load(p)
    bb,al,_,_=OB.build(T,O,H,L,C,V,base_tf="5m")
    idx,F=BH.forward_block(bb,al["5m.atr"],FWD=48,stride=1)
    tr=TR.build_tree(bb,al,tf="15m",W=12,disp_atr=0.5)
    pos=np.zeros(len(bb['c']),np.int64)-1; pos[idx]=np.arange(len(idx))
    m=np.zeros(len(idx),bool); s=pos[np.where(tr["lo_raw"])[0]]; s=s[s>=0]; m[s]=True
    return F["fret"], m
print("IS KAPPA'S INSTABILITY A FAT-TAIL ARTIFACT?\n")
print(f"  {'asset':<8}{'kurtosis':>10}{'raw κ':>10}{'κ @1% winsor':>15}"
      f"{'κ @5% winsor':>15}{'Δmean raw':>12}{'Δmean w5%':>12}")
for sym,p in (("BTC","data/spot/BTCUSDT-1m-full.pkl"),("ETH","data/alt/ETHUSDT-1m.pkl"),
              ("SOL","data/alt/SOLUSDT-1m.pkl"),("XRP","data/alt/XRPUSDT-1m.pkl"),
              ("DOGE","data/alt/DOGEUSDT-1m.pkl")):
    fr,m=load(p)
    v=fr[np.isfinite(fr)]
    kurt=float(((v-v.mean())**4).mean()/max(v.std()**4,1e-9))
    out=[]
    for w in (0.0,0.01,0.05):
        if w>0:
            lo,hi=np.nanquantile(fr[np.isfinite(fr)],[w,1-w])
            f2=np.clip(fr,lo,hi)
        else: f2=fr
        r=N3.decompose(f2[m],f2)
        out.append((r['kappa'] if r else np.nan, r['d_mean'] if r else np.nan))
    print(f"  {sym:<8}{kurt:>10.1f}{out[0][0]:>10.2f}{out[1][0]:>15.2f}"
          f"{out[2][0]:>15.2f}{out[0][1]:>+12.3f}{out[2][1]:>+12.3f}")
print("\n  If κ stabilises under winsorisation, the cross-asset disagreement was")
print("  a handful of extreme bars, not a difference in market behaviour.")
