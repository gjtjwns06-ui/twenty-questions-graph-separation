"""Recompute the selected finite witness using exact integer/Fraction recurrences."""
from fractions import Fraction
from functools import cache
import json
from pathlib import Path
import sys
import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'research'))
from tq.core import ExactSolver, columns_of


def main():
    pair = json.loads((ROOT/'research/runs/hubfree_search_v1/best.json').read_text(encoding='utf-8'))
    grams = []
    report = {}
    for world in ['bad','good']:
        saved = pair[world]['graph']
        rows = [tuple(r) for r in saved['rows']]
        assert len(rows) == len(set(rows)) == 38 and all(len(r)==3 for r in rows)
        cols = columns_of(rows,18)
        grams.append([[sum(i in r and j in r for r in rows) for j in range(18)] for i in range(18)])
        graph = nx.Graph()
        graph.add_edges_from((('o',i),('q',q)) for i,r in enumerate(rows) for q in r)
        assert nx.is_biconnected(graph)
        assert max(sum(q in r for r in rows) for q in range(18)) == 10
        solver = ExactSolver(rows,18,seconds=30,max_states=500000)
        optimum = solver.solve()
        assert optimum['optimal_total'] == saved['exact']['optimal_total']
        @cache
        def greedy(s):
            if s.bit_count() < 2:
                return Fraction(0)
            splits = [(s&c,s&~c) for c in cols if s&c and s&~c]
            score = min(abs(a.bit_count()-b.bit_count()) for a,b in splits)
            best = [(a,b) for a,b in splits if abs(a.bit_count()-b.bit_count()) == score]
            return s.bit_count()+sum((greedy(a)+greedy(b) for a,b in best),Fraction(0))/len(best)
        total = greedy((1<<38)-1)
        regret = (total-optimum['optimal_total'])/38
        assert str(regret) == saved['greedy']['gap_exact']
        assert optimum['argmin'] == saved['greedy']['root_questions'] == [3,12]
        report[world] = dict(optimal_total=optimum['optimal_total'],greedy_total=str(total),regret=str(regret))
    assert grams[0] == grams[1]
    assert report['bad']['regret'] == '13/76' and report['good']['regret'] == '0'
    print(json.dumps(dict(passed=True,rows=38,questions=18,same_indexed_gram=True,no_articulation=True,worlds=report)))


if __name__ == '__main__':
    main()
