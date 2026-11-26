#!/usr/bin/env python3
"""Exact rational certificates for bounded-degree hub-free controlled instances."""
from fractions import Fraction
from pathlib import Path
import json
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import networkx as nx
from tq.io import Profile,write_json,digest,now
from final_work.hubfree_search import graph_checks
from followup_work.root_connected_certificate import sparse_statistics


def bidirected_bridges(rows,m,h):
    t=len(h)
    result=[tuple(q+v*m for q in row) for v in range(t) for row in rows]
    result += [(v*m,v*m+5,w*m+6) for v in range(t) for w in sorted(h[v])]
    return result,t*m


def rational_gap_certificate(h,delta=Fraction(1,10)):
    """B^T(L-delta I)B is positive definite, B_i=e_i-e_last.

    Exact Schur/LDL pivots certify the lower Laplacian gap; no float eigensolver.
    """
    t=len(h)
    degree=dict(h.degree())
    def lap(i,j):return degree[i] if i==j else -int(h.has_edge(i,j))
    scale=delta.denominator
    a=[[Fraction(scale*(lap(i,j)-lap(i,t-1)-lap(t-1,j)+lap(t-1,t-1))
                 -delta.numerator*(int(i==j)+1)) for j in range(t-1)] for i in range(t-1)]
    pivots=[]
    for k in range(t-1):
        pivot=a[k][k]
        pivots.append(pivot)
        if pivot<=0:
            return dict(certified=False,delta_exact=str(delta),failed_pivot=k,pivots_exact=list(map(str,pivots)))
        for i in range(k+1,t-1):
            if not a[i][k]:continue
            for j in range(i,t-1):
                value=a[i][j]-a[i][k]*a[j][k]/pivot
                a[i][j]=value
                a[j][i]=value
    return dict(certified=True,delta_exact=str(delta),pivots_exact=list(map(str,pivots)),
        method='Exact Fraction Schur pivots for B^T(L-delta I)B; positive on the entire zero-sum subspace',
        skeleton_edge_expansion_lower_exact=str(delta/2),
        full_incidence_edge_expansion_lower_exact=str(delta/(25*(7+delta))))


def run():
    out=Path('runs/hubfree_expander_cert_v1')
    out.mkdir(parents=True,exist_ok=False)
    base_path=Path('runs/extremal_analysis_v1/fixed_degree3_base.json')
    base=json.loads(base_path.read_text(encoding='utf-8'))
    cases=[('K4',nx.complete_graph(4)),('K33',nx.complete_bipartite_graph(3,3)),
        ('cube',nx.cubical_graph()),('Petersen',nx.petersen_graph()),('Heawood',nx.heawood_graph())]
    cases += [(f'cubic-{t}-seed{seed}',nx.random_regular_graph(3,t,seed=seed)) for t,seed in [(32,17),(64,29),(76,41),(100,73)]]
    write_json(out/'protocol.json',dict(started=now(),code_sha256=digest(__file__),base_sha256=digest(base_path),
        skeletons=[dict(name=name,T=len(h)) for name,h in cases],
        prescribed_gap_thresholds=['1/10','1/20','1/100'],
        claims='Finite exact rational spectral lower certificates; infinite expander existence is a separate known theorem',
        large_exact_optimal_labels='Not attempted or filled from asymptotic formulas'))
    records=[]
    with Profile() as profile:
        for name,h in cases:
            h=nx.convert_node_labels_to_integers(h,ordering='sorted')
            assert nx.is_connected(h) and all(d==3 for _,d in h.degree()) and nx.number_of_selfloops(h)==0
            with Profile() as case_profile:
                spectral=None
                for delta in [Fraction(1,10),Fraction(1,20),Fraction(1,100)]:
                    spectral=rational_gap_certificate(h,delta)
                    if spectral['certified']:break
                t=len(h)
                worlds={label:bidirected_bridges(base[label]['rows'],8,h) for label in ['a','b']}
                statistics={label:sparse_statistics(rows,m) for label,(rows,m) in worlds.items()}
                assert statistics['a']==statistics['b']
                results={}
                for label,(rows,m) in worlds.items():
                    checks=graph_checks(rows,m)
                    assert checks['biconnected'] and checks['row_degree3'] and checks['unique_rows']
                    assert checks['max_question_degree']==10 and checks['root_tie_count']==2*t
                    assert len(rows)==17*t and m==8*t
                    results[label]=dict(n=len(rows),m=m,checks=checks,
                        cost_labels='No large exact DP label; use explicitly proved bounds',rows=rows)
                record=dict(name=name,T=t,b=3,skeleton_edges=sorted([sorted(e) for e in h.edges()]),
                    spectral_certificate=spectral,worlds=results,same_gram=True,
                    regret_contrast_lower_exact=str(Fraction(t-69,34)-Fraction(235,17*t)),
                    regret_contrast_upper_exact=str(Fraction(t+63,34)+Fraction(235,17*t)),
                    finite_bound_scope='Uniform greedy tie expectation; proof bound, not a measured exact cost')
            record['profile']=case_profile.result
            write_json(out/f'{name}.json',record)
            records.append(dict(name=name,T=t,n=17*t,spectral_certified=spectral['certified'],
                incidence_expansion_lower=spectral.get('full_incidence_edge_expansion_lower_exact'),
                regret_lower=record['regret_contrast_lower_exact'],regret_upper=record['regret_contrast_upper_exact']))
            print(json.dumps(records[-1]),flush=True)
    write_json(out/'summary.json',dict(completed=now(),profile=profile.result,cases=records,
        max_question_degree=10,row_degree=3,no_articulation_vertex=True,
        large_dp_not_used=True,infinite_expansion_not_inferred_from_samples=True))
    write_json(out/'manifest.json',{p.name:digest(p) for p in out.glob('*.json') if p.name!='manifest.json'})


if __name__=='__main__':run()
