# crypto-edge-radar

`crypto-edge-radar` is a research project testing whether pre-TGE prediction-market information can help decide whether to participate in public token sales.

The first pilot compares public-sale valuations with Polymarket FDV markets and post-TGE returns for ten completed projects. It is a descriptive backtest, not a trading system.

## Pilot result

Current conclusion: **MAYBE**.

- Seven projects are actionable because their Polymarket markets opened before the sale closed.
- Four actionable projects have exact day-1 closes; three are positive and the median ROI is `+66.25%`.
- Exact point-in-time Polymarket probabilities are missing for every project, so the core valuation-gap hypothesis cannot yet be tested credibly.
- The result supports collecting a larger point-in-time dataset, not deploying an investment rule.

See [`research/methodology.md`](research/methodology.md) for definitions, look-ahead controls and proxy policy.

## Project structure

- `data/raw/`: immutable source data.
- `data/processed/`: derived analysis fields with exact and proxy values separated.
- `src/edge_radar/`: reusable financial calculations and feature preparation.
- `tests/`: lightweight calculation and data-quality tests.
- `notebooks/01_tge_polymarket_backtest.ipynb`: executable pilot analysis and findings.

## Run the analysis

Python 3.11 or later is recommended.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
PYTHONPATH=src pytest -q
python scripts/run_notebook.py
```

The notebook reads `data/raw/tge_polymarket_pilot_2025_2026.csv` and regenerates `data/processed/tge_polymarket_backtest_v0.csv`. It executes from the repository root and does not modify the raw dataset.
