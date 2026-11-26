"""Bounded hub-free cycle gluing search; all old artifacts are read-only."""
from pathlib import Path
from itertools import combinations
from fractions import Fraction
import argparse
import json
import sys
import time
import networkx as nx

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from extremal_experiment import evaluate
from tq.core import control_check,columns_of
from tq.io import write_json,append_jsonl,digest,now,Profile


def cycle_glue(rows,m,left,right,t):
    assert t>=2 and left!=right
    # Edge e_j identifies right port of j with left port of j+1.
    private=[q for q in range(m) if q not in (left,right)]
    private_id={q:i for i,q in enumerate(private)}
    def qid(q,b):
        if q==right:return b
        if q==left:return (b-1)%t
        return t+b*(m-2)+private_id[q]
    result=[tuple(sorted(qid(q,b) for q in row)) for b in range(t) for row in rows]
    return result,t*(m-1)


def structure(rows,m):
    n=len(rows);g=nx.Graph()
    g.add_nodes_from(range(n+m))
    for i,row in enumerate(rows):
        for q in row:g.add_edge(i,n+q)
    articulation=list(nx.articulation_points(g))
    counts=[c.bit_count() for c in columns_of(rows,m)]
    return dict(connected=nx.is_connected(g),question_articulations=sorted(v-n for v in articulation if v>=n),
        object_articulations=sorted(v for v in articulation if v<n),
        biconnected=nx.is_biconnected(g),maximum_question_degree=max(counts),minimum_question_degree=min(counts),
        constant_questions=[q for q,c in enumerate(counts) if c in (0,n)],
        row_degree_set=sorted(set(map(len,rows))))


def run(out_path):
    out=Path(out_path);out.mkdir(parents=True,exist_ok=False)
    source=Path('runs/extremal_analysis_v1/fixed_degree3_base.json')
    base=json.loads(source.read_text(encoding='utf-8'))
    write_json(out/'protocol.json',dict(started=now(),source_sha256=digest(source),code_sha256=digest(__file__),
        constructor='Cycle identify distinctleft/rightports; no globalcolumn; degree≤14',
        small_scan_copies=2,ports='All28unordered distinctpairs of8columns',
        followup='Top3 completed controlledregretcontrasts atcopies3, plusallstructuralT4,8,32,128',
        exact_limits=dict(seconds=3,max_states=250000,max_rss_mb=768),
        scope='Adaptive discovery, no asymptoticregretclaim'))
    records=[]
    with Profile() as overall:
        for left,right in combinations(range(8),2):
            graphs={x:cycle_glue(base[x]['rows'],8,left,right,2) for x in ['a','b']}
            check=control_check(graphs['a'][0],graphs['b'][0],graphs['a'][1])
            record=dict(left=left,right=right,copies=2,checks=check,worlds={})
            for x,(rows,m) in graphs.items():
                st=structure(rows,m)
                assert st['connected'] and st['row_degree_set']==[3] and not st['constant_questions']
                assert st['maximum_question_degree']<=14
                record['worlds'][x]=dict(structure=st,result=evaluate(rows,m,dict(seconds=3,max_states=250000,max_rss_mb=768)))
            record['complete']=all(w['result']['exact']['status']=='complete' for w in record['worlds'].values())
            if record['complete']:
                ga,gb=[Fraction(record['worlds'][x]['result']['greedy']['gap_exact']) for x in ['a','b']]
                record['regret_b_minus_a_exact']=str(gb-ga)
                record['abs_regret_contrast_exact']=str(abs(gb-ga))
            records.append(record)
            append_jsonl(out/'scan.jsonl',record)
        complete=[r for r in records if r['complete']]
        ranked=sorted(complete,key=lambda r:(-abs(Fraction(r['regret_b_minus_a_exact'])),r['left'],r['right']))
        selected=ranked[:3]
        finite=[];large=[]
        for r in selected:
            l,rr=r['left'],r['right']
            graphs={x:cycle_glue(base[x]['rows'],8,l,rr,3) for x in ['a','b']}
            check=control_check(graphs['a'][0],graphs['b'][0],graphs['a'][1])
            record=dict(left=l,right=rr,copies=3,checks=check,worlds={})
            for x,(rows,m) in graphs.items():
                record['worlds'][x]=dict(structure=structure(rows,m),result=evaluate(rows,m,dict(seconds=3,max_states=250000,max_rss_mb=768)))
            finite.append(record)
            for t in [4,8,32,128]:
                for x in ['a','b']:
                    rows,m=cycle_glue(base[x]['rows'],8,l,rr,t)
                    st=structure(rows,m)
                    assert st['biconnected'] and not st['question_articulations'] and st['maximum_question_degree']<=14
                    large.append(dict(left=l,right=rr,copies=t,world=x,n=len(rows),m=m,structure=st,
                        cost_labels='notcomputed'))
    write_json(out/'selected_T3.json',finite)
    write_json(out/'large_structure.json',large)
    write_json(out/'summary.json',dict(completed=now(),profile=overall.result,
        scan_pairs=len(records),completed_pairs=len(complete),biconnected_pairs=sum(all(w['structure']['biconnected'] for w in r['worlds'].values()) for r in records),
        top=[dict(left=r['left'],right=r['right'],contrast=r['abs_regret_contrast_exact'],signed=r['regret_b_minus_a_exact'],
            a_gap=r['worlds']['a']['result']['greedy']['gap_exact'],b_gap=r['worlds']['b']['result']['greedy']['gap_exact']) for r in selected],
        selected_T3_statuses=[dict(left=r['left'],right=r['right'],statuses={x:w['result']['exact']['status'] for x,w in r['worlds'].items()}) for r in finite],
        asymptotic_regret='notproved;localoverlapscoupleprofiles'))
    write_json(out/'manifest.json',{p.name:digest(p) for p in out.glob('*') if p.is_file() and p.name!='manifest.json'})
    print(json.dumps(load_summary(out)),flush=True)


def load_summary(out):
    s=json.loads((out/'summary.json').read_text())
    return {k:v for k,v in s.items() if k not in ['profile']}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',default='final_work/hubfree_agent_cycle_results')
    run(p.parse_args().out)
