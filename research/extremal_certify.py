#!/usr/bin/env python3
"""Independent finite audit and executable structural certificates."""
from collections import defaultdict
from fractions import Fraction
from functools import lru_cache
from itertools import combinations, product
import argparse
import json
from pathlib import Path
from extremal_experiment import evaluate, GreedyCosts, canonical
from tq.core import columns_of, gram_of, control_check, ExactSolver
from tq.io import Profile, read_jsonl, write_json, digest, now


def exhaustive_audit(rows, m):
    """All 2^n candidate sets, independent of reachable-state search traversal."""
    cols = columns_of(rows, m)
    n, full = len(rows), (1 << len(rows)) - 1
    optimal, minimum, maximum = [0]*(full+1), [0]*(full+1), [0]*(full+1)
    uniform = [Fraction(0)]*(full+1)
    with Profile() as profile:
        for mask in range(1, full+1):
            size = mask.bit_count()
            if size <= 1:
                continue
            options = [(q, a, mask^a) for q, c in enumerate(cols) if (a:=mask&c) and a != mask]
            optimal[mask] = size+min(optimal[a]+optimal[b] for q,a,b in options)
            imbalance = min(abs(a.bit_count()-b.bit_count()) for q,a,b in options)
            ties = [(a,b) for q,a,b in options if abs(a.bit_count()-b.bit_count()) == imbalance]
            uniform[mask] = size+sum((uniform[a]+uniform[b] for a,b in ties),Fraction(0))/len(ties)
            minimum[mask] = size+min(minimum[a]+minimum[b] for a,b in ties)
            maximum[mask] = size+max(maximum[a]+maximum[b] for a,b in ties)
    first = [n+optimal[c]+optimal[full^c] if c and c!=full else None for c in cols]
    return dict(optimal_total=optimal[full], first_totals=first,
        greedy_total_uniform_exact=str(uniform[full]), greedy_total_min=minimum[full],
        greedy_total_max=maximum[full], all_subsets=full, profile=profile.result)


def coverage_certificate(rows, m):
    """Exact coverage envelope, random greedy profiles, and post-first-yes cost."""
    cols = columns_of(rows,m)
    n, full = len(rows), (1<<len(rows))-1
    f, achieving = [0]*(m+1), [None]*(m+1)
    for k in range(m+1):
        for qs in combinations(range(m),k):
            union = 0
            for q in qs:
                union |= cols[q]
            size = union.bit_count()
            if size > f[k] or achieving[k] is None:
                f[k], achieving[k] = size, list(qs)
    greedy = GreedyCosts(cols)

    @lru_cache(None)
    def distribution(mask):
        if not mask:
            return {():Fraction(1)}, Fraction(0)
        best = max((mask&c).bit_count() for c in cols)
        ties = [mask&c for c in cols if (mask&c).bit_count()==best]
        result, post = defaultdict(Fraction), Fraction(0)
        for yes in ties:
            no = mask^yes
            tail, tailpost = distribution(no)
            for gains,p in tail.items():
                result[(best,)+gains] += p/len(ties)
            post += (greedy.cost(yes)[0]+tailpost)/len(ties)
        return dict(result), post

    profiles, post = distribution(full)
    mu, variance = [], []
    for s in range(1,max(f[1],1)+1):
        mean = sum((sum(g>=s for g in gains)*p for gains,p in profiles.items()),Fraction(0))
        second = sum((sum(g>=s for g in gains)**2*p for gains,p in profiles.items()),Fraction(0))
        mu.append(mean)
        variance.append(second-mean**2)
    d = sum((x*x for x in mu),Fraction(0))
    # Find a nested ordered cover attaining EVERY envelope prefix through coverage.
    chain = None
    def visit(mask, qs):
        nonlocal chain
        if mask == full:
            chain = list(qs)
            return True
        for q in range(m):
            if q not in qs and (mask|cols[q]).bit_count()==f[len(qs)+1]:
                if visit(mask|cols[q],qs+(q,)):
                    return True
        return False
    visit(0,())
    gains, local_opt_totals = [], []
    if chain:
        solver = ExactSolver(rows,m,seconds=10,max_states=1000000,max_rss_mb=1024)
        remaining = full
        for q in chain:
            yes = remaining&cols[q]
            gains.append(yes.bit_count())
            local_opt_totals.append(solver.cost(yes))
            remaining ^= yes
    return dict(n=n,m=m,coverage_envelope=f,achieving_sets=achieving,nested_order=chain,
        nested_gains=gains,local_optimal_postyes_totals=local_opt_totals,
        nested_optimal_postyes_mean_exact=str(Fraction(sum(local_opt_totals),n)),
        profiles=[dict(gains=list(g),probability_exact=str(p)) for g,p in sorted(profiles.items())],
        mu_exact=list(map(str,mu)),variance_exact=list(map(str,variance)),
        D_exact=str(d),virtual_cover_slope_exact=str(d/(2*n)),
        virtual_cover_intercept_exact=str((n+sum(variance,Fraction(0)))/(2*n)),
        expected_local_postyes_greedy_exact=str(post/n))


def direct_sum(rows,m,t):
    return [tuple(q+b*m for q in row) for b in range(t) for row in rows],m*t


def cartesian(rows,m,k):
    return [tuple(q+b*m for b,index in enumerate(indices) for q in rows[index])
            for indices in product(range(len(rows)),repeat=k)],m*k


