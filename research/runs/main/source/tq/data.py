from __future__ import annotations
import gc
import json
from pathlib import Path
import random
import time

from .core import generate_parent, find_trades, apply_trade, control_check, ExactSolver, baseline_evaluation
from .features import make_features
from .io import Profile, write_json, append_jsonl, now, digest


def run_dataset(config, out, *, audit_all_trades=False):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    write_json(out / "config.json", config)
    summary = dict(started=now(), parents=0, parents_with_valid_trade=0, candidates=0,
                   valid_candidates=0, worlds=0, completed_worlds=0, pairs=0, completed_pairs=0)
    with Profile() as run_profile:
        for cell_index, cell in enumerate(config["cells"]):
            for index in range(cell["parents"]):
                seed = config["seed"] + cell_index * 1000003 + index * 1009
                parent_id = f'{config["name"]}-c{cell_index:02d}-p{index:05d}'
                rng = random.Random(seed)
                parent = dict(parent_id=parent_id, seed=seed, cell=cell_index,
                              family=cell["family"], n=cell["n"], m=cell["m"],
                              cohort=cell.get("cohort", "id"), created=now())
                with Profile() as generation:
                    rows = generate_parent(cell["n"], cell["m"], cell["family"], rng)
                    trades = find_trades(rows)
                valid = [t for t in trades if t["valid"]]
                selected = rng.sample(valid, min(config.get("trades_per_parent", 1), len(valid)))
                parent.update(rows=rows, candidate_count=len(trades), valid_candidate_count=len(valid),
                              invalid_duplicate_count=len(trades) - len(valid),
                              selected_count=len(selected), generation_profile=generation.result,
                              status="paired" if selected else "no_valid_trade")
                summary["parents"] += 1
                summary["candidates"] += len(trades)
                summary["valid_candidates"] += len(valid)
                summary["parents_with_valid_trade"] += bool(selected)
                if audit_all_trades:
                    parent["all_trade_candidates"] = trades
                append_jsonl(out / "parents.jsonl", parent)
                # Unpaired parents remain in the raw denominator; not labeled or resampled.
                if not selected:
                    continue
                worlds = [(parent_id + "-original", rows, None)]
                pair_records = []
                for k, trade in enumerate(selected):
                    changed, history = apply_trade(rows, trade)
                    checks = control_check(rows, changed, cell["m"])
                    world_id = f"{parent_id}-trade{k}"
                    worlds.append((world_id, changed, history))
                    pair_records.append(dict(parent_id=parent_id, pair_id=f"{parent_id}-pair{k}",
                                             a=worlds[0][0], b=world_id, checks=checks,
                                             trade_history=[history], family=cell["family"],
                                             cohort=parent["cohort"], n=cell["n"], m=cell["m"]))
                exact_by_id = {}
                for world_id, world_rows, history in worlds:
                    with Profile() as solve_profile:
                        solver = ExactSolver(world_rows, cell["m"], **config["solver"])
                        exact = solver.solve()
                    record = dict(world_id=world_id, parent_id=parent_id, family=cell["family"],
                                  cohort=parent["cohort"], n=cell["n"], m=cell["m"], seed=seed,
                                  rows=world_rows, matrix=[[int(q in row) for q in range(cell["m"])]
                                                          for row in world_rows],
                                  history=[] if history is None else [history], exact=exact,
                                  solver_profile=solve_profile.result)
                    exact_by_id[world_id] = exact
                    summary["worlds"] += 1
                    if exact["status"] == "complete":
                        summary["completed_worlds"] += 1
                        if config.get("baselines", True):
                            with Profile() as policy_profile:
                                record["baselines"] = baseline_evaluation(solver, exact, config.get("tie_tolerance", 1e-10))
                            record["baseline_profile"] = policy_profile.result
                        if config.get("features", True):
                            with Profile() as feature_profile:
                                features = make_features(world_rows, cell["m"])
                            record["feature_profile"] = feature_profile.result
                            for feature in features:
                                q = feature["question"]
                                append_jsonl(out / "features.jsonl", dict(world_id=world_id, parent_id=parent_id,
                                    feature=feature, target=(exact["first_totals"][q] - exact["optimal_total"]) / cell["n"]))
                    append_jsonl(out / "worlds.jsonl", record)
                    del solver
                for pair in pair_records:
                    a, b = exact_by_id[pair["a"]], exact_by_id[pair["b"]]
                    pair["complete"] = a["status"] == b["status"] == "complete"
                    if pair["complete"]:
                        pair.update(delta_optimal=(b["optimal_total"] - a["optimal_total"]) / cell["n"],
                                    abs_delta_optimal=abs(b["optimal_total"] - a["optimal_total"]) / cell["n"],
                                    argmin_changed=set(a["argmin"]) != set(b["argmin"]),
                                    argmin_disjoint=not bool(set(a["argmin"]) & set(b["argmin"])))
                        summary["completed_pairs"] += 1
                    summary["pairs"] += 1
                    append_jsonl(out / "pairs.jsonl", pair)
                gc.collect()
                if (index + 1) % 10 == 0 or index == cell["parents"] - 1:
                    print(json.dumps(dict(cell=cell_index, finished=index + 1, **summary)), flush=True)
    summary.update(finished=now(), profile=run_profile.result)
    write_json(out / "summary.json", summary)
    write_json(out / "manifest.json", {p.name: digest(p) for p in sorted(out.glob("*.json*"))
                                       if p.name != "manifest.json"})
    return summary
