#!/usr/bin/env python3
"""Guided extremal search in invariant-preserving Pasch components.

The old main experiment, its code, splits and outcomes are never overwritten.
"""
from __future__ import annotations
from collections import deque, defaultdict
from fractions import Fraction
from functools import lru_cache
import argparse
import hashlib
import heapq
import json
from pathlib import Path
import time
import gc

from tq.core import ExactSolver, apply_trade, find_trades, control_check, gram_of
from tq.io import Profile, append_jsonl, read_jsonl, write_json, digest, now, environment


def canonical(rows):
    return tuple(sorted(tuple(sorted(row)) for row in rows))


def graph_id(rows, m):
    return hashlib.sha256(json.dumps([m, canonical(rows)]).encode()).hexdigest()[:20]


class GreedyCosts:
    """Actual completion costs: uniform, best, and worst greedy tie trees."""
    def __init__(self, columns):
        self.columns = columns
        self.cost = lru_cache(None)(self._cost)

    def choices(self, mask):
        size = mask.bit_count()
        candidates = [(abs(size - 2 * a.bit_count()), q, a, mask ^ a)
                      for q, col in enumerate(self.columns) if (a := mask & col) and a != mask]
        best = min(c[0] for c in candidates)
        return [(q, a, b) for imbalance, q, a, b in candidates if imbalance == best]

    def _cost(self, mask):
        size = mask.bit_count()
        if size <= 1:
            return Fraction(0), 0, 0
        options = []
        for q, a, b in self.choices(mask):
            x, y = self.cost(a), self.cost(b)
            options.append((x[0] + y[0], x[1] + y[1], x[2] + y[2]))
        return (size + sum((x[0] for x in options), Fraction(0)) / len(options),
                size + min(x[1] for x in options), size + max(x[2] for x in options))


def evaluate(rows, m, limits):
    rows = canonical(rows)
    with Profile() as profile:
        solver = ExactSolver(rows, m, **limits)
        exact = solver.solve()
        result = dict(node_id=graph_id(rows, m), rows=rows, n=len(rows), m=m, exact=exact)
        if exact["status"] == "complete":
            greedy = GreedyCosts(solver.columns)
            uniform, low, high = greedy.cost(solver.full)
            n, opt = solver.n, exact["optimal_total"]
            gap = (uniform - opt) / n
            result["greedy"] = dict(total_uniform_exact=str(uniform), mean_uniform_exact=str(uniform / n),
                mean_uniform=float(uniform / n), total_min_ties=low, total_max_ties=high,
                gap_exact=str(gap), gap=float(gap),
                min_tie_gap_exact=str(Fraction(low - opt, n)), min_tie_gap=(low - opt) / n,
                max_tie_gap_exact=str(Fraction(high - opt, n)), max_tie_gap=(high - opt) / n,
                approximation_ratio_exact=str(uniform / opt), approximation_ratio=float(uniform / opt),
                root_questions=[q for q, _, _ in greedy.choices(solver.full)],
                root_oracle_regret_min_exact=str(min(Fraction(exact["first_totals"][q] - opt, n)
                    for q, _, _ in greedy.choices(solver.full))))
    result["profile"] = profile.result
    return result


def select_seeds(config):
    source = Path(config["source_run"])
    worlds = {w["world_id"]: w for w in read_jsonl(source / "worlds.jsonl")}
    pairs = read_jsonl(source / "pairs.jsonl")
    ranked = defaultdict(list)
    for pair in pairs:
        if not pair["complete"] or pair["n"] not in config["sizes"]:
            continue
        a, b = worlds[pair["a"]], worlds[pair["b"]]
        def regret(w):
            return Fraction(w["baselines"]["information_gain"]["policy_mean_exact"]) - Fraction(w["exact"]["optimal_total"], w["n"])
        contrast = abs(regret(a) - regret(b))
        ranked[pair["n"]].append((contrast, max(regret(a), regret(b)), pair["pair_id"], a, b))
    seeds = []
    seen = set()
    for size in config["sizes"]:
        taken = 0
        for contrast, gap, pair_id, a, b in sorted(ranked[size], key=lambda x: (-x[0], -x[1], x[2])):
            key = json.dumps(gram_of(a["rows"], a["m"]))
            if key in seen:
                continue
            seen.add(key)
            seeds.append(dict(source=pair_id, n=size, m=a["m"], rows=a["rows"], companion=b["rows"],
                              source_contrast_exact=str(contrast)))
            taken += 1
            if taken == config["fibers_per_size"]:
                break
    from verify_witness import ROWS_A, ROWS_B
    convert = lambda rows: [[int(q) - 1 for q in row] for row in rows]
    seeds.append(dict(source="paper_witness", n=14, m=8, rows=convert(ROWS_A), companion=convert(ROWS_B)))
    return seeds


