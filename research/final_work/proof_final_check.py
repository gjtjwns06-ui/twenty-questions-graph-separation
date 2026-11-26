"""Small independent exact recurrences; deliberately no project solver imports."""
import json
from fractions import Fraction as Q
from functools import cache
from pathlib import Path

base=json.loads(Path('runs/extremal_analysis_v1/fixed_degree3_base.json').read_text())
out={}
for b in (0,3):
    pair={}
    for label in ('a','b'):
        rows=[tuple(r) for r in base[label]['rows']]+[(0,5,8+j) for j in range(b)]
        n=len(rows)
        cols=[sum(1<<i for i,r in enumerate(rows) if q in r) for q in range(8+b)]
        @cache
        def f(s):
            if s.bit_count()<2:return 0
            return s.bit_count()+min(f(s&c)+f(s&~c) for c in cols if s&c and s&~c)
        @cache
        def g(s):
            if s.bit_count()<2:return Q(0)
            qs=[c for c in cols if s&c and s&~c]
            imbalance=min(abs(s.bit_count()-2*(s&c).bit_count()) for c in qs)
            qs=[c for c in qs if abs(s.bit_count()-2*(s&c).bit_count())==imbalance]
            return s.bit_count()+sum((g(s&c)+g(s&~c) for c in qs),Q(0))/len(qs)
        @cache
        def post(s):
            if not s:return 0
            return min(f(s&c)+post(s&~c) for c in cols if s&c)
        @cache
        def cover(s):
            if not s:return {():Q(1)},Q(0)
            gain=max((s&c).bit_count() for c in cols)
            qs=[c for c in cols if (s&c).bit_count()==gain]
            dist={};k=Q(0)
            for c in qs:
                d,z=cover(s&~c)
                for p,v in d.items():dist[(gain,)+p]=dist.get((gain,)+p,Q(0))+v/len(qs)
                k+=(g(s&c)+z)/len(qs)
            return dist,k
        full=(1<<n)-1
        dist,k=cover(full)
        remain=full;u=0
        for q in (0,2,6):
            y=remain&cols[q];u+=f(y);remain^=y
        assert not remain
        pair[label]={'F':f(full),'G':str(g(full)),'U_min_post':post(full),
            'post_for_026':u,'K_g':str(k/n),
            'profiles':[{'gains':p,'probability':str(v)} for p,v in sorted(dist.items())]}
    out[str(b)]=pair
tail=[]
for d in (7,10):
    values=[]
    for s in range(1,2*d):
        h=s.bit_length()-1
        lo=s*h+2*(s-2**h)
        hi=(s*s+s-2)//2
        values.append(hi+min(s,d)-lo)
    tail.append({'d':d,'max_leafsum_difference':max(values),'at_s':values.index(max(values))+1})
out['tails']=tail
out['arithmetic']={
    'b3_T76_lower':str(Q(76-69,34)-Q(235,17*76)),
    'b3_T100_lower':str(Q(100-69,34)-Q(235,17*100)),
    'incidence_expansion_from_hH_1over20':str(2*Q(1,20)/(25*(7+2*Q(1,20))))}
Path('final_work/proof_final_check.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
