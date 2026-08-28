"""Reference backtest harness for Stratum.

Pessimistic by construction: post-only entries fill only when a 1m bar trades
through the limit; stop and target in the same 1m bar always resolves to the
stop; every trade is charged maker-in + taker-out + half-spread.

The Rust backtester in stratum-backtest must match this to 1e-9 on the golden
fixture. This module is the reference, not a prototype.
"""
import math, statistics as st

MAKER = 1.5 / 1e4      # Hyperliquid maker, VIP 0
TAKER = 4.5 / 1e4      # Hyperliquid taker, VIP 0
HALF  = 0.63 / 1e4     # half-spread, BTC $1 tick on ~$79,850

def agg(rows, mins):
    """1m bars -> mins bars. Returns (bars, index_into_rows_of_each_bar_open)."""
    ms = mins * 60000; out = []; idx = []; cur = None; ci = 0
    for k, (t, o, h, l, c, v, n) in enumerate(rows):
        b = t - (t % ms)
        if cur is None or cur[0] != b:
            if cur: out.append(cur); idx.append(ci)
            cur = [b, o, h, l, c, v, n]; ci = k
        else:
            cur[2] = max(cur[2], h); cur[3] = min(cur[3], l)
            cur[4] = c; cur[5] += v; cur[6] += n
    if cur: out.append(cur); idx.append(ci)
    return out, idx

def atr14(b):
    tr = [b[0][2] - b[0][3]]
    for i in range(1, len(b)):
        tr.append(max(b[i][2]-b[i][3], abs(b[i][2]-b[i-1][4]), abs(b[i][3]-b[i-1][4])))
    a = [None]*len(b); s = sum(tr[:14])/14; a[13] = s
    for i in range(14, len(b)):
        s = (s*13 + tr[i])/14; a[i] = s
    return a

def run(rows, TF=60,L=3,R=3,cluster_atr=.25,touch_atr=.20,stop_atr=2.0,rr=1.5,min_touches=2,
        ttl=300,max_hold=96,rebuild=4,cool=8,ema=0,
        need_wick=0,wick_mult=1.5,vol_weak=0.0,hour_lo=None,hour_hi=None,need_climax=0):
    b,idx=agg(rows,TF); A=atr14(b); n=len(b)
    H1=[r[2] for r in rows]; L1=[r[3] for r in rows]
    C1=[r[4] for r in rows]; T1=[r[0] for r in rows]
    kf,ks=2/21,2/51; ef=[0]*n; es=[0]*n; ef[0]=es[0]=b[0][4]
    for i in range(1,n): ef[i]=b[i][4]*kf+ef[i-1]*(1-kf); es[i]=b[i][4]*ks+es[i-1]*(1-ks)
    V=[x[5] for x in b]
    vs=[None]*n; s=sum(V[:20])
    for i in range(20,n): vs[i]=s/20; s+=V[i]-V[i-20]
    hi=[x[2] for x in b]; lo=[x[3] for x in b]
    swh=[];swl=[];CH=[];CL=[];trades=[];cd=-1
    for i in range(60,n-1):
        a=A[i]
        if not a or not vs[i]: continue
        p=i-R
        if p>L:
            if hi[p]==max(hi[p-L:p+R+1]): swh.append((p,hi[p],V[p]))
            if lo[p]==min(lo[p-L:p+R+1]): swl.append((p,lo[p],V[p]))
        if i%rebuild==0:
            def bld(sws):
                out=[]
                for ix,pr,vv in sws[-200:]:
                    if i-ix>ttl: continue
                    h2=None
                    for c2 in out:
                        if abs(pr-c2[0])<=cluster_atr*a: h2=c2;break
                    if h2: h2[0]=(h2[0]*h2[1]+pr)/(h2[1]+1); h2[1]+=1; h2[2]=max(h2[2],ix); h2[3]=vv
                    else: out.append([pr,1,ix,vv])
                return [c2 for c2 in out if c2[1]>=min_touches]
            CH=bld(swh); CL=bld(swl)
        if i<cd: continue
        cur=b[i]; o,h,l,c=cur[1],cur[2],cur[3],cur[4]
        body=abs(c-o)+1e-9
        if hour_lo is not None:
            hr=(cur[0]//3600000)%24
            if not(hour_lo<=hr<hour_hi): continue
        cands=[(c2,-1) for c2 in CH]+[(c2,+1) for c2 in CL]
        for (lvl,tc,lix,pv),sd in cands:
            if i-lix<2 or abs(c-lvl)>3*a: continue
            if sd<0:
                if not(h>=lvl-touch_atr*a and c<lvl): continue
                if need_wick and (h-max(o,c))<wick_mult*body: continue
                if ema and ef[i]>es[i]: continue
                entry=lvl; stop=lvl+stop_atr*a
            else:
                if not(l<=lvl+touch_atr*a and c>lvl): continue
                if need_wick and (min(o,c)-l)<wick_mult*body: continue
                if ema and ef[i]<es[i]: continue
                entry=lvl; stop=lvl-stop_atr*a
            if vol_weak and not(V[i] < vol_weak*pv): continue
            if need_climax and not(V[i] > 2.0*vs[i]): continue
            risk=abs(stop-entry); tgt=entry+sd*risk*rr
            if not(0.0015<=risk/entry<=0.030): continue
            j0=idx[i+1]; filled=False; res=None; lim=min(j0+max_hold*TF,len(rows))
            for j in range(j0,lim):
                if not filled:
                    if (sd<0 and H1[j]>=entry) or (sd>0 and L1[j]<=entry): filled=True
                    elif j-j0>TF*4: break
                    else: continue
                if sd<0:
                    if H1[j]>=stop: res=-1.0;break
                    if L1[j]<=tgt: res=float(rr);break
                else:
                    if L1[j]<=stop: res=-1.0;break
                    if H1[j]>=tgt: res=float(rr);break
            if not filled: continue
            if res is None: res=sd*(C1[lim-1]-entry)/risk
            cost=(MAKER+TAKER+HALF)*entry/risk
            trades.append((res-cost,risk/entry,cur[0])); cd=i+cool; break
    if not trades: return None
    Rs=[t[0] for t in trades]
    cst=st.mean((MAKER+TAKER+HALF)/x[1] for x in trades)
    days=(T1[-1]-T1[0])/86400000
    return dict(n=len(Rs),net=st.mean(Rs),cost=cst,gross=st.mean(Rs)+cst,
        win=sum(1 for r in Rs if r>0)/len(Rs),perday=len(Rs)/days,
        t=st.mean(Rs)/(st.pstdev(Rs)+1e-9)*math.sqrt(len(Rs)),stop=st.median(x[1] for x in trades)*100, tr=trades)
