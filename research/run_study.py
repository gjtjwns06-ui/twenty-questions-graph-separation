#!/usr/bin/env python3
"""Run the frozen experiment without overwriting any previous run."""
import argparse
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/main.json")
    parser.add_argument("--out", default="runs/main")
    args = parser.parse_args()
    if Path(args.out).exists():
        raise FileExistsError("Choose a new --out directory; original measurements are preserved.")
    for command in ("generate", "split", "compare", "report", "audit"):
        subprocess.run([sys.executable, "experiment.py", command, "--config", args.config,
                        "--out", args.out], check=True)


if __name__ == "__main__":
    main()
