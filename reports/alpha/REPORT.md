# Cost-gated order-book forecast

Publication note (November 13, 2026): the original evaluation policy and manifest are preserved as `frozen_policy.original.json` and `manifest.original.json`. Published source hashes now normalize Git line endings and path separators. Model coefficients, selected margin and the numerical results below are unchanged; the portable manifests record this metadata migration.

**Positive net P&L in 292/400 runs (73.0%); 64 losses and 44 flat runs.**
Mean net P&L: 30.50 tick-shares; median: 26.60; worst: -28.36. The seed-cluster bootstrap interval for the pooled profitable fraction is 68.8%–76.8%.

This evaluates a directional liquidity-taking strategy in the existing synthetic market. It does not establish a real-market trading edge. A flat or no-trade run is never counted as profitable.

## What changed

The earlier maker received fills with strongly negative subsequent markouts. Simply widening quotes did not reliably repair that on development tapes. The new policy predicts a 20-event midprice change from the displayed bid/ask depths. It crosses the spread only when that forecast exceeds a full round-trip spread, both fees, and a validation-selected safety margin. It then exits on a predetermined schedule, whether the trade won or lost.

Frozen margin: **0.5 ticks**, with active trading **True**. One-share positions keep the experiment small relative to displayed depth. Buys and sells sweep the actual visible ladder and pay per-share fees. Both entry and exit incur the configured latency. The forecast is trained on returns measured after that latency, so it cannot assume an old signal survives unchanged.

## Fresh evaluation

50 seeds per scenario, 4000 events per run. Seeds begin at 3000. All policies see identical tapes. The old makers are scaled to one-share quotes and an eight-share cap; their inventory skew is scaled to 0.5 ticks/share. The new strategy voluntarily holds at most one share. Cash earns zero and is included as the economic hurdle.

| Scenario | Profitable / total | Mean alpha P&L | Median | Worst | Fixed maker mean | Inventory maker mean | Opposite-signal mean |
|---|---:|---:|---:|---:|---:|---:|---:|
| quiet | 46/50 | 44.78 | 48.28 | -22.20 | -499.12 | -426.35 | -205.86 |
| uptrend | 45/50 | 41.92 | 46.94 | -26.20 | -492.01 | -437.69 | -203.00 |
| downtrend | 45/50 | 47.64 | 54.36 | -18.20 | -741.99 | -451.45 | -208.72 |
| volatility_switch | 47/50 | 46.81 | 42.30 | -18.92 | -517.66 | -445.68 | -211.79 |
| informed | 44/50 | 48.08 | 47.92 | -28.36 | -559.07 | -475.52 | -208.32 |
| latency | 24/50 | -0.07 | -0.66 | -19.24 | -68.28 | -65.10 | -9.99 |
| costs | 39/50 | 15.26 | 13.70 | -26.60 | -652.32 | -554.71 | -111.38 |
| combined | 2/50 | -0.41 | 0.00 | -12.80 | -398.26 | -537.91 | -0.29 |

## Failures and uncertainty

Scenarios with nonpositive average alpha P&L: latency, combined.
Scenarios without a strict majority of profitable runs: latency, combined.

Latency can erase the forecast before execution. Higher fees leave fewer viable entries. A positive pooled result can coexist with losses in stress regimes; inspect those rows rather than reporting only the aggregate success rate. The opposite-signal control enters on the same absolute forecast triggers and follows the same holding schedule, but flips direction. It tests whether the learned sign adds value beyond trade timing and small position size.

## Research separation

Training seeds: [100, 101, 102, 103, 104]. Validation seeds: [200, 201, 202, 203, 204]. Development probes used seeds 30–31, 40–42 and 50–54. Earlier market-making evaluation seeds 1000–1019 and 2000–2019 were already seen and are excluded from this final evaluation.

Depth features use one-, two-, four- and eight-level imbalance, per-level log-depth differences and nonlinear sweep-depth features. Their volume scale comes from training data. Ridge regression (penalty 10) is fixed in advance. Separate latency-zero and latency-eight models use the same training tapes, with latency-aligned labels. No scenario name, next order, future depth or future price is a prediction input. Labels use strictly future prices from training tapes only. Complete paths, not interleaved rows, are allocated to splits.

Four margins (0, 0.25, 0.5 and 0.75 ticks) are ranked by average validation net P&L across all scenarios. If none beats cash, the frozen policy abstains. The coefficient files, selection scores and implementation hashes are written before evaluating seeds 3000 onward. The model and selected margin remain unchanged throughout evaluation.

## Model dependence

The generator mechanically moves its reference price when queues deplete and replenishes depth. Displayed depth therefore contains predictive information by construction. The strategy monetizes that simulated relationship; the opposite-signal control does not turn it into empirical evidence. Future work needs external event data, a price-time-priority venue, impact, physical timestamps, and out-of-sample validation across real trading days. The one-share clip also means these results say nothing about capacity.

The background market, informed-flow mechanism, volatility, latency and fees were not softened to obtain this result. The old shadow-maker execution remains conservative and separate. The new taker exits against visible depth rather than marking a residual position favorably. All reported profits include spread crossing, depth slippage and fees. No martingale sizing, averaging down, price-dependent exit delay, future-price entry signal, or annualized return is used.

## Reproduce

```bash
python scripts/alpha_experiment.py --stage prepare
python scripts/alpha_experiment.py --stage evaluate
```

Open comparison.html for plots. frozen_policy.json contains the deployable coefficients and selected margin. validation.csv preserves every candidate result. runs.csv includes every evaluation run; summary.csv includes win/loss/flat counts, fees, volume, drawdown and inventory. paired.csv preserves comparisons by seed. manifest.json records source hashes, frozen-policy digest and tape digests. Example path CSVs always use the first evaluation seed.
