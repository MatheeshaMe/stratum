"""Structural backtest with UNBOUNDED exits.

The methodological point of this module: every prior Stratum phase used fixed
target barriers, which truncates the right tail. A trend system's entire thesis
is that the right tail pays for a low win rate. Fixed barriers cannot test that.
Here the primary exit is a TRAILING STRUCTURAL STOP with no profit cap.

Causality: state at bar i uses only pivots CONFIRMED at or before i.
Fills are at the open of bar i+1. R is measured against the initial risk.
"""
import numpy as np

MAKER=1.5/1e4; TAKER=4.5/1e4; HALF=0.63/1e4

def run(b, A, S, D, sig_long, sig_short, exit_mode="trail_struct",
        rr=None, time_stop=None, cost_entry="taker", cost_exit="taker",
        max_bars=2000, risk_buffer=0.25):
    """sig_long/sig_short: boolean arrays, signal known AT bar i.
    Returns list of dicts, one per trade."""
    O,H,L,C=b['o'],b['h'],b['l'],b['c']; n=len(C)
    lsh,lsl=S['last_sh'],S['last_sl']
    ec=(TAKER+HALF) if cost_entry=="taker" else MAKER
    xc=(TAKER+HALF) if cost_exit=="taker" else MAKER
    trades=[]; busy=-1
    for i in range(200, n-2):
        if i<=busy: continue
        side=0
        if sig_long[i]: side=+1
        elif sig_short[i]: side=-1
        if side==0: continue
        a=A[i]
        if not np.isfinite(a) or a<=0: continue
        entry=O[i+1]
        if side>0:
            stop0=lsl[i]-risk_buffer*a
        else:
            stop0=lsh[i]+risk_buffer*a
        if not np.isfinite(stop0): continue
        risk=abs(entry-stop0)
        if risk<=0 or risk/entry<0.0015 or risk/entry>0.08: continue
        tgt=entry+side*rr*risk if rr else None
        stop=stop0; ex_i=None; ex_px=None; reason=None
        for j in range(i+1, min(i+1+max_bars, n)):
            # trailing structural stop -- ratchet behind confirmed swings only
            if exit_mode=="trail_struct":
                if side>0 and np.isfinite(lsl[j]) and lsl[j]-risk_buffer*A[j]>stop:
                    stop=lsl[j]-risk_buffer*A[j]
                if side<0 and np.isfinite(lsh[j]) and lsh[j]+risk_buffer*A[j]<stop:
                    stop=lsh[j]+risk_buffer*A[j]
            elif exit_mode=="trail_atr":
                if side>0: stop=max(stop, C[j-1]-3*A[j])
                else:      stop=min(stop, C[j-1]+3*A[j])
            hit_stop=(L[j]<=stop) if side>0 else (H[j]>=stop)
            hit_tgt=(rr is not None) and ((H[j]>=tgt) if side>0 else (L[j]<=tgt))
            if hit_stop and hit_tgt:            # ambiguity -> the stop
                ex_i,ex_px,reason=j,stop,"stop"; break
            if hit_stop: ex_i,ex_px,reason=j,stop,"stop"; break
            if hit_tgt:  ex_i,ex_px,reason=j,tgt,"target"; break
            if time_stop and j-i>=time_stop:
                ex_i,ex_px,reason=j,C[j],"time"; break
        if ex_i is None:
            ex_i=min(i+max_bars,n-1); ex_px=C[ex_i]; reason="maxbars"
        gross=side*(ex_px-entry)/risk
        cost=(ec+xc)*entry/risk
        mfe=(H[i+1:ex_i+1].max()-entry)/risk if side>0 else (entry-L[i+1:ex_i+1].min())/risk
        mae=(entry-L[i+1:ex_i+1].min())/risk if side>0 else (H[i+1:ex_i+1].max()-entry)/risk
        trades.append(dict(i=i, t=b['t'][i], side=side, R=gross-cost, gross=gross,
                           cost=cost, bars=ex_i-i, reason=reason,
                           mfe=mfe, mae=mae, risk_pct=risk/entry*100))
        busy=ex_i
    return trades

def stats(tr, label=""):
    if len(tr)<20: return None
    R=np.array([t['R'] for t in tr]); B=np.array([t['bars'] for t in tr])
    w=R>0
    gp=R[w].sum(); gl=-R[~w].sum()
    eq=np.cumsum(R); pk=np.maximum.accumulate(eq); dd=(pk-eq).max()
    return dict(label=label, n=len(R), win=w.mean(), ev=R.mean(),
                avg_w=R[w].mean() if w.any() else 0,
                avg_l=R[~w].mean() if (~w).any() else 0,
                pf=gp/gl if gl>0 else np.inf, tot=R.sum(), dd=dd,
                med_bars=np.median(B), t=R.mean()/(R.std()+1e-12)*np.sqrt(len(R)),
                p90=np.percentile(R,90), p99=np.percentile(R,99), mx=R.max())
