from __future__ import annotations
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import threading
import time
import psutil


def now():
    return datetime.now().astimezone().isoformat()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def append_jsonl(path, data):
    with Path(path).open("a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False, allow_nan=False) + "\n")
        f.flush()


def read_jsonl(path):
    with Path(path).open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


class Profile:
    """5 ms sampled RSS plus the Windows process lifetime high-water RSS.

    Short phases can peak between samples. Report that limitation explicitly.
    """
    def __enter__(self):
        self.process = psutil.Process()
        self.baseline = self.process.memory_info().rss
        self.peak = self.baseline
        self.stop = threading.Event()
        self.start = time.perf_counter()

        def sample():
            while not self.stop.wait(.005):
                self.peak = max(self.peak, self.process.memory_info().rss)
        self.thread = threading.Thread(target=sample, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, *args):
        self.stop.set()
        self.thread.join()
        info = self.process.memory_info()
        self.peak = max(self.peak, info.rss)
        self.result = dict(seconds=time.perf_counter() - self.start,
                           baseline_rss_mb=self.baseline / 2**20,
                           sampled_peak_rss_mb=self.peak / 2**20,
                           sampled_increment_mb=max(0, self.peak - self.baseline) / 2**20,
                           lifetime_peak_rss_mb=getattr(info, "peak_wset", info.rss) / 2**20,
                           sampling_interval_seconds=.005)


def environment():
    try:
        cpu = subprocess.check_output(["powershell", "-NoProfile", "-Command",
            "(Get-CimInstance Win32_Processor).Name"], text=True).strip()
    except (OSError, subprocess.SubprocessError):
        cpu = platform.processor()
    versions = subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True).splitlines()
    paths = [Path("experiment.py")] + sorted(Path("tq").glob("*.py"))
    return dict(timestamp=now(), python=sys.version, executable=sys.executable,
                platform=platform.platform(), cpu=cpu, logical_cpus=psutil.cpu_count(),
                physical_memory_mb=psutil.virtual_memory().total / 2**20,
                dependencies=versions, source_sha256={str(p): digest(p) for p in paths if p.exists()},
                threading={key: os.environ.get(key) for key in
                           ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")})
