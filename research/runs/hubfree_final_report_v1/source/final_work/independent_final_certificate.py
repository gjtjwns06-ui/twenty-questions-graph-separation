#!/usr/bin/env python3
"""Independent row-profile costs, vertex deletions, ablations, and exact gap checks."""
from __future__ import annotations
from fractions import Fraction
from functools import lru_cache
from pathlib import Path
import json
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import networkx as nx
from tq.io import Profile,write_json,digest,now
from extremal_experiment import evaluate
from final_work.hubfree_search import graph_checks
from followup_work.root_connected_certificate import sparse_statistics


def profile_costs(rows,m):
    profiles=tuple(sorted(sum(1<<q for q in row) for row in rows))
    assert len(set(profiles))==len(profiles)
    @lru_cache(None)
    def optimum(state):
        if len(state)<=1:return 0
        options=[]
        for q in range(m):
            yes=tuple(p for p in state if p>>q&1)
            no=tuple(p for p in state if not(p>>q&1))
            if yes and no:options.append(optimum(yes)+optimum(no))
        return len(state)+min(options)
    @lru_cache(None)
    def greedy(state):
        if len(state)<=1:return Fraction(0),0,0
        choices=[]
        for q in range(m):
            yes=tuple(p for p in state if p>>q&1)
            no=tuple(p for p in state if not(p>>q&1))
            if yes and no:choices.append((abs(len(yes)-len(no)),yes,no))
        best=min(x[0] for x in choices)
        outcomes=[]
        for imbalance,yes,no in choices:
            if imbalance==best:
                a,b=greedy(yes),greedy(no)
                outcomes.append((a[0]+b[0],a[1]+b[1],a[2]+b[2]))
        return (len(state)+sum((x[0] for x in outcomes),Fraction(0))/len(outcomes),
                len(state)+min(x[1] for x in outcomes),len(state)+max(x[2] for x in outcomes))
    f=optimum(profiles)
    first=[]
    for q in range(m):
        yes=tuple(p for p in profiles if p>>q&1)
        no=tuple(p for p in profiles if not(p>>q&1))
        first.append(len(profiles)+optimum(yes)+optimum(no) if yes and no else None)
    g=greedy(profiles)
    return dict(optimal_total=f,first_totals=first,greedy_uniform_total_exact=str(g[0]),
        greedy_min_total=g[1],greedy_max_total=g[2],states=optimum.cache_info().currsize,
        representation='Immutable tuple of answer profiles; independent of object-subset bitmask implementation')


def all_vertex_deletions(rows,m):
    n=len(rows)
    adjacency=[set() for _ in range(n+m)]
    for i,row in enumerate(rows):
        for q in row:
            adjacency[i].add(n+q);adjacency[n+q].add(i)
    bad=[]
    for removed in range(n+m):
        start=next(i for i in range(n+m) if i!=removed)
        seen={start};stack=[start]
        while stack:
            v=stack.pop()
            new=adjacency[v]-seen-{removed}
            seen.update(new);stack.extend(new)
        if len(seen)!=n+m-1:bad.append(removed)
    return dict(vertices_checked=n+m,disconnecting_vertices=bad,passed=not bad)


def bareiss_gap(edges,t):
    """Independently assemble10B^TLB-B^TB as edge outer products; fraction-free pivots."""
    n=t-1
    a=[[-1-int(i==j) for j in range(n)] for i in range(n)]
    for u,v in edges:
        x=[int(u==i)-int(v==i)-int(u==t-1)+int(v==t-1) for i in range(n)]
        support=[i for i,z in enumerate(x) if z]
        for i in support:
            for j in support:a[i][j]+=10*x[i]*x[j]
    previous=1
    determinants=[]
    for k in range(n):
        pivot=a[k][k]
        assert pivot>0
        determinants.append(pivot)
        for i in range(k+1,n):
            for j in range(i,n):
                numerator=pivot*a[i][j]-a[i][k]*a[j][k]
                assert numerator%previous==0
                a[i][j]=numerator//previous
                a[j][i]=a[i][j]
        previous=pivot
    return determinants


