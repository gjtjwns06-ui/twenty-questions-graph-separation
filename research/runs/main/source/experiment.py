#!/usr/bin/env python3
"""Reproducible entry point. Run --help for commands."""
import os
# Reproducible CPU measurements; avoid BLAS oversubscription on the user's PC.
for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[name] = "1"

import argparse
import json
from pathlib import Path
import subprocess
import sys
from tq.io import environment, write_json, read_jsonl, now


def main():
    p = argparse.ArgumentParser()
    p.add_argument("command", choices=["pilot", "generate", "split", "compare", "report", "audit"])
    p.add_argument("--config", type=Path)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8")) if args.config else None
    if args.command == "pilot":
        args.out.mkdir(parents=True, exist_ok=False)
        write_json(args.out / "environment.json", environment())
        write_json(args.out / "config.json", config)
        summaries = []
        for i, cell in enumerate(config["cells"]):
            job = dict(config, name=f'pilot-{i:02d}', seed=config["seed"] + i * 2000003, cells=[cell])
            job_file = args.out / f"job-{i:02d}.json"
            write_json(job_file, job)
            destination = args.out / f"cell-{i:02d}"
            subprocess.run([sys.executable, __file__, "generate", "--config", str(job_file),
                            "--out", str(destination)], check=True)
            summaries.append(json.loads((destination / "summary.json").read_text(encoding="utf-8")))
        write_json(args.out / "summary.json", dict(completed=now(), cells=summaries))
    elif args.command == "generate":
        from tq.data import run_dataset
        env = environment()
        if config.get("freeze_receipt"):
            receipt = json.loads(Path(config["freeze_receipt"]).read_text(encoding="utf-8"))
            from tq.io import digest
            assert digest(args.config) == receipt["config_sha256"], "Frozen config changed"
            assert all(digest(path) == value for path, value in receipt["source_sha256"].items()), "Frozen sources changed"
        run_dataset(config, args.out, audit_all_trades=True)
        write_json(args.out / "environment.json", env)
    elif args.command == "split":
        from tq.splits import assign_splits
        assign_splits(args.out, config)
    elif args.command == "compare":
        from tq.models import compare
        compare(args.out, config)
    elif args.command == "report":
        from tq.reporting import report
        report(args.out, config)
    elif args.command == "audit":
        from tq.audit import audit_run
        audit_run(args.out)


if __name__ == "__main__":
    main()
