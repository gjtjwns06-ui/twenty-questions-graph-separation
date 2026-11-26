"""Permutation-equivariant question features; no exact solver or labels imported."""
from itertools import combinations
import math
import numpy as np
from .core import Lookahead, columns_of, gram_of


def summary(values):
    a = np.asarray(list(values), dtype=float)
    if not len(a):
        return [0.0] * 7
    return [float(a.mean()), float(a.std()), float(a.min()), float(a.max()),
            float(np.quantile(a, .25)), float(np.quantile(a, .75)), float(np.mean(np.abs(a) <= 1e-10))]


SUMMARY_NAMES = ["mean", "std", "min", "max", "q25", "q75", "zero_fraction"]


def put_summary(out, prefix, values):
    out.update({prefix + "_" + key: value for key, value in zip(SUMMARY_NAMES, summary(values))})


def components(adjacency):
    remaining = set(range(len(adjacency)))
    sizes = []
    while remaining:
        stack = [remaining.pop()]
        size = 0
        while stack:
            v = stack.pop()
            size += 1
            new = {int(x) for x in np.flatnonzero(adjacency[v])} & remaining
            remaining -= new
            stack.extend(new)
        sizes.append(size)
    return sizes


def make_features(rows, m):
    n = len(rows)
    cols = columns_of(rows, m)
    full = (1 << n) - 1
    g = np.array(gram_of(rows, m), dtype=float)
    look = Lookahead(cols)
    hs = {d: look.scores(full, d) for d in (1, 2, 3)}
    result = []
    for q in hs[1]:
        count = int(g[q, q])
        p = count / n
        base = dict(n=float(n), m=float(m), density=3 / m, yes_fraction=p,
                    split_imbalance=abs(1 - 2 * p),
                    entropy=-p * math.log2(p) - (1 - p) * math.log2(1 - p))
        other = [j for j in range(m) if j != q]
        put_summary(base, "question_degrees", np.diag(g) / n)
        put_summary(base, "global_pair_overlap", [g[j, k] / n for j, k in combinations(range(m), 2)])
        put_summary(base, "focal_pair_overlap", [g[q, j] / n for j in other])
        put_summary(base, "next_yes_counts", [g[q, j] / count for j in other])
        put_summary(base, "next_no_counts", [(g[j, j] - g[q, j]) / (n - count) for j in other])
        conditional = {}
        for answer, mask in [("yes", cols[q]), ("no", full ^ cols[q])]:
            size = mask.bit_count()
            conditional[answer + "_size"] = float(size)
            active = [j for j in other if 0 < (cols[j] & mask).bit_count() < size]
            conditional[answer + "_active_fraction"] = len(active) / max(m - 1, 1)
            if active:
                cg = np.array([[(cols[j] & cols[k] & mask).bit_count() / size
                                for k in active] for j in active])
                overlaps = [cg[j, k] for j, k in combinations(range(len(active)), 2)]
                adjacency = cg > 0
                np.fill_diagonal(adjacency, False)
                sizes = components(adjacency)
                spectra = np.linalg.eigvalsh(cg)
            else:
                overlaps, sizes, spectra = [], [], []
            put_summary(conditional, answer + "_conditional_pair", overlaps)
            put_summary(conditional, answer + "_spectrum", spectra)
            put_summary(conditional, answer + "_components", sizes)
            conditional[answer + "_component_count"] = float(len(sizes))
        search = {}
        for d in (1, 2, 3):
            search[f"H{d}"] = hs[d][q]
            search[f"H{d}_gap"] = hs[d][q] - min(hs[d].values())
        # Suppress eigensolver roundoff near zero and question-permutation noise.
        groups = [base, conditional, search]
        for group in groups:
            for name, value in group.items():
                group[name] = 0.0 if abs(value) <= 1e-10 else round(float(value), 12)
        result.append(dict(question=q, base=base, conditional=conditional, search=search))
    return result


BLOCKS = {
    "base": ["base"],
    "base_conditional": ["base", "conditional"],
    "base_search": ["base", "search"],
    "all": ["base", "conditional", "search"],
}


def flatten(feature, block):
    return {group + "." + name: value for group in BLOCKS[block]
            for name, value in sorted(feature[group].items())}
