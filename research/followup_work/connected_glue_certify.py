"""Connected lifts by identifying a nonconstant corresponding question.

Only new follow-up artifacts are written. Existing runs and sources are read-only.
"""
from fractions import Fraction
import json
from pathlib import Path
from extremal_certify import coverage_certificate
from extremal_experiment import evaluate
from tq.core import columns_of, control_check
from tq.io import digest, write_json, now, read_jsonl


def glue(rows, m, port, copies):
    def column(q, block):
        return 0 if q == port else 1 + block*(m-1) + q - (q > port)
    return [tuple(sorted(column(q,b) for q in row)) for b in range(copies) for row in rows], copies*(m-1)+1


def connected(rows,m):
    neighbors=[set() for _ in range(len(rows)+m)]
    for i,row in enumerate(rows):
        for q in row:
            neighbors[i].add(len(rows)+q)
            neighbors[len(rows)+q].add(i)
    seen={0};stack=[0]
    while stack:
        v=stack.pop()
        unseen=neighbors[v]-seen
        seen.update(unseen);stack.extend(unseen)
    return len(seen)==len(neighbors)


def branch_certificate(rows,m,port,answer):
    restricted=[tuple(q-(q>port) for q in row if q!=port)
                for row in rows if int(port in row)==answer]
    c=coverage_certificate(restricted,m-1)
    gains=c['nested_gains']
    nested_concave=bool(gains) and all(a>=b for a,b in zip(gains,gains[1:]))
    c['nested_concave']=nested_concave
    c['optimal_D_exact']=str(sum((2*i+1)*g for i,g in enumerate(gains))) if nested_concave else None
    return c


def main():
    out=Path('followup_work/connected_glue_results')
    out.mkdir(parents=True,exist_ok=False)
    write_json(out/'protocol.json',dict(started=now(),source_sha256=digest(__file__),
        purpose='Exact all-port structural certificate; bounded finite connected checks',
        constraints='Binary, uniform targets, unit cost, degree3; same indexed Gram at each size',
        finite_limits=dict(seconds=3,max_states=250000,max_rss_mb=768),
        finite_cases=['14x8 port3 T=1,2,3','18x9 port3 T=1,2']))
    raw14=json.loads(Path('runs/extremal_analysis_v1/fixed_degree3_base.json').read_text(encoding='utf-8'))
    raw18=json.loads(Path('runs/extremal_pair_design_v1/best.json').read_text(encoding='utf-8'))
    pairs={'base14':dict(m=8,rows={x:raw14[x]['rows'] for x in ('a','b')}),
           'base18':dict(m=9,rows={x:raw18[x]['rows'] for x in ('a','b')})}
    # Preserve the additional four small exploratory port probes used during derivation.
    worlds={w['world_id']:w for w in read_jsonl('runs/main/worlds.jsonl')}
    for parent in ['main-c00-p00147','main-c00-p00117','main-c00-p00087','main-c00-p00144']:
        pairs[parent]=dict(m=8,rows={'a':worlds[parent+'-original']['rows'],
                                    'b':worlds[parent+'-trade0']['rows']})
    records=[]
    for name,pair in pairs.items():
        m=pair['m'];n=len(pair['rows']['a'])
        for port in range(m):
            record=dict(base=name,n=n,m=m,port=port,worlds={})
            for label in ('a','b'):
                branches=[branch_certificate(pair['rows'][label],m,port,a) for a in (0,1)]
                certifiable=all(c['nested_concave'] for c in branches)
                if certifiable:
                    greedy_slope=sum((Fraction(c['D_exact']) for c in branches),Fraction(0))/(2*n)
                    optimal_slope=sum((Fraction(c['optimal_D_exact']) for c in branches),Fraction(0))/(2*n)
                    regret_slope=greedy_slope-optimal_slope
                else:
                    greedy_slope=optimal_slope=regret_slope=None
                record['worlds'][label]=dict(branches=branches,certified=certifiable,
                    greedy_slope_per_copy_exact=str(greedy_slope) if certifiable else None,
                    optimal_slope_per_copy_exact=str(optimal_slope) if certifiable else None,
                    regret_slope_per_copy_exact=str(regret_slope) if certifiable else None)
            if all(w['certified'] for w in record['worlds'].values()):
                delta=Fraction(record['worlds']['a']['regret_slope_per_copy_exact'])-Fraction(record['worlds']['b']['regret_slope_per_copy_exact'])
                record['regret_a_minus_b_per_copy_exact']=str(delta)
                record['regret_a_minus_b_per_object_exact']=str(delta/n)
            records.append(record)
    write_json(out/'all_port_certificates.json',records)
    limits=dict(seconds=3,max_states=250000,max_rss_mb=768)
    finite=[]
    for name,copies_list in [('base14',[1,2,3]),('base18',[1,2])]:
        pair=pairs[name]
        for copies in copies_list:
            expanded={label:glue(rows,pair['m'],3,copies) for label,rows in pair['rows'].items()}
            checks=control_check(expanded['a'][0],expanded['b'][0],expanded['a'][1])
            for label,(rows,m) in expanded.items():
                cols=columns_of(rows,m);size=len(rows)
                imbalance={q:abs(size-2*c.bit_count()) for q,c in enumerate(cols) if 0<c.bit_count()<size}
                least=min(imbalance.values())
                root=[q for q,v in imbalance.items() if v==least]
                assert connected(rows,m)
                assert all(0<c.bit_count()<size for c in cols)
                result=evaluate(rows,m,limits)
                finite.append(dict(base=name,copies=copies,label=label,port=3,shared_question=0,
                    n=size,m=m,connected=True,all_columns_nonconstant=True,greedy_root_questions=root,
                    checks=checks,result=result))
                print(json.dumps(dict(base=name,copies=copies,label=label,status=result['exact']['status'])),flush=True)
    write_json(out/'finite_connected_checks.json',finite)
    summary=dict(completed=now(),all_port_cases=len(records),
        base14_port3_regret_contrast='R_A-R_B=N/784+O(1)',
        base18_all_ports_regret_contrast_leading_zero=True,
        base18_port3_optimal_cost_contrast='Copt_B-Copt_A=N/324+O(1)',
        hub_pair_connector_stronger_regret_contrast='2N/841+O(1); proof in CONNECTED_AGENT.md',
        finite_statuses=[dict(base=r['base'],copies=r['copies'],label=r['label'],status=r['result']['exact']['status']) for r in finite])
    write_json(out/'summary.json',summary)
    write_json(out/'manifest.json',{p.name:digest(p) for p in out.glob('*.json') if p.name!='manifest.json'})


if __name__=='__main__':
    main()
