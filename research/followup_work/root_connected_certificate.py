#!/usr/bin/env python3
"""Root's independent connector construction and exact/structural certificates."""
from __future__ import annotations
from collections import Counter
from fractions import Fraction
from itertools import combinations
from pathlib import Path
import argparse
import json
import random
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tq.core import ExactSolver, columns_of
from tq.io import Profile, write_json, digest, now
from extremal_experiment import evaluate
from extremal_certify import direct_sum


def paired_connector(rows,m,s,port=0):
    """2s original blocks, s degree3 bridges, one shared hub column."""
    original,old_m=direct_sum(rows,m,2*s)
    hub=old_m
    bridges=[(hub,(2*j)*m+port,(2*j+1)*m+port) for j in range(s)]
    return original+bridges,old_m+1,hub


def sparse_statistics(rows,m):
    degrees=[0]*m
    pairs=Counter()
    for row in rows:
        for q in row:
            degrees[q]+=1
        pairs.update(combinations(sorted(row),2))
    return dict(column_degrees=degrees,pairs=[[a,b,v] for (a,b),v in sorted(pairs.items())])


def component_count(rows,m):
    parent=list(range(m))
    def find(q):
        while parent[q]!=q:
            parent[q]=parent[parent[q]]
            q=parent[q]
        return q
    for row in rows:
        a=find(row[0])
        for b in row[1:]:
            parent[find(b)]=a
    used={q for row in rows for q in row}
    return len({find(q) for q in used})+(m-len(used))


def seeded_greedy_tree(rows,m,seed):
    """An EXACT realized policy cost, not the expectation over all tie outcomes."""
    cols=columns_of(rows,m)
    rng=random.Random(seed)
    def tree(mask):
        size=mask.bit_count()
        if size==1:
            return 0,dict(object=mask.bit_length()-1)
        options=[(abs(size-2*a.bit_count()),q,a,mask^a) for q,c in enumerate(cols)
                 if (a:=mask&c) and a!=mask]
        imbalance=min(x[0] for x in options)
        choices=[x for x in options if x[0]==imbalance]
        _,q,a,b=rng.choice(choices)
        ca,ta=tree(a)
        cb,tb=tree(b)
        return size+ca+cb,dict(question=q,yes=ta,no=tb)
    total,policy=tree((1<<len(rows))-1)
    depths=[]
    for i,row in enumerate(rows):
        node,depth=policy,0
        while 'question' in node:
            node=node['yes'] if node['question'] in row else node['no']
            depth+=1
        assert node['object']==i
        depths.append(depth)
    assert sum(depths)==total
    return dict(seed=seed,total_leaf_depth=total,mean_exact=str(Fraction(total,len(rows))),
                root=policy['question'],depths=depths,tree=policy,
                interpretation='One seeded greedy tie tree, alltargets replayed; not uniformtie expectation or optimal label')


