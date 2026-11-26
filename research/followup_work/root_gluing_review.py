#!/usr/bin/env python3
"""Independent row-set review of the shared-question construction and CUT identity."""
from __future__ import annotations
from collections import defaultdict
from fractions import Fraction
from functools import lru_cache
from itertools import combinations
from pathlib import Path
import json
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tq.io import write_json,digest,now
from tq.core import gram_of
from followup_work.root_connected_certificate import sparse_statistics,component_count


def glue_root(rows,m,port,t):
    private=[q for q in range(m) if q!=port]
    ids={q:i for i,q in enumerate(private)}
    return [tuple(sorted(0 if q==port else 1+b*(m-1)+ids[q] for q in row))
            for b in range(t) for row in rows],1+t*(m-1)


def branch_review(rows,m,port,answer):
    private=[q for q in range(m) if q!=port]
    branch=[frozenset(q for q in row if q!=port) for row in rows if (port in row)==bool(answer)]
    f=[0]*m
    for k in range(m):
        for qs in combinations(private,k):
            covered=sum(bool(row.intersection(qs)) for row in branch)
            f[k]=max(f[k],covered)
    @lru_cache(None)
    def profiles(remaining):
        if not remaining:
            return {():Fraction(1)}
        coverage={q:frozenset(i for i in remaining if q in branch[i]) for q in private}
        maximum=max(map(len,coverage.values()))
        tied=[covered for covered in coverage.values() if len(covered)==maximum]
        output=defaultdict(Fraction)
        for covered in tied:
            for tail,prob in profiles(remaining-covered).items():
                output[(maximum,)+tail]+=prob/len(tied)
        return dict(output)
    distribution=profiles(frozenset(range(len(branch))))
    mu=[sum((sum(g>=s for g in profile)*p for profile,p in distribution.items()),Fraction(0))
        for s in range(1,max(f)+1)]
    d=sum((x*x for x in mu),Fraction(0))
    return dict(answer=answer,n=len(branch),coverage_envelope=f,
        profiles=[dict(gains=list(g),probability_exact=str(p)) for g,p in sorted(distribution.items())],
        D_exact=str(d))


def run():
    out=Path('runs/followup_root_gluing_v1')
    out.mkdir(parents=True,exist_ok=False)
    raw14=json.loads(Path('runs/extremal_analysis_v1/fixed_degree3_base.json').read_text(encoding='utf-8'))
    raw18=json.loads(Path('runs/extremal_pair_design_v1/best.json').read_text(encoding='utf-8'))
    write_json(out/'protocol.json',dict(started=now(),source_sha256=digest(__file__),
        purpose='Independent subset and row-set enumeration; not reusing the original profile routine',
        large_cases='Graph invariants only; no large exact optimal labels'))
    structural=[]
    for name,raw,m in [('base14',raw14,8),('base18',raw18,9)]:
        for t in [1,2,3,9,60,128]:
            graphs={label:glue_root(raw[label]['rows'],m,3,t) for label in ('a','b')}
            signatures={label:sparse_statistics(rows,new_m) for label,(rows,new_m) in graphs.items()}
            assert signatures['a']==signatures['b']
            for label,(rows,new_m) in graphs.items():
                assert component_count(rows,new_m)==1
                assert len(set(rows))==len(rows) and all(len(row)==3 for row in rows)
                degrees=signatures[label]['column_degrees']
                assert all(0<d<len(rows) for d in degrees)
                imbalance=[abs(len(rows)-2*d) for d in degrees]
                roots=[q for q,v in enumerate(imbalance) if v==min(imbalance)]
                if name=='base18' or t>=3:
                    assert roots==[0]
                structural.append(dict(base=name,copies=t,world=label,n=len(rows),m=new_m,
                    connected=True,row_degree=3,same_gram=True,all_columns_nonconstant=True,
                    greedy_roots=roots,cost_labels='Not computed in this structural review'))
    branch_cert={label:[branch_review(raw18[label]['rows'],9,3,answer) for answer in [0,1]] for label in ('a','b')}
    assert [x['D_exact'] for x in branch_cert['a']]==['13','19']
    assert [x['D_exact'] for x in branch_cert['b']]==['13','21']
    for label in ('a','b'):
        for c in branch_cert[label]:
            assert c['n']==9 and len(c['profiles'])==1
            profile=c['profiles'][0]['gains']
            assert c['profiles'][0]['probability_exact']=='1'
            assert all(profile[i]>=profile[i+1] for i in range(len(profile)-1))
            assert all(sum(profile[:k])==c['coverage_envelope'][k] for k in range(len(profile)+1))
    cuts=[]
    gram=gram_of(raw18['a']['rows'],9)
    assert gram==gram_of(raw18['b']['rows'],9)
    for mask in range(1<<9):
        subset={q for q in range(9) if mask>>q&1}
        values={label:sum(bool(subset.intersection(row)) and not set(row).issubset(subset)
                          for row in raw18[label]['rows']) for label in ('a','b')}
        cross=sum(gram[i][j] for i in subset for j in range(9) if j not in subset)
        assert cross%2==0 and values['a']==values['b']==cross//2
        cuts.append(dict(subset_mask=mask,cut_a=values['a'],cut_b=values['b'],gram_cross_half=cross//2))
    write_json(out/'structural_checks.json',structural)
    write_json(out/'independent_branch_profiles.json',branch_cert)
    write_json(out/'all_base18_cut_checks.json',cuts)
    write_json(out/'summary.json',dict(completed=now(),passed=True,structural_graphs=len(structural),
        independently_reviewed_branches=4,all_cut_subsets_checked=512,
        connected18_optimal_cost_contrast='N/324+O(1)',
        connected18_regret_contrast_leading=0,
        source_claim='Connection positive; regret-linear amplification negative for this particular merged-column lift'))
    write_json(out/'manifest.json',{p.name:digest(p) for p in out.glob('*.json') if p.name!='manifest.json'})
    print(json.dumps(dict(passed=True,graphs=len(structural),branches=4,cuts=512)))


if __name__=='__main__':
    run()
