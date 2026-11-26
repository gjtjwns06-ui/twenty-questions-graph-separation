"""Exact Gram-isomorphism grouping. WL is a bucket, never a proof of equality."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import networkx as nx
from .core import gram_of
from .io import read_jsonl, write_json, digest, now


def gram_graph(rows, m):
    gram = gram_of(rows, m)
    graph = nx.Graph()
    for j in range(m):
        graph.add_node(j, degree=str(gram[j][j]))
    for j in range(m):
        for k in range(j + 1, m):
            graph.add_edge(j, k, weight=str(gram[j][k]))
    return graph


def iso(a, b):
    return nx.is_isomorphic(a, b, node_match=nx.algorithms.isomorphism.categorical_node_match("degree", ""),
                           edge_match=nx.algorithms.isomorphism.categorical_edge_match("weight", ""))


def bucket(graph):
    return nx.weisfeiler_lehman_graph_hash(graph, node_attr="degree", edge_attr="weight", iterations=4)


def assign_splits(out, config):
    out = Path(out)
    if (out / "splits.json").exists():
        raise FileExistsError("Splits are immutable; choose a new run directory.")
    parents = read_jsonl(out / "parents.jsonl")
    bins = defaultdict(list)
    groups, assignments = [], {}
    for parent in parents:
        graph = gram_graph(parent["rows"], parent["m"])
        key = (parent["n"], parent["m"], bucket(graph))
        match = next((g for g in bins[key] if iso(graph, g["graph"])), None)
        if match is None:
            match = dict(group_id=f"gram-{len(groups):06d}", graph=graph, parents=[],
                         cohorts=set(), n=parent["n"], m=parent["m"], pilot_overlap=False)
            bins[key].append(match)
            groups.append(match)
        match["parents"].append(parent["parent_id"])
        match["cohorts"].add(parent["cohort"])
    pilot_graphs = defaultdict(list)
    for folder in config.get("pilot_directories", []):
        for parent in read_jsonl(Path(folder) / "parents.jsonl"):
            graph = gram_graph(parent["rows"], parent["m"])
            pilot_graphs[(parent["n"], parent["m"], bucket(graph))].append(graph)
    if config.get("reserved_witness"):
        witness = json.loads(Path(config["reserved_witness"]).read_text(encoding="utf-8"))
        for label in ("A", "B"):
            world = witness[label]
            rows = [tuple(int(q) - 1 for q in row) for row in world["rows"]]
            graph = gram_graph(rows, world["n_questions"])
            pilot_graphs[(world["n_objects"], world["n_questions"], bucket(graph))].append(graph)
    strata = defaultdict(list)
    for group in groups:
        key = (group["n"], group["m"], bucket(group["graph"]))
        group["pilot_overlap"] = any(iso(group["graph"], g) for g in pilot_graphs[key])
        if len(group["cohorts"]) > 1 or group["pilot_overlap"]:
            group["split"] = "excluded_overlap"
        elif group["cohorts"] == {"id"}:
            strata[(group["n"], group["m"])].append(group)
        else:
            cohort = next(iter(group["cohorts"]))
            group["split"] = "test_" + cohort
    for groups_in_stratum in strata.values():
        ordered = sorted(groups_in_stratum, key=lambda g: hashlib.sha256(
            f'{config["split_seed"]}|{min(g["parents"])}'.encode()).hexdigest())
        train_end = int(len(ordered) * config["train_fraction"])
        valid_end = train_end + int(len(ordered) * config["validation_fraction"])
        for i, group in enumerate(ordered):
            group["split"] = "train" if i < train_end else "validation" if i < valid_end else "test"
    for group in groups:
        for parent_id in group["parents"]:
            assignments[parent_id] = dict(split=group["split"], gram_group=group["group_id"])
    metadata = [{key: sorted(value) if isinstance(value, set) else value
                 for key, value in group.items() if key != "graph"} for group in groups]
    result = dict(created=now(), config_sha256=digest(out / "config.json"),
                  rule="Exact weighted Gram graph isomorphism after WL bucketing; group before splitting.",
                  parents=assignments, groups=metadata,
                  pilot_gram_overlaps=sum(g["pilot_overlap"] for g in groups),
                  cross_split_gram_duplicates=0,
                  full_bipartite_iso_leakage="Impossible across distinct exact Gram groups; iso M implies iso Gram.")
    write_json(out / "splits.json", result)
    print(json.dumps(dict(split_parent_counts={s: sum(x["split"] == s for x in assignments.values())
        for s in sorted({x["split"] for x in assignments.values()})}, gram_groups=len(groups))), flush=True)
