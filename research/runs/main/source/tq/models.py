from __future__ import annotations
from collections import defaultdict
import csv
import json
from pathlib import Path
import time
import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.base import BaseEstimator, TransformerMixin

from .core import tied_min
from .features import flatten, BLOCKS
from .io import read_jsonl, write_json, append_jsonl, Profile, digest, now


class WeightedStandardScaler(TransformerMixin, BaseEstimator):
    """Stable two-pass weighted population scaling, constant columns kept safe."""
    def fit(self, x, y=None, sample_weight=None):
        self.mean_ = np.average(x, axis=0, weights=sample_weight)
        variance = np.average((x - self.mean_) ** 2, axis=0, weights=sample_weight)
        self.scale_ = np.sqrt(np.maximum(variance, 0))
        self.scale_[self.scale_ <= 1e-10] = 1.0
        return self

    def transform(self, x):
        return (x - self.mean_) / self.scale_


def world_metric(world, scores, tolerance):
    questions = tied_min(scores, tolerance)
    exact = world["exact"]
    regret = np.mean([(exact["first_totals"][q] - exact["optimal_total"]) / world["n"] for q in questions])
    hit = len(set(questions) & set(exact["argmin"])) / len(questions)
    return dict(root_questions=questions, first_regret=float(regret), optimal_probability=hit)


def parent_mean(records, field="first_regret"):
    parents = defaultdict(list)
    for r in records:
        parents[r["parent_id"]].append(r[field])
    return float(np.mean([np.mean(v) for v in parents.values()])) if parents else None


def make_model(family, parameters, seed):
    if family == "ridge":
        return make_pipeline(WeightedStandardScaler(), Ridge(alpha=parameters["alpha"]))
    return HistGradientBoostingRegressor(random_state=seed, early_stopping=False,
        learning_rate=.05, max_iter=parameters["max_iter"],
        max_leaf_nodes=parameters["max_leaf_nodes"], l2_regularization=1.0)


def fit_model(model, family, x, y, weights):
    if family == "ridge":
        model.fit(x, y, weightedstandardscaler__sample_weight=weights, ridge__sample_weight=weights)
    else:
        model.fit(x, y, sample_weight=weights)


