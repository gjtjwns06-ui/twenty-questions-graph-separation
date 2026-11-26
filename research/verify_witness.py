#!/usr/bin/env python3
"""Exact independent audit of the 14-object, 8-test witness.

Standard-library only. This checks one constructed example, not a main study.
Run: python3 verify_witness.py --output verification.json
"""
from __future__ import annotations

import argparse
from fractions import Fraction
from itertools import combinations, product
import json
from pathlib import Path

ROWS_A = ["135", "146", "236", "245", "238", "267", "158", "234",
          "378", "357", "156", "157", "123", "368"]
ROWS_B = ["136", "145", "235", "246"] + ROWS_A[4:]
M = 8


def audit(rows):
    n = len(rows)
    profiles = [frozenset(int(x) - 1 for x in row) for row in rows]
    assert len(set(profiles)) == n, "All objects must be distinguishable."
    columns = [sum(1 << i for i, row in enumerate(profiles) if j in row)
               for j in range(M)]
    gram = [[(columns[i] & columns[j]).bit_count() for j in range(M)]
            for i in range(M)]
    full = (1 << n) - 1
    # Bottom-up exhaustive DP over ALL candidate subsets; proper subsets have
    # smaller bitmasks, so this order is topologically valid.
    costs = [0] * (1 << n)
    optimal = [[] for _ in range(1 << n)]
    greedy_costs = [0] * (1 << n)
    greedy_uniform_tie_costs = [Fraction(0)] * (1 << n)
    for mask in range(1, 1 << n):
        size = mask.bit_count()
        if size <= 1:
            continue
        choices = []
        for j, column in enumerate(columns):
            yes = mask & column
            no = mask ^ yes
            if yes and no:
                choices.append((size + costs[yes] + costs[no], j, yes, no))
        assert choices, "Distinct profiles must supply a separating test."
        best = min(c[0] for c in choices)
        costs[mask] = best
        optimal[mask] = [j for c, j, _, _ in choices if c == best]
        # For uniform targets, maximize binary entropy = minimize imbalance.
        # Question ID is the PREDECLARED tie breaker, not an oracle tie break.
        _, gj, gy, gn = min(choices, key=lambda c: (abs(c[2].bit_count() - c[3].bit_count()), c[1]))
        greedy_costs[mask] = size + greedy_costs[gy] + greedy_costs[gn]
        # Independent uniform choice among ALL entropy-maximizing tests at
        # each visited state. Fractions integrate all possible tie outcomes.
        imbalance = min(abs(c[2].bit_count() - c[3].bit_count()) for c in choices)
        tied = [c for c in choices if abs(c[2].bit_count() - c[3].bit_count()) == imbalance]
        greedy_uniform_tie_costs[mask] = size + sum(
            (greedy_uniform_tie_costs[yes] + greedy_uniform_tie_costs[no]
             for _, _, yes, no in tied), Fraction(0)
        ) / len(tied)

    first = []
    for j, column in enumerate(columns):
        yes = full & column
        no = full ^ yes
        first.append(n + costs[yes] + costs[no] if yes and no else None)

    def tree(mask):
        if mask.bit_count() == 1:
            return {"object": mask.bit_length()}
        j = min(optimal[mask])
        yes = mask & columns[j]
        return {"question": j + 1, "yes": tree(yes), "no": tree(mask ^ yes)}

    witness_tree = tree(full)
    depths = []
    for i, profile in enumerate(profiles):
        t = witness_tree
        depth = 0
        while "question" in t:
            depth += 1
            t = t["yes"] if t["question"] - 1 in profile else t["no"]
        assert t["object"] == i + 1
        depths.append(depth)
    assert sum(depths) == costs[full]

    c4 = sum(gram[i][j] * (gram[i][j] - 1) // 2
             for i, j in combinations(range(M), 2))
    column_sets = [{i for i, p in enumerate(profiles) if j in p} for j in range(M)]
    c6_direct = 0
    c6_formula = 0
    triple_counts = {}
    for i, j, k in combinations(range(M), 3):
        ij = column_sets[i] & column_sets[j]
        jk = column_sets[j] & column_sets[k]
        ik = column_sets[i] & column_sets[k]
        t = len(ij & jk)
        triple_counts[f"{i+1},{j+1},{k+1}"] = t
        c6_direct += sum(len({a, b, c}) == 3 for a, b, c in product(ij, jk, ik))
        c6_formula += len(ij) * len(jk) * len(ik) - t * (len(ij) + len(jk) + len(ik)) + 2 * t
    assert c6_direct == c6_formula
    return {
        "rows": rows,
        "n_objects": n, "n_questions": M,
        "row_degrees": list(map(len, profiles)),
        "column_degrees": [gram[j][j] for j in range(M)],
        "gram": gram,
        "total_leaf_depth_optimal": costs[full],
        "mean_optimal_exact": str(Fraction(costs[full], n)),
        "mean_optimal_decimal": costs[full] / n,
        "first_question_total_costs": first,
        "optimal_first_questions": [j + 1 for j in optimal[full]],
        "total_leaf_depth_greedy_id_ties": greedy_costs[full],
        "mean_greedy_id_ties_exact": str(Fraction(greedy_costs[full], n)),
        "greedy_regret_exact": str(Fraction(greedy_costs[full] - costs[full], n)),
        "total_leaf_depth_greedy_uniform_ties_exact": str(greedy_uniform_tie_costs[full]),
        "mean_greedy_uniform_ties_exact": str(greedy_uniform_tie_costs[full] / n),
        "mean_greedy_uniform_ties_decimal": float(greedy_uniform_tie_costs[full] / n),
        "greedy_uniform_ties_regret_exact": str((greedy_uniform_tie_costs[full] - costs[full]) / n),
        "optimal_tree": witness_tree,
        "optimal_tree_object_depths": depths,
        "simple_4cycles": c4,
        "simple_6cycles": c6_direct,
        "triple_counts": triple_counts,
        "subsets_evaluated": full,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("verification.json"))
    args = parser.parse_args()
    a, b = audit(ROWS_A), audit(ROWS_B)
    assert a["gram"] == b["gram"]
    assert a["row_degrees"] == b["row_degrees"] == [3] * 14
    assert a["total_leaf_depth_optimal"] == 54
    assert b["total_leaf_depth_optimal"] == 55
    assert a["first_question_total_costs"] == [55, 54, 55, 58, 55, 55, 56, 57]
    assert b["first_question_total_costs"] == [56, 56, 55, 58, 55, 55, 56, 57]
    assert not set(a["optimal_first_questions"]) & set(b["optimal_first_questions"])
    changed = {k: [v, b["triple_counts"][k]] for k, v in a["triple_counts"].items()
               if v != b["triple_counts"][k]}
    n = a["n_objects"]
    regrets = [[Fraction(c - world["total_leaf_depth_optimal"], n)
                for c in world["first_question_total_costs"]] for world in (a, b)]
    deterministic_minimax = min(max(regrets[0][j], regrets[1][j]) for j in range(M))
    mix_cost = [Fraction(w["first_question_total_costs"][1] + w["first_question_total_costs"][2], 2 * n)
                for w in (a, b)]
    mix_regret = [c - Fraction(w["total_leaf_depth_optimal"], n) for c, w in zip(mix_cost, (a, b))]
    assert deterministic_minimax == Fraction(1, 14)
    assert mix_regret == [Fraction(1, 28), Fraction(1, 28)]
    out = {
        "scope": "One constructed witness; not a sampled experiment or a novelty claim.",
        "assumptions": ["uniform target", "unit question cost", "noiseless answers",
                        "fixed binary questions", "adaptive identification of a unique object"],
        "A": a, "B": b,
        "checks": {"same_gram": True, "same_row_degrees": True,
                   "disjoint_optimal_first_question_sets": True,
                   "optimal_trees_replayed_for_all_objects": True,
                   "simple_6cycles_counted_two_ways": True},
        "changed_triple_counts": changed,
        "pair_stat_only_root_policy_regret_bounds": {
            "deterministic_worst_case": "1/14",
            "randomized_worst_case": "1/28",
            "attaining_randomized_policy": {"Q2": "1/2", "Q3": "1/2"},
            "continuation": "Oracle-optimal continuation after the first question.",
            "per_question_regret_A_exact": list(map(str, regrets[0])),
            "per_question_regret_B_exact": list(map(str, regrets[1])),
            "deterministic_minimax_regret_verified": str(deterministic_minimax),
            "q2_q3_mixture_mean_costs_exact": list(map(str, mix_cost)),
            "q2_q3_mixture_regrets_exact": list(map(str, mix_regret)),
            "randomized_lower_bound_proof": "Let p be the probability of Q2. A-regret is at least (1-p)/14 and B-regret at least p/14, so max regret is at least 1/28."
        }
    }
    args.output.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output.resolve()),
                      "A": {k: a[k] for k in ("mean_optimal_exact", "optimal_first_questions", "mean_greedy_id_ties_exact", "greedy_regret_exact", "mean_greedy_uniform_ties_exact", "greedy_uniform_ties_regret_exact", "simple_4cycles", "simple_6cycles")},
                      "B": {k: b[k] for k in ("mean_optimal_exact", "optimal_first_questions", "mean_greedy_id_ties_exact", "greedy_regret_exact", "mean_greedy_uniform_ties_exact", "greedy_uniform_ties_regret_exact", "simple_4cycles", "simple_6cycles")},
                      "q2_q3_mixture_costs": list(map(str, mix_cost)),
                      "q2_q3_mixture_regrets": list(map(str, mix_regret)),
                      "changed_triples": changed}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