def run():
    out=Path('runs/final_independent_certificate_v1')
    out.mkdir(parents=True,exist_ok=False)
    write_json(out/'protocol.json',dict(started=now(),source_sha256=digest(__file__),
        tasks=['Independent tuple-profile exact DP','All single vertex removals',
               'All single question ablations and deletion of both original greedyroots',
               'Independent integer Bareiss certificate for all9 skeleton spectral gaps'],
        ablation_limits=dict(seconds=3,max_states=250000,max_rss_mb=1024),
        scope='Ablations may relax uniform rowdegree3 to aligned equal degreevectors; record separately'))
    best=json.loads(Path('runs/hubfree_search_v1/best.json').read_text(encoding='utf-8'))
    independent={}
    ablations=[]
    with Profile() as profile:
        for label in ['bad','good']:
            w=best[label]['graph']
            with Profile() as audit_profile:
                result=profile_costs(w['rows'],w['m'])
            assert result['optimal_total']==w['exact']['optimal_total']
            assert result['first_totals']==w['exact']['first_totals']
            assert result['greedy_uniform_total_exact']==w['greedy']['total_uniform_exact']
            assert result['greedy_min_total']==w['greedy']['total_min_ties']
            assert result['greedy_max_total']==w['greedy']['total_max_ties']
            vertices=all_vertex_deletions(w['rows'],w['m'])
            assert vertices['passed']
            independent[label]=dict(costs=result,vertex_deletions=vertices,profile=audit_profile.result)
        root_set=best['bad']['checks']['root_questions']
        deletions=[[q] for q in range(18)]+[root_set]
        for removed in deletions:
            records={}
            keep=[q for q in range(18) if q not in removed]
            mapping={q:i for i,q in enumerate(keep)}
            for label in ['bad','good']:
                rows=[tuple(mapping[q] for q in row if q in mapping) for row in best[label]['graph']['rows']]
                # Uniform targets allow rowrelabeling; align degreevectors before assertingpaircontrols.
                rows=sorted(rows,key=lambda row:(len(row),row))
                assert len(set(rows))==len(rows)
                result=evaluate(rows,len(keep),dict(seconds=3,max_states=250000,max_rss_mb=1024))
                records[label]=dict(rows=rows,graph=result,
                    structural=graph_checks(rows,len(keep)),row_degrees=[len(row) for row in rows])
            assert records['bad']['row_degrees']==records['good']['row_degrees']
            assert sparse_statistics(records['bad']['rows'],len(keep))==sparse_statistics(records['good']['rows'],len(keep))
            complete=all(r['graph']['exact']['status']=='complete' for r in records.values())
            ablations.append(dict(removed_original_questions=removed,controls_same_gram=True,
                controls_same_aligned_rowdegreevector=True,row_degree3_relaxed=True,records=records,
                complete=complete,regret_bad_minus_good_exact=str(Fraction(records['bad']['graph']['greedy']['gap_exact'])-
                    Fraction(records['good']['graph']['greedy']['gap_exact'])) if complete else None))
        expander=[]
        folder=Path('runs/hubfree_expander_cert_v1')
        for p in sorted(folder.glob('*.json')):
            if p.name in ['protocol.json','summary.json','manifest.json']:continue
            r=json.loads(p.read_text(encoding='utf-8'))
            cert=r['spectral_certificate']
            assert cert['certified'] and cert['delta_exact']=='1/10'
            det=bareiss_gap(r['skeleton_edges'],r['T'])
            pivot=[Fraction(value,det[i-1] if i else 1) for i,value in enumerate(det)]
            assert list(map(str,pivot))==cert['pivots_exact']
            expander.append(dict(name=r['name'],T=r['T'],positive_principal_minors=list(map(str,det)),
                method='Integer Bareiss elimination; independent edgeouterproduct matrixassembly',
                laplacian_gap_lower_exact='1/10',full_edge_expansion_lower_exact='1/1775'))
    write_json(out/'finite38_independent_costs.json',independent)
    write_json(out/'question_ablations.json',ablations)
    write_json(out/'independent_expansion_certificates.json',expander)
    values=[Fraction(r['regret_bad_minus_good_exact']) for r in ablations[:-1] if r['complete']]
    write_json(out/'summary.json',dict(completed=now(),profile=profile.result,
        finite38_costs_and_all_vertex_deletions_passed=True,ablation_pairs=len(ablations),
        completed_ablation_pairs=sum(r['complete'] for r in ablations),
        positive_single_deletion_contrast_count=sum(x>0 for x in values),
        single_deletion_min_contrast_exact=str(min(values)),single_deletion_max_contrast_exact=str(max(values)),
        remove_both_original_root_questions_contrast_exact=ablations[-1]['regret_bad_minus_good_exact'],
        independent_exact_spectral_certificates=len(expander),
        ablation_scope='EqualGram/equalalignedrowdegrees preserved, constantrowdegree3 relaxed; separate sensitivityexperiment'))
    write_json(out/'manifest.json',{p.name:digest(p) for p in out.glob('*.json') if p.name!='manifest.json'})
    print((out/'summary.json').read_text(encoding='utf-8'))


if __name__=='__main__':run()
