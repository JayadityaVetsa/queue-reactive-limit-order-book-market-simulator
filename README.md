# Queue-reactive order book and trading experiments

Can current order-book depth predict a move large enough to pay for trading?

This project combines a Python queue-reactive order book, shadow FIFO execution, a small C++17 execution primitive, and reproducible trading experiments. The first study compares fixed-spread and inventory-aware market makers. The second adds a depth-forecast strategy that takes liquidity only when its estimated edge covers costs. All policies replay identical synthetic event tapes.

The latest frozen policy was profitable in **292 of 400 fresh simulation runs (73%)**, with 64 losses and 44 flat runs after execution costs. Mean P&L was 30.50 tick-shares. Latency and combined stress still had negative average P&L. These are results in a synthetic queue-depletion model, not evidence of live profitability.

## Start with the evidence

- [Latest findings](reports/alpha/REPORT.md): depth-forecast strategy, maker baselines, an opposite-signal control, and 50 fresh seeds per scenario.
- [Interactive comparison](reports/alpha/comparison.html): net P&L, profitable fractions, and a predetermined stress path. Download/open locally to view.
- [Strategy explained](docs/ALPHA_STRATEGY.md): forecast inputs, cost threshold, a worked trade, latency, and failure modes.
- [Interactive walkthroughs](docs/walkthrough/README.md): adjustable order books and a trade you can follow from entry to exit. Download the HTML files and open them in a browser.
- [Earlier market-making findings](reports/market_making/REPORT.md): the losing strategies that motivated the new policy. This is a preserved prior experiment, with its original source snapshot hashes.
- [Execution and accounting notes](docs/MARKET_MAKING.md): quote rules, units, queue assumptions, equations, native build instructions, and tradeoffs.
- [Latest run-level results](reports/alpha/runs.csv), [frozen policy](reports/alpha/frozen_policy.json), and [reproduction manifest](reports/alpha/manifest.json).

## Reproduce

Use Python 3.11 or newer for the documented environment:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m pip install -r requirements-research.txt
python -m pytest
python scripts/alpha_experiment.py --stage prepare
python scripts/alpha_experiment.py --stage evaluate
```

The latest experiment runs without a compiler. Preparation fits the forecasts and selects a safety margin on validation paths, then writes a frozen policy. Evaluation checks the implementation hashes before using fresh paths. It writes tables, an HTML figure with bundled Plotly, sample paths, source/tape hashes, and a short report under `reports/alpha`.

For a quick integration check run `python scripts/alpha_experiment.py --events 200 --train-events 200 --train-seeds 2 --validation-seeds 2 --seeds 2 --output reports/alpha_smoke`. This checks functionality and does not reproduce the full statistical study. Run `python scripts/market_making_experiment.py` to reproduce the earlier market-making experiment with the current implementation.

The exact direct research dependencies used for the checked-in results are in `requirements-research.txt`. The manifest records the interpreter version; floating dashboard dependencies are outside that research environment snapshot.

To build the optional native backend:

```bash
cmake -S . -B build
cmake --build build --config Release
```

Pass the resulting shared library to the earlier market-making script's `--native` option and set `LOB_NATIVE` to its absolute path when running tests. See the execution notes for direct compiler commands on Windows and Linux. The native primitive has exact parity with the Python reference; no performance advantage is claimed for a per-fill ctypes call. The depth forecaster and aggressive execution policy use Python/NumPy.

## What the studies control

The original maker study uses five-share quotes and a 40-share inventory cap. Its inventory policy shifts the reservation price by `-skew * inventory`; a zero skew remains an eligible outcome. Its source and settings are recorded with the earlier report.

The new study uses training seeds 100–104, validation seeds 200–204, and evaluation seeds 3000–3049. A 20-event forecast uses displayed depths only. It trades one share when `abs(expected_move) > 1 + 2 * fee + margin`, then exits on schedule. It accounts for latency at entry and exit. The makers use one-share quotes and an eight-share inventory cap for this comparison; inventory skew scales to 0.5 ticks/share. The new policy voluntarily caps its own position at one share. An opposite-signal control tests the learned direction; cash earns zero. Flat runs are counted separately from wins.

Scenarios cover a quiet market, upward and downward moves, a volatility regime change, informed flow, delayed replacement, higher fees, and combined stress. Neither the generator nor its costs were softened for the new policy. Each run records net P&L, fees, volume, drawdown and inventory. The maker study also reports signed ten-event fill markouts. Paired comparisons retain seed alignment; pooled profitable-fraction intervals account for dependence across scenarios by resampling whole seed clusters.

## Existing simulator tools

The aggregate book supports multi-level depth, market orders, cancellations, depletion-driven price changes, and partial fills. A separate FIFO tracker supports individual resting orders. Calibration estimates event rates from counts divided by state exposure; synthetic sample generation and distribution checks remain available.

```bash
python scripts/generate_sample_data.py --events 2500 --seed 11
python scripts/calibrate.py
python scripts/run_simulation.py --events 10000 --duration 600 --seed 7
python scripts/validate.py
streamlit run dashboard/app.py
```

The existing Streamlit dashboard explores the background book and includes a Research Guide. Market-making findings are delivered in the report and interactive HTML figure.

## Boundaries

Policies are small shadow participants and cannot change background prices or flow. Makers receive no queue credit for cancellations; replacements lose priority and old quotes remain live in transit. Their terminal liquidation estimate assumes unlimited depth at half a tick plus fees. The new aggressive policy sweeps visible depth at entry and exit and finishes flat. Scenario parameters are illustrative, not fitted to an exchange. Event latency is not physical time. These choices materially affect the results.

The synthetic generator links queue depletion to price movement, so depth is predictive by construction. Successful trading in this model does not establish a transferable real-market edge or capacity. The C++ component is an allocation-free FIFO primitive with a C ABI; research orchestration and accounting remain in Python. The latest predictor estimates a price change, not a calibrated up/down probability.

## Layout

```text
src/lob_sim/                 book, calibration, execution, ledger, depth forecast and policies
native/execution.cpp        integer FIFO primitive
scripts/market_making_experiment.py
scripts/alpha_experiment.py  train, freeze and evaluate the cost-gated forecast
reports/alpha/              latest report, policy, plots and raw results
reports/market_making/      generated findings and raw results
docs/MARKET_MAKING.md       modeling and engineering decisions
tests/                     mechanics, accounting, determinism and native parity
dashboard/                 existing educational Streamlit app
```

The implementation is informed by the queue-reactive literature and the reservation-price intuition of Avellaneda–Stoikov; links and the distinction from their models are in the execution notes. It makes no claim about any firm's proprietary infrastructure.
