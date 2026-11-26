# Reproducing the research

[Overview](../README.md) · [한국어 소개](README.ko.md) · [Results and scope](RESULTS_AND_SCOPE.md)

The publication checkout keeps the completed workspace under `research/`. Its files and historical manifests are preserved byte for byte. The presentation, archive handling and CI live at the repository root.

## 1. Verify before running experiments

Python 3.10+ is sufficient for archive verification and restoration; the recorded scientific environment was Python 3.13.5.

```powershell
python scripts/verify_release.py
```

This checks all 599 included research files, decompresses archived files in memory for hashing, compares the archived scientific manifests, and checks the local links in the new documentation. Restoration is not needed for this check.

The manifest explicitly declares 74 excluded local/third-party artifacts: 42 downloaded source files and extracted texts, 24 raw web-search/page receipts, four browser upload/download receipts, and four TeX smoke/debug outputs. They are not represented as successfully checked local files. Original source URLs and hashes remain in [the literature source manifest](../research/runs/novelty_audit_v1/source_manifest.json), with [authored claim comparisons](../research/runs/novelty_audit_v1/claim_matrix.csv).

The historical novelty and manuscript validators expected the complete private working directory, including those local source snapshots and browser receipts. Use `scripts/verify_release.py` for this public checkout; a private-workspace validator can fail on a declared omission even when the public package is intact. Literature absence and formal proof correctness are not certified by the hash checker.

## 2. Install the recorded scientific dependencies

PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r research/requirements-lock.txt
```

For POSIX shells, the corresponding interpreter is `.venv/bin/python`:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r research/requirements-lock.txt
```

The original timing and memory measurements were taken on Windows, Core Ultra 5 226V, 8 logical CPUs and approximately 15.54 GiB RAM, with BLAS threads fixed to one. Exact integer/rational results are reproduction targets. Wall time, RSS, termination timing and time-budgeted search visit counts depend on the machine.

## 3. Recompute the exact witnesses

The original 14×8 example concerns the optimal first question and is distinct from the 14×8 base used in the amplification proof.

```powershell
.\.venv\Scripts\python.exe research/verify_witness.py --output witness14_recomputed.json
.\.venv\Scripts\python.exe scripts/verify_finite38.py
```

The 38×18 script checks distinct degree-three rows, indexed Gram equality, degree ten, biconnectivity, the saved optimal cost, and full greedy cost with an independently written `Fraction` recursion. Expected totals:

| World | Optimal total | Uniform-tie greedy total | Mean regret |
|---|---:|---:|---:|
| A | 215 | 443/2 | 13/76 |
| B | 216 | 216 | 0 |

Run the existing solver/invariance tests from the preserved research directory:

```powershell
Push-Location research
..\.venv\Scripts\python.exe -m unittest discover -s tests -v
Pop-Location
```

CI runs the public integrity check, the original witness, the existing research tests, and the finite 38×18 check. It does not regenerate the full study or establish a theorem automatically.

## 4. Restore the raw records

```powershell
python scripts/restore_data.py
```

Ten large JSONL/CSV files are stored as deterministic gzip streams: 189,166,506 original bytes in 15,650,478 compressed bytes. Restoration verifies archive hashes and original hashes, creates the original paths under `research/`, and is safe to run again. It refuses to replace a modified destination. The restored large files are ignored by Git because their checked-in equivalents are the lossless archives.

The original environment manifests, predictions, model selection, parent splits, timings, incomplete runs and zero-effect pairs are retained. Restoration performs no model fitting or resampling.

## 5. Regenerate presentation or rerun a study

Regenerate the four README figure pairs from saved JSON/CSV:

```powershell
.\.venv\Scripts\python.exe scripts/make_assets.py
```

The figure input hashes are recorded in [assets/provenance.json](../assets/provenance.json). Large-instance bands are evaluated proof formulas; the finite bars and paired ML intervals come from saved raw results.

To rerun the frozen main experiment, first restore the raw inputs and choose a new output directory:

```powershell
Push-Location research
..\.venv\Scripts\python.exe run_study.py --config configs/main.json --out runs/reproduction_github
Pop-Location
```

This is a new experiment run and can take substantially longer than the exact witness checks. The runner refuses to overwrite an existing run. Keep the recorded source/configuration unchanged when using the frozen receipt. Details of pilot selection, split isolation, features and model selection are in the [original workflow README](../research/README.md) and [preregistered experiment design](../research/reports/EXPERIMENT_DESIGN.md).

The extremal and connector stages have separate configurations and output policies; follow the corresponding sections of the preserved README rather than replacing the saved `runs/*_v1` folders. Time-limited searches are not expected to visit exactly the same number of states on every machine.

## 6. Compile the paper

Open [research/paper/main.tex](../research/paper/main.tex) in XeLaTeX, TeX Live 2025+. The complete paper includes its tables, vector figures and bibliography, so external image files and BibTeX are unnecessary. The final online build was XeLaTeX / TeX Live 2026, 18 pages, Errors 0, Warnings 0. One bibliography underfull-box typesetting message was visually inspected.

The delivered [PDF](../research/output/pdf/Twenty_Questions_Paper_Final.pdf) is the actual completed online build. The [paper evidence file](../research/paper/evidence.json) lists the 31 preserved inputs used for table and figure generation. The publication wrapper does not revise those measurements.
