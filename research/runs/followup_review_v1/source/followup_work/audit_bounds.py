"""Finite certificates for strengthened proof constants. No old artifact changes."""
from fractions import Fraction
from functools import lru_cache
from pathlib import Path
import json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from followup_work.proof_signature import full_costs
from tq.io import write_json,digest,now


def minimum_post(rows,m):
    cols,F=full_costs(rows,m)
    certificates={}
    @lru_cache(None)
    def cost(mask):
        if not mask:return 0
        options=[]
        for q,col in enumerate(cols):
            yes=mask&col
            if yes:
                options.append((F[yes]+cost(mask^yes),q,yes,mask^yes))
        value,q,yes,no=min(options)
        certificates[str(mask)]=dict(value=value,question=q,yes_mask=yes,no_mask=no,yes_cost=F[yes])
        return value
    full=(1<<len(rows))-1
    value=cost(full)
    path=[];mask=full
    while mask:
        c=certificates[str(mask)]
        path.append(dict(question=c['question'],new_coverage=c['yes_mask'].bit_count(),post_cost=c['yes_cost']))
        mask=c['no_mask']
    return dict(minimum=value,path=path,reachable_states=cost.cache_info().currsize,states=certificates)


def main():
    base=json.loads(Path('runs/extremal_analysis_v1/fixed_degree3_base.json').read_text())
    post={label:minimum_post(base[label]['rows'],8) for label in ['a','b']}
    assert all(x['minimum']==19 for x in post.values())
    tails=[]
    for s in range(1,14):
        h=s.bit_length()-1
        lmin=s*h+2*(s-(1<<h))
        lmax=(s*s+s-2)//2
        tails.append(dict(s=s,Lmin=lmin,Lmax=lmax,max_constant_descendants=min(s,7),
                          difference_bound=lmax+min(s,7)-lmin))
    assert max(x['difference_bound'] for x in tails)==48
    values=[]
    for t in [1,2,38,39,50,81,100]:
        lo=Fraction(t-33,28)-Fraction(97,14*t)
        hi=Fraction(t+27,28)+Fraction(97,14*t)
        values.append(dict(T=t,lower_exact=str(lo),upper_exact=str(hi),lower=float(lo),upper=float(hi)))
    connected=[]
    for s in [9,32,33,54,100]:
        lo=Fraction(2*s-62,29)-Fraction(97,29*s)
        hi=Fraction(2*s+56,29)+Fraction(97,29*s)
        connected.append(dict(S=s,N=29*s,lower_exact=str(lo),upper_exact=str(hi),lower=float(lo),upper=float(hi)))
    result=dict(created=now(),source_sha256={p:digest(p) for p in ['followup_work/audit_bounds.py','followup_work/proof_signature.py']},
        minimum_post=post,tail_leaf_bounds=tails,maximum_tail_leaf_difference=48,
        disconnected_stronger_bound=dict(lower='(T-33)/28-97/(14T)',upper='(T+27)/28+97/(14T)',
            first_uniformly_positive_integer_T=39,values=values),
        paired_hub_bridge_stronger_bound=dict(lower='(2S-62)/29-97/(29S)',upper='(2S+56)/29+97/(29S)',
            first_uniformly_positive_integer_S=33,values=connected),
        interpretation='Finite proof certificates, not measured large-graph exact costs')
    write_json('followup_work/proof_audit_certificates.json',result)
    print(json.dumps(dict(post_minima={k:v['minimum'] for k,v in post.items()},tail=48,
        disconnected_first_T=39,connected_first_S=33)))


if __name__=='__main__':main()