def main(out_path='runs/extremal_analysis_v1', pair_run='runs/extremal_pair_design_v1'):
    out=Path(out_path)
    out.mkdir(parents=True,exist_ok=False)
    write_json(out/'protocol.json',dict(created=now(),purpose='Independent audits and theorem certificates; no retuning',
        sources={p:digest(p) for p in ['extremal_certify.py','extremal_experiment.py','tq/core.py']},
        full_subset_audit_sizes=[18],explicit_lift_checks=['degree3 directsum T=2','cartesian k=2'],
        lift_limits=dict(seconds=20,max_states=1500000,max_rss_mb=1024)))
    best=json.loads((Path(pair_run)/'best.json').read_text(encoding='utf-8'))
    audit={}
    for label in ('a','b'):
        world=best[label]
        independent=exhaustive_audit(world['rows'],world['m'])
        assert independent['optimal_total']==world['exact']['optimal_total']
        assert independent['first_totals']==world['exact']['first_totals']
        assert independent['greedy_total_uniform_exact']==world['greedy']['total_uniform_exact']
        assert independent['greedy_total_min']==world['greedy']['total_min_ties']
        assert independent['greedy_total_max']==world['greedy']['total_max_ties']
        audit[label]=independent
    audit['same_gram_checks']=control_check(best['a']['rows'],best['b']['rows'],best['a']['m'])
    write_json(out/'new18_independent_audit.json',audit)
    worlds={w['world_id']:w for w in read_jsonl('runs/main/worlds.jsonl')}
    source_ids=['main-c01-p00102-original','main-c01-p00102-trade0']
    base={label:evaluate(worlds[wid]['rows'],8,dict(seconds=10)) for label,wid in zip(('a','b'),source_ids)}
    certificates={label:coverage_certificate(w['rows'],8) for label,w in base.items()}
    assert certificates['a']['coverage_envelope'][:4]==certificates['b']['coverage_envelope'][:4]==[0,7,12,14]
    assert certificates['a']['nested_gains']==certificates['b']['nested_gains']==[7,5,2]
    assert certificates['a']['D_exact']=='65/2' and certificates['b']['D_exact']=='67/2'
    assert certificates['a']['nested_optimal_postyes_mean_exact']==certificates['b']['nested_optimal_postyes_mean_exact']=='17/7'
    write_json(out/'fixed_degree3_base.json',dict(source_ids=source_ids,a=base['a'],b=base['b'],
        checks=control_check(base['a']['rows'],base['b']['rows'],8),certificates=certificates))
    no_linear={label:coverage_certificate(best[label]['rows'],9) for label in ('a','b')}
    assert no_linear['a']['D_exact']==no_linear['b']['D_exact']=='40'
    write_json(out/'new18_directsum_negative.json',dict(certificates=no_linear,
        conclusion='Both leading greedy and optimal directsum costs are10T/9; no linear regret amplification from this lift'))
    checks=[]
    limits=dict(seconds=20,max_states=1500000,max_rss_mb=1024)
    for label,w in base.items():
        rows,m=direct_sum(w['rows'],8,2)
        result=evaluate(rows,m,limits)
        assert result['exact']['status']=='complete'
        checks.append(dict(kind='directsum',copies=2,base=label,result=result,
            interpretation='Exact finite label, not filled from an asymptotic expression'))
    assert gram_of(checks[0]['result']['rows'],16)==gram_of(checks[1]['result']['rows'],16)
    # Product amplifies the stronger18gadget but increases each row degree to6.
    for label in ('a','b'):
        w=best[label]
        rows,m=cartesian(w['rows'],9,2)
        result=evaluate(rows,m,limits)
        if result['exact']['status']=='complete':
            assert result['exact']['optimal_total']==2*w['exact']['optimal_total']*18
            assert Fraction(result['greedy']['mean_uniform_exact'])==2*Fraction(w['greedy']['mean_uniform_exact'])
        checks.append(dict(kind='cartesian',copies=2,base=label,result=result,
            interpretation='Row degree6 extension; resource limits remain incomplete if encountered'))
    assert gram_of(checks[2]['result']['rows'],18)==gram_of(checks[3]['result']['rows'],18)
    write_json(out/'explicit_lift_checks.json',checks)
    scaling=[]
    for t in [1,2,4,8,16,32,64,81,128,256,512,1024]:
        lower=Fraction(t-71,28)-Fraction(393,14*t)
        scaling.append(dict(T=t,N=14*t,m=8*t,row_degree=3,
            optimal_leading_exact=str(Fraction(8*t,7)),
            greedy_a_leading_exact=str(Fraction(65*t,56)),greedy_b_leading_exact=str(Fraction(67*t,56)),
            regret_contrast_leading_exact=str(Fraction(t,28)),
            certified_regret_b_minus_a_lower_exact=str(lower),
            certified_regret_b_minus_a_lower=float(lower),source='Proved bounds, NOT exact DP measurements'))
    write_json(out/'scaling_bounds.json',scaling)
    write_json(out/'summary.json',dict(completed=now(),independent_full_subset_audits_passed=True,
        explicit_lift_statuses=[dict(kind=x['kind'],base=x['base'],status=x['result']['exact']['status']) for x in checks],
        fixed_degree3_linear_regret_contrast='N/392+O(1)',fixed_degree3_ratio='bounded; limits65/64 and67/64',
        new18_cartesian_contrast='2k/9 withdegree3k',new18_directsum_linear_contrast=False))
    write_json(out/'manifest.json',{p.name:digest(p) for p in out.glob('*.json') if p.name!='manifest.json'})
    print(json.dumps(dict(audit='passed',explicit_lift_statuses=[r['result']['exact']['status'] for r in checks])))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',default='runs/extremal_analysis_v1')
    parser.add_argument('--pair-run',default='runs/extremal_pair_design_v1')
    args=parser.parse_args()
    main(args.out,args.pair_run)
