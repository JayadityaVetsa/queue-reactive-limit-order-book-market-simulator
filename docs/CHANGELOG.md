# Market-making extension · November 11, 2026

This extension was developed in a separate source copy. Publication is based on a fresh checkout of the existing GitHub repository, preserving its history and CI configuration.

## Added

- Fixed-spread and inventory-skewed quoting against a common synthetic event tape.
- Queue-ahead execution with partial fills, post-only checks, replacement latency and shared inventory limits.
- Average-cost accounting with position reversals, fees, marked drawdown and terminal liquidation estimates.
- Directional, volatility, informed-flow, latency and cost stress scenarios.
- Separate tuning/development/final-evaluation seeds, paired uncertainty estimates, full run tables and predetermined example paths.
- A small allocation-free C++17 FIFO primitive through a C ABI, plus Python reference and randomized parity checks.
- Standalone interactive plots, generated findings, reproduction hashes and direct research dependency versions.

## Corrected in the existing simulator

- `run()` now resets book and random state so repeated runs reproduce the configured experiment.
- A waiting time crossing the duration ends at the horizon rather than emitting an out-of-range final snapshot.
- Invalid replenishment depth is rejected before it can produce a nonterminating depletion loop; negative queue depths are rejected too.

## Scope

Existing calibration tools and the Streamlit dashboard remain available. The market-making experiment reuses the aggregate book but does not turn it into an individual-order exchange. C++ covers the execution primitive only. No native speedup, empirical fit, or real-market profitability is claimed.

## Depth-forecast follow-up

Added a directional liquidity-taking policy that estimates a 20-event price change from displayed depths, aligns its forecast with execution latency, and enters only beyond a round-trip cost threshold. It takes one-share positions, exits on a fixed schedule, sweeps visible depth and pays fees at both ends.

The new experiment separates fitting, margin validation, policy freeze and evaluation on new seeds. It retains the losing maker baselines and adds an opposite-signal control. Reports count flat runs separately, disclose worst losses and estimate the pooled profitable fraction by resampling seed clusters. The simulator and its scenario costs were unchanged for this follow-up. The complete outcome is in `reports/alpha/REPORT.md`; any positive result applies to that synthetic experiment.

## Publication · November 13, 2026

Version 0.2.0 adds browser-openable interactive walkthroughs and declares the verified Python 3.11 minimum. Frozen-policy source checks now use repository-relative POSIX paths and normalized LF line endings so Git checkouts on Windows and Linux agree. The original policy and evaluation manifest are preserved alongside the portable versions. Coefficients, margin and numerical result tables were not changed during this metadata migration.
