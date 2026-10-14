# Week 6 - Data Visualization

Each of the three datasets is visualized with a different library.
The rules for working in this project are in [AGENTS.md](AGENTS.md).

## Run

```
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe main.py
```

Tested with Python 3.9.21 on Windows.

## Layout

```
week6/
├── assignment_5_AGENTS/        Assignment folder
│   ├── 5_AGENTS.md作業. 題目.md   The assignment brief (authoritative)
│   ├── 5_AGENTS.md作業.問題1.md   Question 1: test the AGENTS.md
│   ├── AGENTS.md               Task 1: the Data Visualization AGENTS.md (draft)
│   └── test_run/               Clean test project: AGENTS.md copy, data/raw, src/, outputs/
├── scenario1/                  Example scenario 1 (data analysis); test run
│   ├── AGENTS.md
│   ├── main.py, README.md
│   ├── data/raw/, data/processed/
│   └── outputs/figures/
├── scenario2/                  Example scenario 2 (frontend + Firebase guestbook)
│   ├── AGENTS.md
│   ├── index.html, style.css
│   ├── app.js                  UI
│   ├── db.js                   All Firebase access
│   └── firebase-config.js      Placeholder config, fill in your own
├── data/
│   ├── raw/                    Original CSVs, never modified
│   └── processed/              Cleaned CSVs written by main.py
├── outputs/figures/            PNG (matplotlib, seaborn) and HTML (plotly) figures
├── 01_AlgorithmBenchmark_matplotlib.csv   Original datasets (backup)
├── 02_SoftwareQuality_seaborn.csv
├── 03_WebServiceLogs_plotly.csv
├── 4_AGENTS.md.pdf            Lecture notes on AGENTS.md
├── AGENTS.md                   Rules for this project
├── main.py                     Cleans the data and draws all figures
├── requirements.txt
└── README.md
```

`.venv/` (local virtual environment) is not listed.

## Analysis choices

**01 Algorithm benchmark (matplotlib)**
- One row had no `runtime_ms`; it was dropped (1 of 224 rows). No duplicate rows were found in any of the three files.
- Runtime and comparisons are averaged over the repeats, then plotted against input size on log-log axes. Input sizes span 100 to 100,000, so linear axes would hide the small sizes.
- Binary search is nearly flat while linear search and the two sorts grow roughly linearly with input size. At small sizes binary search is actually the slowest, probably because of fixed overhead.
- Memory is shown as a box plot at the largest input size only, to compare algorithms at a single scale.

**02 Software quality (seaborn)**
- No missing values, so the data is copied to `data/processed/` unchanged.
- The correlation heatmap gives an overview of the numeric metrics. LOC and code churn are strongly related (0.73). Defect count correlates only weakly with any single metric (at most about 0.21).
- Scatter, box and bar plots break complexity, coverage and defects down by language and module type.

**03 Web service logs (plotly)**
- `timestamp` is parsed to datetime and `cache_hit` to boolean.
- Output is interactive HTML so points can be hovered. Plotly.js is loaded from a CDN, so the HTML files need an internet connection to open.
- Figures cover latency by endpoint, status codes by endpoint, requests per hour, latency by region and cache hit, and response size vs latency.