def compare(out, config):
    out = Path(out)
    destination = out / "comparison"
    destination.mkdir(exist_ok=False)
    write_json(destination / "environment.json", __import__("tq.io", fromlist=["environment"]).environment())
    split = json.loads((out / "splits.json").read_text(encoding="utf-8"))["parents"]
    worlds = {w["world_id"]: w for w in read_jsonl(out / "worlds.jsonl") if w["exact"]["status"] == "complete"}
    features = read_jsonl(out / "features.jsonl")
    by_world = defaultdict(list)
    for r in features:
        by_world[r["world_id"]].append(r)
    training = [r for r in features if split[r["parent_id"]]["split"] == "train"]
    validation_ids = [wid for wid, w in worlds.items() if split[w["parent_id"]]["split"] == "validation"]
    assert training and validation_ids
    world_counts = defaultdict(set)
    for r in training:
        world_counts[r["parent_id"]].add(r["world_id"])
    weights = np.array([1 / (len(world_counts[r["parent_id"]]) * len(by_world[r["world_id"]])) for r in training])
    weights /= weights.mean()
    y = np.array([r["target"] for r in training])
    seed0 = config["model_seeds"][0]
    candidates, winners = [], []
    with Profile() as training_profile:
        for block in BLOCKS:
            names = list(flatten(training[0]["feature"], block))
            x = np.array([list(flatten(r["feature"], block).values()) for r in training])
            xv = {wid: np.array([list(flatten(r["feature"], block).values()) for r in by_world[wid]])
                  for wid in validation_ids}
            for family in ("ridge", "boosting"):
                options = config["model_grid"][family]
                scored = []
                for i, parameters in enumerate(options):
                    model = make_model(family, parameters, seed0)
                    start = time.perf_counter()
                    fit_model(model, family, x, y, weights)
                    fit_seconds = time.perf_counter() - start
                    records = []
                    for wid in validation_ids:
                        prediction = model.predict(xv[wid])
                        scores = {r["feature"]["question"]: float(v) for r, v in zip(by_world[wid], prediction)}
                        metric = world_metric(worlds[wid], scores, config["tie_tolerance"])
                        records.append(dict(parent_id=worlds[wid]["parent_id"], world_id=wid, **metric))
                    loss = parent_mean(records)
                    candidate = dict(block=block, family=family, parameters=parameters,
                                     grid_index=i, validation_parent_regret=loss, fit_seconds=fit_seconds,
                                     validation_optimal_probability=parent_mean(records, "optimal_probability"))
                    candidates.append(candidate)
                    scored.append((loss, i, candidate, model))
                    append_jsonl(destination / "validation_candidates.jsonl", candidate)
                # A fixed complexity/order rule resolves metric ties. Test labels are unused.
                best_loss = min(z[0] for z in scored)
                chosen = next(z for z in scored if z[0] <= best_loss + config["selection_tolerance"])
                candidate, model = chosen[2], chosen[3]
                model_id = f"{family}_{block}"
                winner = dict(candidate, model_id=model_id, feature_names=names)
                winners.append(winner)
                joblib.dump(model, destination / f"{model_id}-seed{seed0}.joblib")
                print(json.dumps(dict(selected=model_id, validation_regret=best_loss)), flush=True)
    best_loss = min(w["validation_parent_regret"] for w in winners)
    primary = next(w for w in winners if w["validation_parent_regret"] <= best_loss + config["selection_tolerance"])
    # This receipt is written BEFORE accessing test metrics or predictions.
    selection = dict(frozen=now(), primary_model=primary["model_id"], winners=winners,
                     criterion="Validation mean first regret, equal weight per independent parent.",
                     tie_rule="Predeclared block order, ridge before boosting, grid order.",
                     training_profile=training_profile.result,
                     splits_sha256=digest(out / "splits.json"), config_sha256=digest(out / "config.json"))
    write_json(destination / "selection.json", selection)
    for winner in winners:
        block, family = winner["block"], winner["family"]
        x = np.array([list(flatten(r["feature"], block).values()) for r in training])
        for seed in config["model_seeds"]:
            path = destination / f'{winner["model_id"]}-seed{seed}.joblib'
            if seed == seed0:
                model = joblib.load(path)
                fit_seconds = winner["fit_seconds"]
            else:
                model = make_model(family, winner["parameters"], seed)
                start = time.perf_counter()
                fit_model(model, family, x, y, weights)
                fit_seconds = time.perf_counter() - start
                joblib.dump(model, path)
            for wid, world in worlds.items():
                partition = split[world["parent_id"]]["split"]
                if not (partition.startswith("test") or partition == "validation"):
                    continue
                start = time.perf_counter()
                features_x = np.array([list(flatten(r["feature"], block).values()) for r in by_world[wid]])
                prediction = model.predict(features_x)
                infer_seconds = time.perf_counter() - start
                scores = {r["feature"]["question"]: float(v) for r, v in zip(by_world[wid], prediction)}
                metric = world_metric(world, scores, config["tie_tolerance"])
                append_jsonl(destination / "predictions.jsonl", dict(world_id=wid, parent_id=world["parent_id"],
                    split=partition, model=winner["model_id"], seed=seed, **metric,
                    predicted_regrets=scores, inference_seconds=infer_seconds,
                    feature_seconds=world["feature_profile"]["seconds"],
                    root_seconds_with_features=infer_seconds + world["feature_profile"]["seconds"],
                    fit_seconds=fit_seconds))
    write_json(destination / "status.json", dict(completed=now(), primary_model=primary["model_id"],
        full_ml_policy="Not evaluated: models trained on initial states only.",
        training_rows=len(training), training_parents=len(world_counts),
        model_files_sha256={p.name: digest(p) for p in sorted(destination.glob("*.joblib"))}))
