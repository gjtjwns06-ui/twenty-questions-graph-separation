"""Independent optimal-control signatures for block direct sums."""
from functools import lru_cache
import json
from pathlib import Path
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tq.core import columns_of
from tq.io import write_json


def full_costs(rows,m):
    columns=columns_of(rows,m)
    costs=[0]*(1<<len(rows))
    for mask in range(1,len(costs)):
        if mask.bit_count()>1:
            costs[mask]=mask.bit_count()+min(costs[a]+costs[mask^a]
                for c in columns if (a:=mask&c) and a!=mask)
    return columns,costs


def main():
    base=json.loads(Path('runs/extremal_analysis_v1/fixed_degree3_base.json').read_text())
    intern={}
    signatures={}
    outputs={}
    for label in ['a','b']:
        rows=base[label]['rows']; m=base[label]['m']
        cols,F=full_costs(rows,m)
        @lru_cache(None)
        def signature(mask):
            if not mask:
                return 0
            options=set()
            for col in cols:
                yes=mask&col
                if yes:
                    options.add((yes.bit_count(),F[yes],signature(mask^yes)))
            key=(mask.bit_count(),tuple(sorted(options)))
            if key not in intern:
                intern[key]=len(intern)+1
                signatures[intern[key]]=key
            return intern[key]
        sid=signature((1<<len(rows))-1)
        outputs[label]=dict(initial_signature=sid,reachable_local_states=signature.cache_info().currsize,
            initial_options=signatures[sid])
    result=dict(equal=outputs['a']['initial_signature']==outputs['b']['initial_signature'],worlds=outputs,
        all_signatures={str(k):v for k,v in signatures.items()})
    write_json('followup_work/optimal_signature_result.json',result)
    print(json.dumps(dict(equal=result['equal'],worlds=outputs)))


if __name__=='__main__':main()
