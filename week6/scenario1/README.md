# Scenario 1 test - Algorithm benchmark

Task given to the agent: "Analyze this data and make a suitable visualization."

## Run

```
..\.venv\Scripts\python.exe main.py
```

Needs only pandas and matplotlib (already installed; no new dependencies added).

## Analysis choices

- Raw file `data/raw/01_AlgorithmBenchmark_matplotlib.csv` is only read, never written.
- One row has no `runtime_ms`; it is dropped. No duplicate rows. The cleaned copy is saved to `data/processed/algorithm_benchmark_clean.csv` (223 rows).
- Runtime is averaged over repeats and drawn against input size on log-log axes, because input sizes span 100 to 100,000.
- Memory is shown as a box plot at the largest input size so the algorithms are compared at one scale.
- Only pandas and matplotlib are used, as AGENTS.md prefers.

## Known deviation from AGENTS.md

AGENTS.md says "Use Python 3.12". This machine only has Python 3.9.21, so the program was run and tested with 3.9.21. See the test report.
