"""Exact audit of two *natural*, not all possible, binary encodings of HS26.

Reconstructs equations (6)-(8) of arXiv:2610.07771v1.  No classifier
training or independent validation of that paper's complexity proofs is claimed.
"""
from collections import Counter
from hashlib import sha256
from functools import cache
from fractions import Fraction
from itertools import combinations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'runs' / 'novelty_audit_v1'


def tables(n):
    N, m = 2**n, 2**(n-1)
    fast, slow = [], []
    for z in range(N):
        f = [1 + ((z >> (i % n)) & 1) for i in range(m)]
        s = [((1 if z == i else 2) if z < m else
              (2 if z-m == i else 1)) for i in range(m)]
        v = [0 if z == k else 1 for k in range(N)]
        fast.append(f + v)
        slow.append(s + v)
    for j in range(m):
        p = [0 if j == i else 3 + ((j >> (i % n)) & 1) for i in range(m)]
        fast.append(p + [1]*N)
        slow.append(p + [1]*N)
    return fast, slow


def gram(M):
    cols = list(zip(*M))
    return [[sum(x*y for x, y in zip(a, b)) for b in cols] for a in cols]


def incidence(rows, m):
    return [[int(j in r) for j in range(m)] for r in rows]


def cut_profile(rows, m):
    return [sum(bool(set(r) & {i for i in range(m) if mask >> i & 1}) and
                bool(set(r) - {i for i in range(m) if mask >> i & 1}) for r in rows)
            for mask in range(1 << m)]


def small_costs(M):
    @cache
    def solve(S):
        if len(S) <= 1:
            return 0, Fraction(0)
        splits = []
        for q in range(len(M[0])):
            a = tuple(i for i in S if M[i][q])
            b = tuple(i for i in S if not M[i][q])
            if a and b:
                splits.append((a, b))
        vals = [(len(a), solve(a), solve(b)) for a, b in splits]
        opt = len(S) + min(a[0] + b[0] for _, a, b in vals)
        best = max(min(n, len(S)-n) for n, _, _ in vals)
        eligible = [(a[1] + b[1]) for n, a, b in vals if min(n, len(S)-n) == best]
        return opt, len(S) + sum(eligible, Fraction(0))/len(eligible)
    opt, greedy = solve(tuple(range(len(M))))
    return dict(optimal_mean=str(Fraction(opt, len(M))), greedy_mean=str(greedy/len(M)))


def main():
    records = []
    for n in (4, 5, 6):
        F, S = tables(n)
        H, q = len(F), len(F[0])
        assert all(Counter(a) == Counter(b) for a, b in zip(zip(*F), zip(*S)))
        target_f = [[int(x == 0) for x in r] for r in F]
        target_s = [[int(x == 0) for x in r] for r in S]
        assert target_f == target_s
        assert all(sum(r) == 1 for r in target_f)
        assert len({tuple(r) for r in target_f}) == H
        # Column (query i, returned label y), with labels 0,...,4.
        one_f = [[int(x == y) for x in r for y in range(5)] for r in F]
        one_s = [[int(x == y) for x in r for y in range(5)] for r in S]
        gf, gs = gram(one_f), gram(one_s)
        a, b = 1, 6  # (p0, label1), (p1, label1)
        assert gf[a][b] == 2**n//4
        assert gs[a][b] == 2**n//2-2
        assert gf[a][b] != gs[a][b]
        records.append(dict(n=n, victims=H, original_queries=q,
            matched_all_one_query_label_histograms=True,
            target_indicator_tables_identical=True,
            target_indicator_row_degree=1,
            onehot_row_degree=q, onehot_columns=5*q,
            onehot_gram_equal=False,
            mismatch=dict(columns=['(p0,label1)', '(p1,label1)'],
                          fast=gf[a][b], slow=gs[a][b]),
            scope='These two encodings fail to give the present theorem; no impossibility of all reductions is claimed.'))
    out = OUT / 'natural_reduction_checks.json'
    k4, k43 = list(combinations(range(4), 2)), list(combinations(range(4), 3))
    assert cut_profile(k4, 4) == cut_profile(k43, 4)
    g2, g3 = gram(incidence(k4, 4)), gram(incidence(k43, 4))
    assert g2[0][1] == 1 and g3[0][1] == 2
    pa = [(0,2,4), (0,3,5), (1,2,5), (1,3,4)]
    pb = [(0,2,5), (0,3,4), (1,2,4), (1,3,5)]
    ma, mb = incidence(pa, 6), incidence(pb, 6)
    assert gram(ma) == gram(mb)
    ca, cb = small_costs(ma), small_costs(mb)
    assert ca == cb == dict(optimal_mean='2', greedy_mean='2')
    out.write_text(json.dumps(dict(source='https://arxiv.org/html/2610.07771v1',
        source_equations=['6','7','8'], checks=records,
        chen_k4=dict(cut_profile_equal=True, gram_equal=False,
                     off_diagonal_gram=[g2[0][1],g3[0][1]], rows=[len(k4),len(k43)],
                     row_degrees=[2,3]),
        bare_pasch=dict(gram_equal=True, a=ca, b=cb,
                       interpretation='A pair-preserving trade alone does not force any cost separation.'),
        script_sha256=sha256(Path(__file__).read_bytes()).hexdigest()), indent=2), encoding='utf-8')
    print(json.dumps(records))


if __name__ == '__main__':
    main()
