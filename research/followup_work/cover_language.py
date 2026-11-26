"""Exact feasible gain languages and local post-yes optimal costs."""
from functools import lru_cache
from pathlib import Path
import json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from followup_work.proof_signature import full_costs
from tq.io import write_json


def main():
    base=json.loads(Path('runs/extremal_analysis_v1/fixed_degree3_base.json').read_text())
    worlds={}
    for label in ['a','b']:
        w=base[label]; cols,F=full_costs(w['rows'],w['m'])
        @lru_cache(None)
        def language(mask):
            if not mask:return {():0}
            result={}
            for col in cols:
                yes=mask&col
                if not yes:continue
                for tail,cost in language(mask^yes).items():
                    profile=(yes.bit_count(),)+tail
                    value=F[yes]+cost
                    result[profile]=min(result.get(profile,value),value)
            return result
        worlds[label]=language((1<<len(w['rows']))-1)
    a,b=worlds['a'],worlds['b']
    result=dict(equal=a==b,count_a=len(a),count_b=len(b),
        a_only=[dict(gains=k,cost=a[k]) for k in sorted(set(a)-set(b))],
        b_only=[dict(gains=k,cost=b[k]) for k in sorted(set(b)-set(a))],
        cost_differences=[dict(gains=k,a=a[k],b=b[k]) for k in sorted(set(a)&set(b)) if a[k]!=b[k]],
        languages={label:[dict(gains=k,cost=v) for k,v in sorted(d.items())] for label,d in worlds.items()})
    write_json('followup_work/cover_language_result.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='languages'}))


if __name__=='__main__':main()
