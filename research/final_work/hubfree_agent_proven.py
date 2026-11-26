"""Proof certificates for a bounded-degree, no-hub connector family."""
from pathlib import Path
from fractions import Fraction
from itertools import combinations
import json
import sys
import networkx as nx

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from extremal_certify import coverage_certificate
from extremal_experiment import evaluate
from tq.core import ExactSolver,columns_of
from tq.io import write_json,digest,now,Profile
from followup_work.root_connected_certificate import sparse_statistics
from final_work.hubfree_agent_cycle import structure


def construct(rows,m,arcs,t):
    originals=[tuple(q+m*v for q in row) for v in range(t) for row in rows]
    connectors=[(m*v,m*v+5,m*w+6) for v,w in arcs]
    return originals+connectors,m*t


def tail_bound(d):
    result=[]
    for s in range(1,2*d):
        h=s.bit_length()-1
        lmin=s*h+2*(s-2**h)
        lmax=(s*s+s-2)//2
        result.append(dict(s=s,bound=lmax+min(s,d)-lmin))
    return max(x['bound'] for x in result),result


def run():
    out=Path('final_work/hubfree_agent_proven_results')
    out.mkdir(parents=True,exist_ok=False)
    basepath=Path('runs/extremal_analysis_v1/fixed_degree3_base.json')
    base=json.loads(basepath.read_text())
    write_json(out/'protocol.json',dict(started=now(),source_sha256=digest(__file__),base_sha256=digest(basepath),
        purpose='Finite certificates for proved boundeddegreeconnector family, notrandomprevalence',
        exact_cases='DirectedcycleT2 only; otherfamilies structural/proofbounds',
        exact_limits=dict(seconds=5,max_states=250000,max_rss_mb=768)))
    decorated={}
    for b in [1,2,3]:
        n=14+b
        pair={}
        for label in ['a','b']:
            rows=[tuple(row) for row in base[label]['rows']]+[(0,5,8+j) for j in range(b)]
            c=coverage_certificate(rows,8+b)
            solver=ExactSolver(rows,8+b,seconds=10)
            cols=columns_of(rows,8+b)
            remain=(1<<n)-1
            upper_post=0;parts=[]
            for q in [0,2,6]:
                y=remain&cols[q]
                f=solver.cost(y)
                upper_post+=f;parts.append(dict(question=q,yes_size=y.bit_count(),F_yes=f))
                remain^=y
            assert not remain
            expectedD=Fraction(65,2)+b if label=='a' else Fraction(67,2)+b
            assert Fraction(c['D_exact'])==expectedD
            expectedprofiles=([7+b,5,2],[7+b,4,3]) if label=='a' else ([7+b,5,2],[7+b,4,2,1])
            assert {tuple(x['gains']) for x in c['profiles']}==set(map(tuple,expectedprofiles))
            assert all(x['probability_exact']=='1/2' for x in c['profiles'])
            pair[label]=dict(certificate=c,upper_optimal_post_total=upper_post,upper_policy_parts=parts)
        e,tail=tail_bound(7+b)
        kdiff=Fraction(pair['b']['certificate']['expected_local_postyes_greedy_exact'])-Fraction(pair['a']['certificate']['expected_local_postyes_greedy_exact'])
        lower_const=kdiff-Fraction(pair['b']['upper_optimal_post_total']-19,n)
        upper_const=kdiff+Fraction(pair['a']['upper_optimal_post_total']-19,n)
        lower=lambda t:Fraction(t,2*n)+lower_const-Fraction(2*e+1,n*t)
        first=next(t for t in range(1,10000) if lower(t)>0)
        decorated[str(b)]=dict(n_per_block=n,worlds=pair,max_question_degree=7+b,
            tail_leafsum_bound=e,tail_table=tail,greedy_post_difference_exact=str(kdiff),
            contrast_lower='T/(2n)+lower_constant-(2E+1)/(nT)',
            lower_constant_exact=str(lower_const),upper_constant_exact=str(upper_const),
            first_positive_integer_T=first,
            sample_bounds=[dict(T=t,N=n*t,lower_exact=str(lower(t)),
                upper_exact=str(Fraction(t,2*n)+upper_const+Fraction(2*e+1,n*t))) for t in sorted({2,4,8,first,100,128})])
    write_json(out/'decorated_certificates.json',decorated)
    graphs=[]
    # b=1 orientedcycle is covered by the balanced-directed extension of the theorem.
    cases=[]
    for t in [2,3,4,8,32,128]:
        cases.append(('directed_cycle',1,t,[(v,(v+1)%t) for v in range(t)]))
    for t in [3,4,8,32]:
        h=nx.cycle_graph(t)
        cases.append(('bidirected_cycle',2,t,[(v,w) for v,w in h.edges() for v,w in [(v,w),(w,v)]]))
    for t in [4,8,16,32,128]:
        h=nx.complete_graph(4) if t==4 else nx.cubical_graph() if t==8 else nx.random_regular_graph(3,t,seed=391+t)
        cases.append(('bidirected_cubic',3,t,[(v,w) for v,w in h.edges() for v,w in [(v,w),(w,v)]]))
    finite=[]
    with Profile() as profile:
        for name,b,t,arcs in cases:
            assert len(set(arcs))==b*t and all(v!=w for v,w in arcs)
            pair={label:construct(base[label]['rows'],8,arcs,t) for label in ['a','b']}
            sa,sb=[sparse_statistics(pair[label][0],pair[label][1]) for label in ['a','b']]
            assert sa==sb
            for label,(rows,m) in pair.items():
                st=structure(rows,m)
                assert st['biconnected'] and not st['question_articulations'] and not st['object_articulations']
                assert st['maximum_question_degree']==7+b and st['row_degree_set']==[3]
                assert len(set(map(tuple,rows)))==len(rows)
                counts=[c.bit_count() for c in columns_of(rows,m)]
                roots=[q for q,c in enumerate(counts) if abs(len(rows)-2*c)==min(abs(len(rows)-2*x) for x in counts)]
                assert set(roots)=={8*v+q for v in range(t) for q in [0,5]}
                graphs.append(dict(name=name,b=b,T=t,world=label,N=len(rows),m=m,arcs=arcs,
                    structure=st,greedy_roots=roots,same_gram=True,cost_labels='notcomputed'))
                if name=='directed_cycle' and t==2:
                    finite.append(dict(name=name,b=b,T=t,world=label,result=evaluate(rows,m,dict(seconds=5,max_states=250000,max_rss_mb=768))))
    write_json(out/'graph_checks.json',graphs)
    write_json(out/'small_exact.json',finite)
    summary=dict(completed=now(),profile=profile.result,structural_graphs=len(graphs),
        biconnected_same_gram_degree3=True,maximum_question_degrees=[8,9,10],
        cycle_contrast='N/450+O(1)',bidirected_cubic_contrast='N/578+O(1)',
        all_tie_robust=False,expansion='Conditionalonchoosingexpanderblockgraphs; notinferredfromrandomsamples',
        decorated_positive_T={b:x['first_positive_integer_T'] for b,x in decorated.items()},
        small_exact_statuses=[dict(world=x['world'],status=x['result']['exact']['status'],
            regret=x['result'].get('greedy',{}).get('gap_exact')) for x in finite])
    write_json(out/'summary.json',summary)
    write_json(out/'manifest.json',{p.name:digest(p) for p in out.glob('*') if p.is_file() and p.name!='manifest.json'})
    print(json.dumps(summary),flush=True)


if __name__=='__main__':run()
