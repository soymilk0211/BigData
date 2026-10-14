# AGENTS.md

## Project
This is a Python data-analysis assignment.
The three CSV files are visualized with different libraries:
- 01_AlgorithmBenchmark_matplotlib.csv -> matplotlib
- 02_SoftwareQuality_seaborn.csv -> seaborn
- 03_WebServiceLogs_plotly.csv -> plotly

## Rules
- Use Python 3.9+ (the local machine has Python 3.9.21).
- Prefer pandas and matplotlib; use seaborn and plotly only for the files named above.
- Files under data/raw/ may be cleaned in place (remove missing values and duplicate rows) when the user asks. Keep the untouched originals in the project root as a backup.
- Save cleaned data to data/processed/.
- Save figures to outputs/figures/.
- Do not add new dependencies unless they are necessary.

## Validation
- Run `python main.py` before finishing.
- Confirm the program can run from a clean checkout.
- Briefly explain the analysis choices in README.md.
