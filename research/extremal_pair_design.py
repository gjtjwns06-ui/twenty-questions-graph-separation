#!/usr/bin/env python3
"""Adversarially design a Pasch pair's shared context; Gram varies between steps."""
from fractions import Fraction
from itertools import combinations
import argparse
import gc
import json
import math
from pathlib import Path
import random
import time
from extremal_experiment import evaluate, canonical
from tq.core import control_check
from tq.io import Profile, write_json, append_jsonl, digest, now

LEFT = ((0, 2, 4), (0, 3, 5), (1, 2, 5), (1, 3, 4))
RIGHT = ((0, 2, 5), (0, 3, 4), (1, 2, 4), (1, 3, 5))


def run(config_path, out):
    config_path, out = Path(config_path), Path(out)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    out.mkdir(parents=True, exist_ok=False)
    write_json(out / "config.json", config)
    write_json(out / "frozen.json", dict(frozen=now(), config_sha256=digest(config_path),
        sources={p: digest(p) for p in ["extremal_pair_design.py", "extremal_experiment.py", "tq/core.py"]}))
    initial = json.loads(Path(config["seed_pair"]).read_text(encoding="utf-8"))
    ia, ib = canonical(initial["bad"]["rows"]), canonical(initial["good"]["rows"])
    sl, sr, sc = tuple(sorted(set(ia)-set(ib))), tuple(sorted(set(ib)-set(ia))), tuple(sorted(set(ia)&set(ib)))
    assert len(sl) == len(sr) == 4
    rng = random.Random(config["seed"])
    start, cache, best = time.perf_counter(), {}, None
    accepted_count, proposal_count = 0, 0
    with Profile() as profile:
        for size_index, size in enumerate(config["sizes"]):
            n, m = size["n"], size["m"]
            for restart in range(config["restarts"]):
                if time.perf_counter() - start > config["max_seconds"]:
                    break
                seeded = n == len(ia) and m == initial["bad"]["m"] and restart == 0
                left, right = (sl, sr) if seeded else (LEFT, RIGHT)
                available = [r for r in combinations(range(m), 3) if r not in set(left)|set(right)]
                common = sc if seeded else canonical(rng.sample(available, n-4))

                def assess(background, predecessor):
                    nonlocal best
                    a, b = canonical(left+background), canonical(right+background)
                    key = (m, a, b)
                    if key in cache:
                        return cache[key]
                    checks = control_check(a, b, m)
                    ra, rb = evaluate(a, m, config["solver"]), evaluate(b, m, config["solver"])
                    record = dict(candidate_id=len(cache), size_index=size_index, restart=restart,
                        predecessor=predecessor, a=ra, b=rb, checks=checks,
                        common_background=background, trade_left=left, trade_right=right)
                    if ra["exact"]["status"] == rb["exact"]["status"] == "complete":
                        ga, gb = Fraction(ra["greedy"]["gap_exact"]), Fraction(rb["greedy"]["gap_exact"])
                        bad, good = (ra, rb) if ga >= gb else (rb, ra)
                        contrast = abs(ga-gb)
                        robust = Fraction(bad["greedy"]["min_tie_gap_exact"])-Fraction(good["greedy"]["max_tie_gap_exact"])
                        record.update(complete=True, contrast_exact=str(contrast), contrast=float(contrast),
                            robust_separation_exact=str(robust), robust_separation=float(robust),
                            bad_id=bad["node_id"], good_id=good["node_id"], max_gap=max(float(ga), float(gb)),
                            energy=float(contrast)+.02*max(float(ga), float(gb)))
                        rank = (contrast, robust, max(ga, gb))
                        if best is None or rank > best[0]:
                            best = (rank, record)
                            write_json(out / "best.json", record)
                            progress = dict(candidate_id=record["candidate_id"], contrast=str(contrast),
                                robust=str(robust), n=n, m=m, seconds=time.perf_counter()-start)
                            append_jsonl(out / "incumbents.jsonl", progress)
                            print(json.dumps(progress), flush=True)
                    else:
                        record.update(complete=False, energy=None)
                    cache[key] = record
                    append_jsonl(out / "candidates.jsonl", record)
                    return record

                current = assess(common, None)
                for step in range(config["steps_per_restart"]):
                    if time.perf_counter()-start > config["max_seconds"]:
                        break
                    index = rng.randrange(len(common))
                    inserted = rng.choice([r for r in available if r not in common])
                    proposal = canonical(common[:index]+common[index+1:]+(inserted,))
                    record = assess(proposal, current["candidate_id"])
                    temperature = config["initial_temperature"]*(config["final_temperature"]/config["initial_temperature"])**(step/max(1,config["steps_per_restart"]-1))
                    accepted = False
                    if record["complete"]:
                        delta = record["energy"]-current["energy"] if current["complete"] else 1
                        accepted = delta >= 0 or rng.random() < math.exp(max(-700,delta/temperature))
                    append_jsonl(out / "trace.jsonl", dict(size_index=size_index,restart=restart,step=step,
                        before=current["candidate_id"],proposal=record["candidate_id"],accepted=accepted,
                        removed=common[index],inserted=inserted,temperature=temperature))
                    proposal_count += 1
                    if accepted:
                        accepted_count += 1
                        current, common = record, proposal
                gc.collect()
    write_json(out / "summary.json", dict(completed=now(), unique_candidates=len(cache),proposals=proposal_count,
        accepted=accepted_count,profile=profile.result,best_candidate=best[1]["candidate_id"] if best else None,
        best_contrast_exact=str(best[0][0]) if best else None,
        scope="Each pair controlled; Gram varies along shared-background design path",
        stop_reason="time_budget" if time.perf_counter()-start>config["max_seconds"] else "scheduled_steps_completed"))
    write_json(out / "manifest.json", {p.name:digest(p) for p in out.glob("*.json*") if p.name!="manifest.json"})


if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--config",default="configs/extremal_pair_design.json")
    p.add_argument("--out",default="runs/extremal_pair_design_v1")
    args=p.parse_args()
    run(args.config,args.out)