def run(out_path):
    out=Path(out_path)
    out.mkdir(parents=True,exist_ok=False)
    source=Path('runs/extremal_analysis_v1/fixed_degree3_base.json')
    base=json.loads(source.read_text(encoding='utf-8'))
    write_json(out/'protocol.json',dict(started=now(),source_sha256=digest(source),
        code_sha256=digest(__file__),constructor='two oldblocks per degree3 connector; one shared hub',
        ports=[0],small_exact_s=[1],structural_s=[1,2,9,16,54,100,256],
        seeded_policy_s=[9,16],seeded_policy_seeds=[17,83],
        exact_limits=dict(seconds=10,max_states=500000,max_rss_mb=1024),
        scientific_scope='Connected family with proof bounds; no inferred largeexact optimal labels'))
    stats=[]
    exact=[]
    trees=[]
    with Profile() as full_profile:
        for s in [1,2,9,16,54,100,256]:
            constructions={label:paired_connector(base[label]['rows'],8,s) for label in ('a','b')}
            signatures={label:sparse_statistics(rows,m) for label,(rows,m,hub) in constructions.items()}
            assert signatures['a']==signatures['b']
            for label,(rows,m,hub) in constructions.items():
                assert len(rows)==29*s and m==16*s+1
                assert all(len(row)==3 and len(set(row))==3 for row in rows)
                assert len(set(map(tuple,rows)))==len(rows)
                assert component_count(rows,m)==1
                degrees=signatures[label]['column_degrees']
                assert degrees[hub]==s and max(degrees[:hub])<=8
                root_ties=[q for q,d in enumerate(degrees)
                           if abs(len(rows)-2*d)==min(abs(len(rows)-2*x) for x in degrees)]
                if s>=9:
                    assert root_ties==[hub]
                record=dict(s=s,world=label,n=len(rows),m=m,row_degree=3,components=1,
                    unique_profiles=True,same_gram=True,gram_sparse_sha256=__import__('hashlib').sha256(
                        json.dumps(signatures[label],sort_keys=True).encode()).hexdigest(),
                    hub=hub,hub_degree=degrees[hub],max_private_degree=max(degrees[:hub]),
                    greedy_root_questions=root_ties,
                    lower_contrast_exact=str(Fraction(2*s-100,29)-Fraction(393,29*s)),
                    upper_contrast_exact=str(Fraction(2*s+94,29)+Fraction(393,29*s)),
                    bound_applicable=s>=9,measurement='Graph invariants/root verified; costbounds are proved, not DP labels')
                stats.append(record)
                if s==1:
                    result=evaluate(rows,m,dict(seconds=10,max_states=500000,max_rss_mb=1024))
                    assert result['exact']['status']=='complete'
                    # Restriction/sandwich holds even when the greedyroot is not the hub.
                    original,old_m=direct_sum(base[label]['rows'],8,2*s)
                    original_result=evaluate(original,old_m,dict(seconds=10,max_states=500000,max_rss_mb=1024))
                    assert original_result['exact']['status']=='complete'
                    cconn=Fraction(s+1,2)-Fraction(1,s)
                    weighted_opt=Fraction(28,29)*Fraction(original_result['exact']['optimal_total'],28*s)+cconn/29
                    connected_opt=Fraction(result['exact']['optimal_total'],29*s)
                    assert weighted_opt<=connected_opt<=weighted_opt+1
                    exact.append(dict(s=s,world=label,connected=result,original=original_result,
                        cconn_exact=str(cconn),class_optimum_lower_exact=str(weighted_opt),
                        class_optimum_upper_exact=str(weighted_opt+1),sandwich_checked=True))
                if s in [9,16]:
                    for seed in [17,83]:
                        policy=seeded_greedy_tree(rows,m,seed)
                        assert policy['root']==hub
                        old_count=28*s
                        old_depths=policy['depths'][:old_count]
                        connector_depths=policy['depths'][old_count:]
                        # Every connector branch is a singleton-test chain; allties samecost.
                        cconn=Fraction(s+1,2)-Fraction(1,s)
                        assert sum(d-1 for d in connector_depths)==s*cconn
                        assert policy['total_leaf_depth']==len(rows)+sum(d-1 for d in old_depths)+s*cconn
                        trees.append(dict(s=s,world=label,policy=policy))
    write_json(out/'graph_checks.json',stats)
    write_json(out/'small_exact_checks.json',exact)
    write_json(out/'seeded_policy_replays.json',trees)
    write_json(out/'summary.json',dict(completed=now(),profile=full_profile.result,
        connected_same_gram_degree3=True,structural_graphs_checked=len(stats),
        exact_graphs_checked=len(exact),seeded_trees_replayed=len(trees),
        regret_contrast='2N/841+O(1)',cost_ratios=['131/129','45/43'],
        finite_bound_positive_for_s_ge=54,
        exact_large_n_optimal_labels='Not computed or fabricated'))
    write_json(out/'manifest.json',{p.name:digest(p) for p in out.glob('*.json') if p.name!='manifest.json'})
    print(json.dumps(dict(passed=True,structural_graphs=len(stats),exact_graphs=len(exact),trees=len(trees))))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',default='runs/followup_connected_v1')
    run(parser.parse_args().out)
