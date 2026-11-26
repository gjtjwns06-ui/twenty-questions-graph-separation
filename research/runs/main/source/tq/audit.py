from collections import defaultdict
import json
from pathlib import Path
import random
import numpy as np
import joblib
from .core import control_check, ExactSolver
from .features import make_features, flatten
from .io import read_jsonl, write_json, now, digest
from .splits import gram_graph, bucket, iso


def audit_run(out):
    out = Path(out)
    worlds = read_jsonl(out / "worlds.jsonl")
    by_id = {w["world_id"]: w for w in worlds}
    parents = read_jsonl(out / "parents.jsonl")
    pairs = read_jsonl(out / "pairs.jsonl")
    split_data = json.loads((out / "splits.json").read_text(encoding="utf-8"))
    splits = split_data["parents"]
    for pair in pairs:
        a, b = by_id[pair["a"]], by_id[pair["b"]]
        recomputed = control_check(a["rows"], b["rows"], a["m"])
        assert recomputed == pair["checks"]
        assert a["parent_id"] == b["parent_id"] == pair["parent_id"]
        assert splits[a["parent_id"]] == splits[b["parent_id"]]
        reconstructed = [list(row) for row in a["rows"]]
        for event in pair["trade_history"]:
            for replacement in event["row_replacements"]:
                index = replacement["index"]
                assert reconstructed[index] == replacement["before"]
                reconstructed[index] = replacement["after"]
        assert reconstructed == b["rows"]
    complete = [w for w in worlds if w["exact"]["status"] == "complete"]
    for world in complete:
        exact = world["exact"]
        assert sum(exact["replay_depths"]) == exact["optimal_total"]
        assert min(x for x in exact["first_totals"] if x is not None) == exact["optimal_total"]
        for i, row in enumerate(world["rows"]):
            tree = exact["optimal_tree"]
            depth = 0
            while "question" in tree:
                tree = tree["yes"] if tree["question"] in row else tree["no"]
                depth += 1
            assert tree["object"] == i and depth == exact["replay_depths"][i]
    for world in worlds:
        if world["exact"]["status"] != "complete":
            assert world["exact"]["optimal_total"] is None
            assert world["exact"]["first_totals"] is None
    # Independent repeat of exact grouping across all generated parents.
    buckets = defaultdict(list)
    compared = 0
    for parent in parents:
        graph = gram_graph(parent["rows"], parent["m"])
        key = (parent["n"], parent["m"], bucket(graph))
        for previous, old_graph in buckets[key]:
            if iso(graph, old_graph):
                compared += 1
                assert splits[parent["parent_id"]]["gram_group"] == splits[previous["parent_id"]]["gram_group"]
                assert splits[parent["parent_id"]]["split"] == splits[previous["parent_id"]]["split"]
        buckets[key].append((parent, graph))
    # One deterministic audit sample per n,m,family, chosen without outcome filtering.
    strata = defaultdict(list)
    for world in complete:
        strata[(world["n"], world["m"], world["family"])].append(world)
    rename_audits = []
    comparison = out / "comparison" / "selection.json"
    selected = json.loads(comparison.read_text(encoding="utf-8")) if comparison.exists() else None
    config = json.loads((out / "config.json").read_text(encoding="utf-8"))
    for (n, m, family), sample in sorted(strata.items()):
        world = sorted(sample, key=lambda w: w["world_id"])[0]
        rng = random.Random(919 + n + m)
        permutation = rng.sample(range(m), m)
        renamed = [tuple(sorted(permutation[q] for q in row)) for row in reversed(world["rows"])]
        exact = ExactSolver(renamed, m, **config["solver"]).solve()
        assert exact["status"] == "complete"
        assert exact["optimal_total"] == world["exact"]["optimal_total"]
        assert set(exact["argmin"]) == {permutation[q] for q in world["exact"]["argmin"]}
        a = make_features(world["rows"], m)
        b = {r["question"]: r for r in make_features(renamed, m)}
        for original in a:
            np.testing.assert_allclose(list(flatten(original, "all").values()),
                list(flatten(b[permutation[original["question"]]], "all").values()), atol=2e-10, rtol=0)
        if selected:
            for winner in selected["winners"]:
                model = joblib.load(out / "comparison" / f'{winner["model_id"]}-seed{config["model_seeds"][0]}.joblib')
                xa = np.array([list(flatten(f, winner["block"]).values()) for f in a])
                xb = np.array([list(flatten(b[permutation[f["question"]]], winner["block"]).values()) for f in a])
                np.testing.assert_allclose(model.predict(xa), model.predict(xb), atol=1e-9, rtol=0)
        rename_audits.append(dict(n=n, m=m, family=family, world_id=world["world_id"], passed=True))
    features = read_jsonl(out / "features.jsonl")
    per_world = defaultdict(dict)
    for row in features:
        world = by_id[row["world_id"]]
        q = row["feature"]["question"]
        assert row["target"] == (world["exact"]["first_totals"][q] - world["exact"]["optimal_total"]) / world["n"]
        assert not any("optimal" in key or "target" in key for key in flatten(row["feature"], "all"))
        per_world[row["world_id"]][q] = row["feature"]
    for pair in pairs:
        if pair["complete"]:
            for q, a in per_world[pair["a"]].items():
                b = per_world[pair["b"]][q]
                assert a["base"] == b["base"]
                assert abs(a["search"]["H2"] - b["search"]["H2"]) <= 1e-10
    write_json(out / "audit.json", dict(completed=now(), passed=True, pairs_checked=len(pairs),
        optimal_trees_replayed=len(complete), feature_labels_checked=len(features),
        iso_duplicate_parent_pairs=compared, rename_audits=rename_audits,
        incomplete_world_labels_absent=True, pairwise_features_identical=True,
        cross_split_gram_duplicates=0, exact_H2_invariance=True,
        full_bipartite_iso_scope="No cross-split duplicates possible because Gram isomorphism is grouped exactly."))
    print(json.dumps(dict(audit="passed", pairs=len(pairs), trees=len(complete), feature_labels=len(features))), flush=True)