def search(config_path, out):
    config_path, out = Path(config_path), Path(out)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    out.mkdir(parents=True, exist_ok=False)
    seeds = select_seeds(config)
    write_json(out / "seeds.json", seeds)
    write_json(out / "config.json", config)
    write_json(out / "environment.json", environment())
    receipt = dict(frozen=now(), config_sha256=digest(config_path),
        sources={str(p): digest(p) for p in [Path(__file__), Path("tq/core.py"), Path("tq/io.py")]},
        original_main_manifest_sha256=digest(Path(config["source_run"]) / "ARTIFACT_MANIFEST.json"),
        seed_count=len(seeds), interpretation="Adaptive extrema; not an independent prevalence evaluation")
    write_json(out / "frozen.json", receipt)
    start = time.perf_counter()
    total_nodes = 0
    summaries = []
    with Profile() as full_profile:
        for index, seed in enumerate(seeds):
            if time.perf_counter() - start > config["max_seconds"]:
                break
            fiber_id = f"fiber-{index:02d}"
            m = seed["m"]
            seen, records = set(), {}
            high, low, fifo = [], [], deque()
            expanded = set()
            edges, round_number = 0, 0
            origin_gram = gram_of(seed["rows"], m)

            def add(rows, predecessor=None, history=None):
                nonlocal total_nodes
                rows = canonical(rows)
                node_id = graph_id(rows, m)
                if node_id in seen:
                    return node_id
                if total_nodes >= config["max_total_unique_nodes"] or len(seen) >= config["max_unique_nodes_per_fiber"]:
                    return None
                seen.add(node_id)
                total_nodes += 1
                record = evaluate(rows, m, config["solver"])
                assert gram_of(rows, m) == origin_gram
                record.update(fiber_id=fiber_id, predecessor=predecessor, trade=history,
                              row_canonicalization="Sort rows after every move; all row degrees remain 3")
                records[node_id] = record
                append_jsonl(out / "nodes.jsonl", record)
                if record["exact"]["status"] == "complete":
                    gap = record["greedy"]["gap"]
                    heapq.heappush(high, (-gap, node_id))
                    heapq.heappush(low, (gap, node_id))
                    fifo.append(node_id)
                return node_id

            add(seed["rows"])
            # The measured companion is an initial node in the same indexed fiber.
            add(seed["companion"])
            stop_reason = "component_exhausted"
            while True:
                if time.perf_counter() - start > config["max_seconds"]:
                    stop_reason = "global_time_budget"
                    break
                if total_nodes >= config["max_total_unique_nodes"]:
                    stop_reason = "global_node_budget"
                    break
                if len(seen) >= config["max_unique_nodes_per_fiber"]:
                    stop_reason = "fiber_node_budget"
                    break
                mode = round_number % 4
                round_number += 1
                frontier = high if mode in (0, 1) else low if mode == 2 else fifo
                current = None
                while frontier:
                    candidate = frontier.popleft() if mode == 3 else heapq.heappop(frontier)[1]
                    if candidate not in expanded:
                        current = candidate
                        break
                if current is None:
                    for candidate in fifo:
                        if candidate not in expanded:
                            current = candidate
                            break
                if current is None:
                    break
                expanded.add(current)
                rows = canonical(records[current]["rows"])
                for trade in find_trades(rows):
                    if not trade["valid"]:
                        continue
                    changed, history = apply_trade(rows, trade)
                    checks = control_check(rows, changed, m)
                    new_id = graph_id(changed, m)
                    append_jsonl(out / "edges.jsonl", dict(fiber_id=fiber_id, before=current, after=new_id,
                        history=history, checks=checks))
                    edges += 1
                    add(changed, current, history)
                    if (len(seen) >= config["max_unique_nodes_per_fiber"] or total_nodes >= config["max_total_unique_nodes"]
                            or time.perf_counter() - start > config["max_seconds"]):
                        break
            complete = [r for r in records.values() if r["exact"]["status"] == "complete"]
            if complete:
                bad = max(complete, key=lambda r: (Fraction(r["greedy"]["gap_exact"]), r["node_id"]))
                good = min(complete, key=lambda r: (Fraction(r["greedy"]["gap_exact"]), r["node_id"]))
                robust_bad = max(complete, key=lambda r: r["greedy"]["min_tie_gap"])
                robust_good = min(complete, key=lambda r: r["greedy"]["max_tie_gap"])
                span = Fraction(bad["greedy"]["gap_exact"]) - Fraction(good["greedy"]["gap_exact"])
                summary = dict(fiber_id=fiber_id, source=seed["source"], n=seed["n"], m=m,
                    nodes=len(records), completed=len(complete), expanded=len(expanded), edges=edges,
                    stop_reason=stop_reason,
                    component_certified_exhausted=stop_reason == "component_exhausted" and len(complete) == len(records),
                    uniform_span_exact=str(span), uniform_span=float(span),
                    max_uniform_gap_exact=bad["greedy"]["gap_exact"],
                    max_uniform_gap=bad["greedy"]["gap"],
                    robust_separation_exact=str(Fraction(robust_bad["greedy"]["min_tie_gap_exact"])
                        - Fraction(robust_good["greedy"]["max_tie_gap_exact"])),
                    bad_id=bad["node_id"], good_id=good["node_id"],
                    robust_bad_id=robust_bad["node_id"], robust_good_id=robust_good["node_id"])
                write_json(out / f"{fiber_id}-extrema.json", dict(summary=summary, bad=bad, good=good,
                    robust_bad=robust_bad, robust_good=robust_good,
                    checks=control_check(bad["rows"], good["rows"], m)))
                summaries.append(summary)
                print(json.dumps(summary), flush=True)
            gc.collect()
    write_json(out / "summary.json", dict(completed=now(), started=receipt["frozen"], total_nodes=total_nodes,
        profile=full_profile.result, fibers=summaries,
        stop_reason="global_time_budget" if time.perf_counter() - start > config["max_seconds"] else "completed_scheduled_components"))
    write_json(out / "manifest.json", {p.name: digest(p) for p in sorted(out.glob("*.json*")) if p.name != "manifest.json"})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/extremal.json")
    parser.add_argument("--out", default="runs/extremal_v1")
    args = parser.parse_args()
    search(args.config, args.out)
