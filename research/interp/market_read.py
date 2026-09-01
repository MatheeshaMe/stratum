#!/usr/bin/env python3
"""§28 — the market read. Observation / interpretation / hypothesis / invalidation
kept strictly separate (§11), competing narratives held simultaneously (§8),
and "I don't know" as a first-class output (§20).

Every claim carries the measured information class behind it:
  [MAG]  magnitude/timing info that replicated across 6 era-asset cells
  [DIR?] directional info that did NOT replicate -- reported, never acted on
  [OBS]  a bare observation with no validated forward information
"""
import sys, os, pickle, numpy as np
sys.path.insert(0,'research/interp'); sys.path.insert(0,'research/btc3')
import observe as OB, events as E

# information classes, from validate.py: sign replication across 6 cells
REPLICATED_MAG = {"5m.accept_hi","5m.accept_lo","5m.seq.compress_expand_up",
                  "5m.seq.compress_expand_dn","4h.sweep_lo","4h.sweep_hi",
                  "1h.seq.sweep_accept_up","4h.seq.sweep_accept_up"}
REPLICATED_DIR = {"4h.sweep_lo"}          # the only one that held its sign everywhere

def read(al, bb, i):
    g=lambda k: al[k][i] if k in al else np.nan
    L=[]
    def obs(txt, tag="OBS"): L.append((tag,txt))

    # ── multi-timeframe structure, never collapsed to one label (§1,§2)
    tn={1:"bullish",-1:"bearish",0:"unresolved"}
    L.append(("HDR","STRUCTURE (each timeframe stated separately)"))
    for tf in ("4h","1h","15m","5m"):
        t=g(f"{tf}.trend")
        obs(f"{tf:<4} {tn.get(int(t) if np.isfinite(t) else 0,'unresolved')}"
            f"   swing {g(f'{tf}.swing_mag_atr'):.1f} ATR" if np.isfinite(g(f'{tf}.swing_mag_atr'))
            else f"{tf:<4} {tn.get(int(t) if np.isfinite(t) else 0,'unresolved')}")

    # ── location
    L.append(("HDR","LOCATION"))
    rp=g("4h.range_pos")
    if np.isfinite(rp):
        z="discount" if rp<0.33 else ("premium" if rp>0.67 else "mid-range")
        obs(f"4h range position {rp:.2f} ({z})")
    obs(f"5m volatility percentile {g('5m.vol_pct'):.2f}" if np.isfinite(g('5m.vol_pct')) else "volatility unknown")

    # ── liquidity: the EVENT, not its meaning (§4,§18)
    L.append(("HDR","LIQUIDITY"))
    any_lq=False
    for tf in ("4h","1h","15m","5m"):
        for k,desc in ((f"{tf}.sweep_lo","sell-side liquidity swept (poke + close back)"),
                       (f"{tf}.sweep_hi","buy-side liquidity swept (poke + close back)"),
                       (f"{tf}.accept_lo","ACCEPTED below the pool (two closes)"),
                       (f"{tf}.accept_hi","ACCEPTED above the pool (two closes)")):
            if g(k)==1:
                tag="MAG" if k in REPLICATED_MAG else ("DIR?" if k in REPLICATED_DIR else "OBS")
                obs(f"{tf:<4} {desc}", tag); any_lq=True
    if not any_lq: obs("no liquidity interaction on any timeframe")

    # ── sequences (§5): meaning comes from what FOLLOWED the event
    L.append(("HDR","SEQUENCES COMPLETED"))
    any_sq=False
    for k in [x for x in al if ".seq." in x]:
        if g(k)==1:
            tag="MAG" if k in REPLICATED_MAG else "OBS"
            obs(f"{k.replace('.seq.',' : ')}", tag); any_sq=True
    if not any_sq: obs("no completed sequence")

    # ── competing narratives, both held (§8,§12)
    L.append(("HDR","COMPETING NARRATIVES"))
    bull=[]; bear=[]
    if g("4h.trend")==1: bull.append("4h structure bullish")
    if g("4h.trend")==-1: bear.append("4h structure bearish")
    if g("1h.trend")==1: bull.append("1h structure bullish")
    if g("1h.trend")==-1: bear.append("1h structure bearish")
    if np.isfinite(rp) and rp<0.33: bull.append("price at a 4h discount")
    if np.isfinite(rp) and rp>0.67: bear.append("price at a 4h premium")
    for tf in ("4h","1h"):
        if g(f"{tf}.sweep_lo")==1: bull.append(f"{tf} sell-side swept")
        if g(f"{tf}.sweep_hi")==1: bear.append(f"{tf} buy-side swept")
        if g(f"{tf}.accept_hi")==1: bull.append(f"{tf} acceptance above pool")
        if g(f"{tf}.accept_lo")==1: bear.append(f"{tf} acceptance below pool")
    obs(f"BULLISH evidence ({len(bull)}): " + ("; ".join(bull) if bull else "none"))
    obs(f"BEARISH evidence ({len(bear)}): " + ("; ".join(bear) if bear else "none"))

    # ── assessment, honest about what the measurement supports (§20)
    L.append(("HDR","ASSESSMENT"))
    mag_on=[k for k in REPLICATED_MAG if g(k)==1]
    if mag_on:
        rng_hint="faster and larger" if any("compress_expand" in k or "accept" in k for k in mag_on) else "different"
        obs(f"MAGNITUDE: {len(mag_on)} replicated magnitude/timing observation(s) active "
            f"-> expect resolution {rng_hint} than baseline", "MAG")
    else:
        obs("MAGNITUDE: nothing active -> expect a baseline-speed market", "MAG")
    obs("DIRECTION: no directional observation in this engine replicated its sign "
        "across eras AND assets. Direction is NOT claimed.", "DIR?")
    if len(bull)>0 and len(bear)>0:
        obs("Narratives CONFLICT. The honest read is: I don't know.")
    elif len(bull)==0 and len(bear)==0:
        obs("No evidence either way. No thesis.")
    else:
        obs(f"Evidence leans {'bullish' if bull else 'bearish'}, but see the DIRECTION line.")

    L.append(("HDR","ACTION"))
    obs("WAIT — this engine is an interpreter. It does not size or fire orders. "
        "No directional observation cleared validation, so no trade thesis is issued.")
    return L

def render(L):
    out=[]
    for tag,txt in L:
        if tag=="HDR": out.append(f"\n  {txt}\n  " + "-"*len(txt))
        else: out.append(f"    [{tag:<4}] {txt}")
    return "\n".join(out)

if __name__=="__main__":
    bb,al=pickle.load(open("/tmp/interp_obs.pkl","rb"))
    n=len(bb['c'])
    rng=np.random.default_rng(3)
    print("="*84); print("  MARKET READ — sampled timestamps, BTC 5m base grid"); print("="*84)
    shown=0
    for i in rng.integers(300000,n-100,60):
        i=int(i)
        seq_active=any(al[k][i]==1 for k in al if ".seq." in k)
        if not seq_active and shown>0: continue
        ts=np.datetime64(int(bb['t'][i]),'ms')
        print(f"\n{'='*84}\n  {ts}   close {bb['c'][i]:,.2f}\n{'='*84}")
        print(render(read(al,bb,i)))
        shown+=1
        if shown>=3: break
