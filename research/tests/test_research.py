import itertools
import random
import unittest
import tempfile
from pathlib import Path
from fractions import Fraction
import numpy as np

from tq.core import (ExactSolver, Lookahead, generate_parent, find_trades,
                     apply_trade, control_check, baseline_evaluation)
from tq.features import make_features, flatten
from verify_witness import ROWS_A, ROWS_B


def witness_rows(strings):
    return [tuple(int(q) - 1 for q in row) for row in strings]


def exhaustive(rows, m):
    cols = [sum(1 << i for i, row in enumerate(rows) if q in row) for q in range(m)]
    costs = [0] * (1 << len(rows))
    for mask in range(1, len(costs)):
        if mask.bit_count() > 1:
            costs[mask] = mask.bit_count() + min(costs[mask & col] + costs[mask ^ (mask & col)]
                for col in cols if mask & col and mask & col != mask)
    full = len(costs) - 1
    first = [len(rows) + costs[col] + costs[full ^ col] if col and col != full else None for col in cols]
    return costs[-1], first


class ResearchTests(unittest.TestCase):
    def test_witness_and_uniform_policy(self):
        for strings, total, first, mean in [
            (ROWS_A, 54, [55, 54, 55, 58, 55, 55, 56, 57], Fraction(659, 168)),
            (ROWS_B, 55, [56, 56, 55, 58, 55, 55, 56, 57], Fraction(111, 28))]:
            solver = ExactSolver(witness_rows(strings), 8)
            result = solver.solve()
            self.assertEqual(result["optimal_total"], total)
            self.assertEqual(result["first_totals"], first)
            baseline = baseline_evaluation(solver, result)
            self.assertEqual(Fraction(baseline["information_gain"]["policy_mean_exact"]), mean)

    def test_independent_exhaustive_solver(self):
        for seed in range(8):
            rows = generate_parent(9, 6, "natural", random.Random(seed))
            expected, first = exhaustive(rows, 6)
            result = ExactSolver(rows, 6).solve()
            self.assertEqual(result["optimal_total"], expected)
            self.assertEqual(result["first_totals"], first)

    def test_trade_enumerator_against_bruteforce(self):
        rows = generate_parent(13, 7, "natural", random.Random(4))
        brute = set()
        for four in itertools.combinations(rows, 4):
            counts = {q: sum(q in row for row in four) for q in set().union(*map(set, four))}
            if len(counts) == 6 and set(counts.values()) == {2} and all(
                    len(set(a) & set(b)) == 1 for a, b in itertools.combinations(four, 2)):
                brute.add(tuple(sorted(four)))
        trades = find_trades(rows)
        self.assertEqual(brute, {tuple(t["removed"]) for t in trades})
        for trade in trades:
            if trade["valid"]:
                changed, _ = apply_trade(rows, trade)
                self.assertTrue(control_check(rows, changed, 7)["same_gram"])

    def test_information_invariants_and_renaming(self):
        rows, changed = witness_rows(ROWS_A), witness_rows(ROWS_B)
        a, b = make_features(rows, 8), make_features(changed, 8)
        for x, y in zip(a, b):
            self.assertEqual(x["base"], y["base"])
            self.assertAlmostEqual(x["search"]["H2"], y["search"]["H2"], places=12)
        self.assertTrue(any(x["conditional"] != y["conditional"] for x, y in zip(a, b)))
        permutation = random.Random(71).sample(range(8), 8)
        permuted = [tuple(sorted(permutation[q] for q in row)) for row in reversed(rows)]
        features = {x["question"]: x for x in make_features(permuted, 8)}
        for original in a:
            np.testing.assert_allclose(list(flatten(original, "all").values()),
                list(flatten(features[permutation[original["question"]]], "all").values()), atol=1e-10)

    def test_limits_do_not_emit_approximate_labels(self):
        result = ExactSolver(witness_rows(ROWS_A), 8, seconds=-1).solve()
        self.assertEqual(result["status"], "time_limit")
        self.assertIsNone(result["optimal_total"])
        self.assertIsNone(result["first_totals"])

    def test_exact_gram_grouping_under_question_permutation(self):
        from tq.io import append_jsonl, write_json
        from tq.splits import assign_splits
        rows = witness_rows(ROWS_A)
        permutation = [6, 3, 4, 1, 7, 2, 0, 5]
        renamed = [tuple(sorted(permutation[q] for q in row)) for row in reversed(rows)]
        with tempfile.TemporaryDirectory() as folder:
            dest = Path(folder)
            write_json(dest / "config.json", {})
            for i, r in enumerate([rows, renamed, witness_rows(ROWS_B)]):
                append_jsonl(dest / "parents.jsonl", dict(parent_id=str(i), rows=r, m=8, n=14, cohort="id"))
            assign_splits(dest, dict(split_seed=7, train_fraction=.6, validation_fraction=.2))
            import json
            assignments = json.loads((dest / "splits.json").read_text())["parents"]
            self.assertEqual(assignments["0"], assignments["1"])
            self.assertEqual(assignments["0"], assignments["2"])

    def test_weighted_scaler_constant_columns_and_parent_weights(self):
        from tq.models import WeightedStandardScaler
        x = np.array([[.3, 1.], [.3, 3.], [.3, 5.]])
        weights = np.array([1., 2., 4.])
        scaler = WeightedStandardScaler().fit(x, sample_weight=weights)
        z = scaler.transform(x)
        self.assertTrue(np.all(np.isfinite(z)))
        np.testing.assert_allclose(np.average(z, axis=0, weights=weights), [0, 0], atol=1e-12)


if __name__ == "__main__":
    unittest.main()
