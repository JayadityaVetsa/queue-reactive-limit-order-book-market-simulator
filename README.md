# Queue-Reactive Limit Order Book Market Simulator

A runnable queue-reactive limit order book simulator with calibration, validation, synthetic sample data, and an interactive Streamlit dashboard.

## What Is Implemented

- Multi-level bid/ask queue state with configurable depth, tick size, and midprice.
- Event-driven limit orders, market orders, and cancellations.
- Queue-reactive price movement: best ask depletion moves the midprice up one tick; best bid depletion moves it down one tick.
- Individual FIFO queue position tracking with partial fills.
- Empirical intensity calibration using the research formula `lambda_i(q) = N_i(q) / T(q)`.
- Validation metrics for spread, depth, and imbalance distributions.
- Deterministic simulation under a fixed seed.
- Beginner-friendly Streamlit dashboard for interactive exploration.
- Dedicated Research Guide page explaining the fake order book, equations, calibration workflow, and quant use case.

The current implementation is a Python v0.1 research simulator. The original C++ throughput target remains the natural next step for a production/HFT-grade core.

## Install

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e ".[dev]"
```

## Run The Simulator

Generate sample events, calibrate intensities, run a simulation, and validate output:

```bash
python scripts/generate_sample_data.py --events 2500 --seed 11
python scripts/calibrate.py
python scripts/run_simulation.py --events 10000 --duration 600 --seed 7
python scripts/validate.py
```

Or use the package CLI after installation:

```bash
lob-sim sample-data --events 2500
lob-sim calibrate
lob-sim simulate --duration 600 --max-events 10000
```

## Interactive Dashboard

```bash
streamlit run dashboard/app.py
```

The dashboard runs at:

```text
http://localhost:8501
```

The app is intentionally educational. It clearly states that this is **not live data**, does **not use stock tickers**, and does **not estimate company value**. It simulates a fake exchange order book so users can learn how liquidity, market orders, cancellations, and queue depletion work.

### Main Simulator Page

The main page includes:

- Help icons on every sidebar control.
- A sidebar `Page` selector with `Simulator` and `Research Guide`.
- `Market Story`, `Order Book`, `Events`, and `Trades` tabs.
- A fake midprice path chart.
- Event mix chart showing limit, market, and cancel events.
- Liquidity-through-time chart.
- Bid/ask book ladder chart.
- Plain-English tables explaining what each event and data column means.

### Research Guide Page

The guide page lives at:

```text
dashboard/pages/01_Research_Guide.py
```

Open it from the sidebar `Page` selector by choosing `Research Guide`. The standalone multipage file also exists at `dashboard/pages/01_Research_Guide.py`, but the in-app selector is the most reliable navigation path.

The guide explains:

- What an order book is.
- Bid, ask, spread, depth, midprice, and imbalance.
- Why this simulator is fake/synthetic rather than live market data.
- The queue state:

```text
Q_t = (Q_t^{-K}, ..., Q_t^{-1}, Q_t^{1}, ..., Q_t^{K})
```

- Event intensities:

```text
lambda_i(Q_t), i in {limit, market, cancel}
```

- Calibration:

```text
lambda_hat_i(q) = N_i(q) / T(q)
```

- Price movement when best queues deplete.
- How a quant researcher would use the tool for execution research, fill probability, liquidity stress testing, and later strategy backtesting.

### If You Do Not See The Research Guide

1. Refresh `http://localhost:8501`.
2. Use the sidebar `Page` selector and choose `Research Guide`.
3. If it still does not appear, stop and restart Streamlit:

```bash
streamlit run dashboard/app.py
```

## Tests

```bash
pytest
```

Implemented tests cover order book mechanics, price moves, queue tracking, deterministic simulation, calibration persistence, empirical depth/spread checks, and the full calibration-to-validation loop.

## Latest Local Verification

Run on June 16, 2026 using the bundled Codex Python runtime:

| Check | Result |
|---|---:|
| Direct deterministic/calibration smoke test | Passed |
| Pytest assertions | 11/11 reached 100% |
| Validation script | Passed |
| Python benchmark | 107,336 events/sec |
| Streamlit app tests | Passed for main app and Research Guide |
| Local dashboard endpoint | HTTP 200 |

Note: `pytest` printed all 11 passing dots but the process hung after completion in this local shell, so the command timed out after reporting `[100%]`. The direct smoke harness and validation scripts exited cleanly.

Latest demo simulation:

| Metric | Value |
|---|---:|
| Events | 7,698 |
| Trades | 1,441 |
| Traded volume | 16,568 |
| Final midprice | 100.00 |
| Mean spread | 1 tick |
| Mean bid depth | 7,186.55 |
| Mean ask depth | 6,920.63 |
| Mean imbalance | 0.0234 |

## Research Consistency

The simulator follows the Cont-Stoikov-Talreja and Huang-Lehalle-Rosenbaum queue-reactive framing:

- The book state is the vector of queue sizes across bid and ask levels.
- Events arrive from state-dependent intensities.
- Calibration estimates intensities from event counts divided by state exposure time.
- The Markov event loop samples exponential waiting times from the total event intensity.
- Price changes are triggered by depletion of the best queue.

## Data

Public LOBSTER and Kaggle datasets often require registration or manual download. For a reproducible local demo, this repo includes synthetic data generation with the same canonical schema:

```text
timestamp,event_type,side,level,volume,order_id
```

Generated files:

- `data/sample/sample_events.csv`
- `data/processed/intensities.json`
- `data/processed/simulation_events.csv`
- `data/processed/simulation_snapshots.csv`

## Project Layout

```text
src/lob_sim/          Python simulator package
dashboard/app.py      Main beginner-friendly Streamlit UI
dashboard/pages/      Streamlit guide pages
scripts/              CLI-style workflows
tests/                Unit, integration, and empirical tests
data/sample/          Small reproducible synthetic sample
data/processed/       Calibrated parameters and demo outputs
```

## Push Checklist

Before pushing:

```bash
pytest
python scripts/validate.py
python scripts/benchmark.py --events 100000
streamlit run dashboard/app.py
```

Then open `http://localhost:8501`, run the simulator once, and open the Research Guide from the sidebar `Page` selector.

## Deploy On Streamlit Community Cloud

This repo is ready for Streamlit Community Cloud deployment.

Deployment settings:

```text
Repository: your GitHub repository URL
Branch: main
Main file path: dashboard/app.py
Python version: 3.12 or any supported 3.9+ version
Secrets: none required
```

Steps:

1. Push this repository to GitHub.
2. Go to Streamlit Community Cloud.
3. Choose `Create app`.
4. Select the GitHub repository and branch.
5. Set the app entrypoint to `dashboard/app.py`.
6. Deploy.
7. After deployment, copy the public `streamlit.app` URL into this README and the GitHub repository `About` website field.

The app does not require API keys, passwords, brokerage credentials, or live market data secrets.

## Privacy And Publishing Notes

Before pushing publicly, avoid committing:

- `.streamlit/secrets.toml`
- `streamlit.log`
- `streamlit.err.log`
- `__pycache__/`
- `.pytest_cache/`
- local virtual environments
- large raw data files in `data/raw/`

The included sample and processed files are synthetic simulator artifacts, not private market data.
