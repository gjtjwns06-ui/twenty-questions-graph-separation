"""Check exact finite gain-language dominance in both directions."""
from pathlib import Path
import json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tq.io import write_json


def cumsum(gains,m=8):
    acc=0;out=[]
    for i in range(m):
        if i<len(gains):acc+=gains[i]
        out.append(acc)
    return out


def main():
    data=json.loads(Path('followup_work/cover_language_result.json').read_text())
    languages=data['languages']; result={}
    for src,tgt in [('a','b'),('b','a')]:
        unmatched=[];matches=[]
        for x in languages[src]:
            cx=cumsum(x['gains'])
            found=next((y for y in languages[tgt] if y['cost']<=x['cost'] and
                all(a>=b for a,b in zip(cumsum(y['gains']),cx))),None)
            if found is None:unmatched.append(x)
            else:matches.append(dict(source=x,target=found))
        result[src+'_by_'+tgt]=dict(all_dominated=not unmatched,unmatched=unmatched,matches=matches)
    write_json('followup_work/profile_dominance_result.json',result)
    print(json.dumps({k:{'all_dominated':v['all_dominated'],'unmatched':v['unmatched']} for k,v in result.items()}))


if __name__=='__main__':main()
