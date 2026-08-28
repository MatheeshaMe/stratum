"""Breakout / continuation harness -- the complement to engine.py.

Charges taker-in + taker-out, because a breakout entry must cross the spread.
Section 9.3 H2 in STRATUM.md uses this. Results did not hold sign across the
two validation periods; treat any output as unproven.
"""
import math, statistics as st
MAKER=1.5/1e4; TAKER=4.5/1e4; HALF=0.6/1e4
def agg(rows,mins):
    ms=mins*60000; out=[];idx=[];cur=None;ci=0
    for k,(t,o,h,l,c,v,n) in enumerate(rows):
        b=t-(t%ms)
        if cur is None or cur[0]!=b:
            if cur: out.append(cur);idx.append(ci)
            cur=[b,o,h,l,c,v,n];ci=k
        else:
            cur[2]=max(cur[2],h);cur[3]=min(cur[3],l);cur[4]=c;cur[5]+=v;cur[6]+=n
    if cur: out.append(cur);idx.append(ci)
    return out,idx
def atr14(b):
    tr=[b[0][2]-b[0][3]]
    for i in range(1,len(b)): tr.append(max(b[i][2]-b[i][3],abs(b[i][2]-b[i-1][4]),abs(b[i][3]-b[i-1][4])))
    a=[None]*len(b); s=sum(tr[:14])/14; a[13]=s
    for i in range(14,len(b)): s=(s*13+tr[i])/14; a[i]=s
    return a
def run(rows,TF=60,L=3,R=3,cluster_atr=.25,break_atr=.15,stop_atr=2.0,rr=1.5,min_touches=2,
        ttl=300,max_hold=96,rebuild=4,cool=8,ema=0,need_vol=0.0,entry_mode='market'):
    b,idx=agg(rows,TF); A=atr14(b); n=len(b)
    H1=[r[2] for r in rows];L1=[r[3] for r in rows];C1=[r[4] for r in rows];T1=[r[0] for r in rows]
    kf,ks=2/21,2/51; ef=[0]*n; es=[0]*n; ef[0]=es[0]=b[0][4]
    for i in range(1,n): ef[i]=b[i][4]*kf+ef[i-1]*(1-kf); es[i]=b[i][4]*ks+es[i-1]*(1-ks)
    V=[x[5] for x in b]; vs=[None]*n; s=sum(V[:20])
    for i in range(20,n): vs[i]=s/20; s+=V[i]-V[i-20]
    hi=[x[2] for x in b]; lo=[x[3] for x in b]
    swh=[];swl=[];CH=[];CL=[];trades=[];cd=-1
    for i in range(60,n-1):
        a=A[i]
        if not a or not vs[i]: continue
        p=i-R
        if p>L:
            if hi[p]==max(hi[p-L:p+R+1]): swh.append((p,hi[p]))
            if lo[p]==min(lo[p-L:p+R+1]): swl.append((p,lo[p]))
        if i%rebuild==0:
            def bld(sws):
                out=[]
                for ix,pr in sws[-200:]:
                    if i-ix>ttl: continue
                    h2=None
                    for c2 in out:
                        if abs(pr-c2[0])<=cluster_atr*a: h2=c2;break
                    if h2: h2[0]=(h2[0]*h2[1]+pr)/(h2[1]+1);h2[1]+=1;h2[2]=max(h2[2],ix)
                    else: out.append([pr,1,ix])
                return [c2 for c2 in out if c2[1]>=min_touches]
            CH=bld(swh);CL=bld(swl)
        if i<cd: continue
        cur=b[i]; c=cur[4]
        if need_vol and V[i] < need_vol*vs[i]: continue
        for (lvl,tc,lix),sd in [(x,+1) for x in CH]+[(x,-1) for x in CL]:
            if i-lix<2: continue
            # BREAKOUT: close beyond the level by break_atr
            if sd>0:
                if not(c > lvl + break_atr*a and b[i-1][4] <= lvl + break_atr*a): continue
                if ema and ef[i]<es[i]: continue
            else:
                if not(c < lvl - break_atr*a and b[i-1][4] >= lvl - break_atr*a): continue
                if ema and ef[i]>es[i]: continue
            entry=c; stop=entry-sd*stop_atr*a
            risk=abs(stop-entry); tgt=entry+sd*risk*rr
            if not(0.0015<=risk/entry<=0.030): continue
            j0=idx[i+1]; lim=min(j0+max_hold*TF,len(rows)); res=None
            for j in range(j0,lim):
                if sd>0:
                    if L1[j]<=stop: res=-1.0;break
                    if H1[j]>=tgt: res=float(rr);break
                else:
                    if H1[j]>=stop: res=-1.0;break
                    if L1[j]<=tgt: res=float(rr);break
            if res is None: res=sd*(C1[lim-1]-entry)/risk
            cost=((TAKER+HALF)+(TAKER+HALF))*entry/risk   # taker in, taker out (breakout must cross)
            trades.append((res-cost,risk/entry,cur[0])); cd=i+cool; break
    if not trades: return None
    Rs=[x[0] for x in trades]
    cst=st.mean((TAKER+HALF)*2/x[1] for x in trades)
    days=(T1[-1]-T1[0])/86400000
    return dict(n=len(Rs),net=st.mean(Rs),cost=cst,gross=st.mean(Rs)+cst,
        win=sum(1 for r in Rs if r>0)/len(Rs),perday=len(Rs)/days,
        t=st.mean(Rs)/(st.pstdev(Rs)+1e-9)*math.sqrt(len(Rs)),tr=trades)
