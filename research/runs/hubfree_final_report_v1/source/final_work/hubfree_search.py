#!/usr/bin/env python3
"""Hub-free controlled cyclic bridge search; no existing artifacts are overwritten."""
from __future__ import annotations
from collections import defaultdict
from fractions import Fraction
from itertools import combinations
from pathlib import Path
import argparse
import gc
import json
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import networkx as nx
from tq.core import columns_of
from tq.io import Profile,append_jsonl,write_json,digest,now
from extremal_experiment import evaluate
from followup_work.root_connected_certificate import sparse_statistics


def base_pairs():
    a=json.loads(Path('runs/extremal_analysis_v1/fixed_degree3_base.json').read_text(encoding='utf-8'))
    b=json.loads(Path('runs/extremal_pair_design_v1/best.json').read_text(encoding='utf-8'))
    return {'base14':{label:a[label]['rows'] for label in ['a','b']},
            'base18':{label:b[label]['rows'] for label in ['a','b']}}


def cyclic_bridge(pair,m,ports,orientation):
    """c_j uses two local ports and one port from the next block."""
    left,right,next_port=ports
    t=len(orientation)
    rows=[tuple(q+j*m for q in row) for j,label in enumerate(orientation) for row in pair[label]]
    rows += [tuple(sorted((j*m+left,j*m+right,((j+1)%t)*m+next_port))) for j in range(t)]
    return rows,m*t


def graph_checks(rows,m):
    n=len(rows)
    graph=nx.Graph()
    graph.add_nodes_from(range(n+m))
    graph.add_edges_from((i,n+q) for i,row in enumerate(rows) for q in row)
    cuts=list(nx.articulation_points(graph))
    cols=columns_of(rows,m)
    counts=[c.bit_count() for c in cols]
    imbalance=[abs(n-2*k) for k in counts]
    roots=[q for q,v in enumerate(imbalance) if 0<counts[q]<n and v==min(imbalance)]
    return dict(connected=nx.is_connected(graph),biconnected=nx.is_biconnected(graph),
        articulation_questions=[x-n for x in cuts if x>=n],articulation_objects=[x for x in cuts if x<n],
        max_question_degree=max(counts),min_question_degree=min(counts),
        max_support_fraction=max(counts)/n,root_questions=roots,root_tie_count=len(roots),
        all_columns_nonconstant=all(0<k<n for k in counts),
        unique_rows=len(set(map(tuple,rows)))==n,row_degree3=all(len(set(r))==len(r)==3 for r in rows))


def pattern_list(m):
    # Two local ports unordered; the distinct next-block port is marked.
    return [(a,b,c) for a,b in combinations(range(m),2) for c in range(m) if c not in (a,b)]


def run(out_path,mode):
    out=Path(out_path)
    out.mkdir(parents=True,exist_ok=False)
    pairs=base_pairs()
    limits=dict(seconds=3,max_states=250000,max_rss_mb=1024)
    config=dict(mode=mode,started=now(),code_sha256=digest(__file__),
        hard_conditions=['connected','no articulation vertex of either bipartite class','degree3 rows',
                         'uniform-in-size bounded question degree','same indexed Gram per controlled pair',
                         'at least2 tied greedy first questions'],
        constructor='Tperiodicblocks + c_j={two localports, one nextblockport}',
        copies=2,orientations=['aa','ab','bb'],solver=limits,
        global_seconds=180 if mode=='search' else 30,
        purpose='Extremal discovery, not prevalence or global optimality',
        secondary_objective='all-tie robust regret contrast')
    write_json(out/'protocol.json',config)
    start=time.perf_counter()
    summaries=[]
    best=None
    total_worlds,complete=0,0
    with Profile() as profile:
        for name,m in [('base14',8),('base18',9)]:
            patterns=pattern_list(m) if mode=='search' else [(0,5,6),(0,2,3)]
            # A mathematically motivated pattern is evaluated first; ordering never filters effects.
            patterns=sorted(set(patterns),key=lambda p:(p!=(0,5,6),p))
            for index,ports in enumerate(patterns):
                if time.perf_counter()-start>config['global_seconds']:
                    break
                group=[]
                stats=None
                for orientation in ['aa','ab','bb']:
                    rows,new_m=cyclic_bridge(pairs[name],m,ports,orientation)
                    current_stats=sparse_statistics(rows,new_m)
                    if stats is None:stats=current_stats
                    assert stats==current_stats
                    checks=graph_checks(rows,new_m)
                    valid=all(checks[k] for k in ['connected','biconnected','all_columns_nonconstant','unique_rows','row_degree3'])
                    valid=valid and checks['max_question_degree'] <= (8 if name=='base14' else 10) and checks['root_tie_count']>=2
                    if not valid:
                        append_jsonl(out/'rejections.jsonl',dict(base=name,ports=ports,orientation=orientation,checks=checks))
                        continue
                    result=evaluate(rows,new_m,limits)
                    record=dict(base=name,pattern_index=index,ports=ports,orientation=orientation,
                                checks=checks,graph=result,same_gram_within_pattern=True)
                    append_jsonl(out/'worlds.jsonl',record)
                    total_worlds+=1
                    if result['exact']['status']=='complete':
                        group.append(record)
                        complete+=1
                if group:
                    low=min(group,key=lambda r:Fraction(r['graph']['greedy']['gap_exact']))
                    high=max(group,key=lambda r:Fraction(r['graph']['greedy']['gap_exact']))
                    contrast=Fraction(high['graph']['greedy']['gap_exact'])-Fraction(low['graph']['greedy']['gap_exact'])
                    robust=Fraction(high['graph']['greedy']['min_tie_gap_exact'])-Fraction(low['graph']['greedy']['max_tie_gap_exact'])
                    summary=dict(base=name,ports=ports,completed_orientations=len(group),
                        contrast_exact=str(contrast),contrast=float(contrast),robust_exact=str(robust),
                        high_orientation=high['orientation'],low_orientation=low['orientation'])
                    summaries.append(summary)
                    append_jsonl(out/'patterns.jsonl',summary)
                    rank=(contrast,robust)
                    if best is None or rank>best[0]:
                        best=(rank,dict(summary=summary,bad=high,good=low))
                        write_json(out/'best.json',best[1])
                        print(json.dumps(dict(new_best=str(contrast),robust=str(robust),base=name,ports=ports)),flush=True)
                gc.collect()
    write_json(out/'summary.json',dict(completed=now(),worlds=total_worlds,complete_worlds=complete,
        patterns=len(summaries),best_contrast_exact=str(best[0][0]) if best else None,
        profile=profile.result,stop_reason='time_budget' if time.perf_counter()-start>config['global_seconds'] else 'scheduled_patterns_completed',
        no_articulation_vertex=True,max_question_degree_uniform_bound=10,not_an_expander_certificate=True))
    write_json(out/'manifest.json',{p.name:digest(p) for p in out.glob('*.json*') if p.name!='manifest.json'})


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--out',default='runs/hubfree_search_v1')
    p.add_argument('--mode',choices=['pilot','search'],default='search')
    args=p.parse_args()
    run(args.out,args.mode)
