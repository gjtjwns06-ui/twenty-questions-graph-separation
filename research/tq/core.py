from __future__ import annotations

from collections import defaultdict
from fractions import Fraction
from functools import lru_cache
from itertools import combinations
import math
import random
import time


def columns_of(rows, m):
    return [sum(1 << i for i, row in enumerate(rows) if q in row) for q in range(m)]


def gram_of(rows, m):
    cols = columns_of(rows, m)
    return [[(a & b).bit_count() for b in cols] for a in cols]


def control_check(rows, changed, m):
    g = gram_of(rows, m)
    same_g = g == gram_of(changed, m)
    r = [len(x) for x in rows]
    checks = dict(same_gram=same_g, same_row_degrees=r == [len(x) for x in changed],
                  unique_rows=len(set(map(tuple, changed))) == len(changed),
                  valid_columns=all(0 <= q < m for row in changed for q in row))
    assert all(checks.values()), checks
    c4 = sum(g[j][k] * (g[j][k] - 1) // 2 for j, k in combinations(range(m), 2))
    assert set(r) == {3}
    c6 = (sum(g[j][k] * g[k][l] * g[j][l] for j, k, l in combinations(range(m), 3))
          - sum(g[j][k] ** 2 for j, k in combinations(range(m), 2)) + 2 * len(rows))
    return dict(**checks, row_degrees=r, gram=g, c4=c4, c6=c6,
                triple_histogram={"0": math.comb(m, 3) - len(rows), "1": len(rows)})


def generate_parent(n, m, family, rng):
    """Uniform subsets, or an embedded random Pasch with weighted background."""
    universe = list(combinations(range(m), 3))
    if family == "natural":
        return [tuple(x) for x in rng.sample(universe, n)]
    q = rng.sample(range(m), 6)
    seed = [(0, 2, 4), (0, 3, 5), (1, 2, 5), (1, 3, 4)]
    planted = [tuple(sorted(q[i] for i in row)) for row in seed]
    available = [row for row in universe if row not in planted]
    if family == "planted":
        background = rng.sample(available, n - 4)
    elif family == "modular":
        # Successive sampling without replacement, weight 6 for within-module triples.
        order = rng.sample(range(m), m)
        groups = {q: i // ((m + 1) // 2) for i, q in enumerate(order)}
        keys = [(rng.random() ** (1 / (6 if len({groups[q] for q in row}) == 1 else 1)), row)
                for row in available]
        background = [row for _, row in sorted(keys, reverse=True)[:n - 4]]
    else:
        raise ValueError(family)
    rows = planted + background
    rng.shuffle(rows)
    return rows


def find_trades(rows):
    """Enumerate each embedded Pasch once, before seeing any costs.

    Every two Pasch triples intersect once. A third triple selects one of each
    of their nonshared vertices and a sixth vertex; the fourth is forced.
    """
    rowset = set(rows)
    pair_index = defaultdict(list)
    for row in rows:
        for pair in combinations(row, 2):
            pair_index[pair].append(row)
    candidates = {}
    for a, b in combinations(rows, 2):
        shared = set(a) & set(b)
        if len(shared) != 1:
            continue
        common = next(iter(shared))
        aa, bb = set(a) - shared, set(b) - shared
        for x in aa:
            for y in bb:
                for c in pair_index.get(tuple(sorted((x, y))), []):
                    z = next(iter(set(c) - {x, y}))
                    if z in set(a) | set(b):
                        continue
                    d = tuple(sorted((next(iter(aa - {x})), next(iter(bb - {y})), z)))
                    if d not in rowset:
                        continue
                    removed = tuple(sorted((a, b, c, d)))
                    if removed in candidates:
                        continue
                    vertices = sorted(set(a) | set(b) | {z})
                    edges = set(pair for row in removed for pair in combinations(row, 2))
                    added = tuple(t for t in combinations(vertices, 3)
                                  if t not in removed and all(p in edges for p in combinations(t, 2)))
                    assert len(added) == 4 and common in vertices
                    valid = not bool(set(added) & (rowset - set(removed)))
                    candidates[removed] = dict(removed=removed, added=added, valid=valid,
                                               reason=None if valid else "duplicate_after_trade")
    return [candidates[k] for k in sorted(candidates)]


def apply_trade(rows, trade):
    assert trade["valid"]
    mapping = dict(zip(trade["removed"], trade["added"]))
    changed = [mapping.get(row, row) for row in rows]
    log = dict(removed=trade["removed"], added=trade["added"],
               row_replacements=[dict(index=i, before=a, after=b)
                                 for i, (a, b) in enumerate(zip(rows, changed)) if a != b])
    return changed, log


class ResourceLimit(RuntimeError):
    pass


class ExactSolver:
    """Integer DP over reachable candidate sets, equivalent to exhaustive DP."""
    def __init__(self, rows, m, seconds=10.0, max_states=1000000, max_rss_mb=1024):
        self.rows, self.m, self.n = rows, m, len(rows)
        assert len(set(map(tuple, rows))) == self.n
        self.columns = columns_of(rows, m)
        self.full = (1 << self.n) - 1
        self.cache = {0: 0}
        self.deadline = time.perf_counter() + seconds
        self.max_states, self.max_rss_mb = max_states, max_rss_mb
        self.calls = 0

    def splits(self, mask):
        return [(q, yes, mask ^ yes) for q, col in enumerate(self.columns)
                if (yes := mask & col) and yes != mask]

    def cost(self, mask):
        if mask.bit_count() <= 1:
            return 0
        if mask in self.cache:
            return self.cache[mask]
        self.calls += 1
        if self.calls % 128 == 1:
            if time.perf_counter() > self.deadline:
                raise ResourceLimit("time_limit")
            if len(self.cache) >= self.max_states:
                raise ResourceLimit("state_limit")
            import psutil
            if psutil.Process().memory_info().rss > self.max_rss_mb * 2**20:
                raise ResourceLimit("memory_limit")
        values = [self.cost(a) + self.cost(b) for _, a, b in self.splits(mask)]
        if not values:
            raise ValueError("indistinguishable_objects")
        result = mask.bit_count() + min(values)
        self.cache[mask] = result
        return result

    def solve(self):
        start = time.perf_counter()
        try:
            optimal = self.cost(self.full)
            first = [None] * self.m
            for q, a, b in self.splits(self.full):
                first[q] = self.n + self.cost(a) + self.cost(b)
            argmin = [q for q, value in enumerate(first) if value == optimal]

            def tree(mask):
                if mask.bit_count() == 1:
                    return dict(object=mask.bit_length() - 1)
                target = self.cost(mask) - mask.bit_count()
                q, a, b = next((q, a, b) for q, a, b in self.splits(mask)
                               if self.cost(a) + self.cost(b) == target)
                return dict(question=q, yes=tree(a), no=tree(b))

            optimal_tree = tree(self.full)
            depths = []
            for i, row in enumerate(self.rows):
                t, depth = optimal_tree, 0
                while "question" in t:
                    depth += 1
                    t = t["yes"] if t["question"] in row else t["no"]
                assert t["object"] == i
                depths.append(depth)
            assert sum(depths) == optimal
            return dict(status="complete", optimal_total=optimal, optimal_mean=optimal / self.n,
                        first_totals=first, argmin=argmin, optimal_tree=optimal_tree,
                        replay_depths=depths, states=len(self.cache),
                        elapsed_seconds=time.perf_counter() - start)
        except ResourceLimit as error:
            # Partial values are deliberately NOT emitted as labels.
            return dict(status=str(error), optimal_total=None, first_totals=None, argmin=None,
                        states=len(self.cache), elapsed_seconds=time.perf_counter() - start)


class Lookahead:
    def __init__(self, columns):
        self.columns = columns
        self.value = lru_cache(None)(self._value)

    def splits(self, mask):
        return [(q, a, mask ^ a) for q, col in enumerate(self.columns)
                if (a := mask & col) and a != mask]

    def scores(self, mask, depth):
        size = mask.bit_count()
        return {q: 1 + (a.bit_count() * self.value(a, depth - 1)
                        + b.bit_count() * self.value(b, depth - 1)) / size
                for q, a, b in self.splits(mask)}

    def _value(self, mask, depth):
        if mask.bit_count() <= 1:
            return 0.0
        if depth == 0:
            return math.log2(mask.bit_count())
        return min(self.scores(mask, depth).values())


def tied_min(scores, tolerance=1e-10):
    best = min(scores.values())
    return [q for q, value in scores.items() if abs(value - best) <= tolerance]


def baseline_evaluation(solver, exact, tolerance=1e-10):
    output = {}
    for name, depth in [("random", 0), ("information_gain", 1), ("lookahead2", 2), ("lookahead3", 3)]:
        # A cold cache per method makes root-time comparisons interpretable.
        look = Lookahead(solver.columns)
        start = time.perf_counter()

        def choices(mask):
            if depth == 0:
                return [q for q, _, _ in solver.splits(mask)]
            if depth == 1:
                return tied_min({q: abs(a.bit_count() - b.bit_count())
                                 for q, a, b in solver.splits(mask)}, tolerance)
            return tied_min(look.scores(mask, depth), tolerance)

        root_start = time.perf_counter()
        root = choices(solver.full)
        root_seconds = time.perf_counter() - root_start

        @lru_cache(None)
        def total(mask):
            if mask.bit_count() <= 1:
                return Fraction(0)
            qs = choices(mask)
            return mask.bit_count() + sum((total(mask & solver.columns[q])
                     + total(mask ^ (mask & solver.columns[q])) for q in qs), Fraction(0)) / len(qs)

        actual_total = total(solver.full)
        regret = sum((Fraction(exact["first_totals"][q] - exact["optimal_total"], solver.n)
                      for q in root), Fraction(0)) / len(root)
        hit = Fraction(len(set(root) & set(exact["argmin"])), len(root))
        output[name] = dict(root_questions=root, first_regret=float(regret),
                            first_regret_exact=str(regret), optimal_probability=float(hit),
                            policy_mean=float(actual_total / solver.n),
                            policy_mean_exact=str(actual_total / solver.n),
                            policy_regret=float((actual_total - exact["optimal_total"]) / solver.n),
                            root_seconds=root_seconds, evaluation_seconds=time.perf_counter() - start)
    return output
