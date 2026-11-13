# Local verification · November 11, 2026

Environment: Windows, Python 3.11.15, NumPy 2.4.6, pandas 3.0.3; MinGW g++ for the native library. Direct research package versions are recorded in `requirements-research.txt`.

## Completed

- `python -m pytest` with `LOB_NATIVE` pointing at the compiled library: **30 passed** after the depth-forecast extension. Third-party pytest plugin auto-loading was disabled for this local check.
- Native compilation with `-std=c++17 -O2 -Wall -Wextra -Werror -shared`: passed.
- 10,000 randomized FIFO primitive comparisons against the Python reference: exact equality.
- Full experiment with each backend: **320 evaluation runs per backend**, 4,000 events per run; all numeric run tables matched exactly.
- All **160** scenario/seed event-tape digests matched between backends.
- The earlier maker study's source hashes matched its implementation when generated; its manifest is preserved as a historical snapshot.

The test suite includes average-cost accounting through reversals, queue priority and partial fills, better-price depth, post-only/latency behavior, inventory bounds, repeated-run determinism, horizon bounds, invalid replenishment, and prefix invariance when future data changes.

The final report uses five tuning seeds and 20 separate evaluation seeds across eight scenarios. Development seeds used while correcting the quoting implementation are explicitly disclosed. The checked-in figure is a standalone Plotly HTML file with its JavaScript bundled.

## Depth-forecast strategy

The new tests check side-reflection of features, latency-aligned training labels, spread and fee accounting on a known round trip, short profits, scheduled losing exits, latency at both ends, the no-trade/cost gate, visible-depth slippage, future-prefix invariance, and latency-model mismatch rejection.

The complete small integration run completed with two seeds per split and 200 events. It exercised model fitting, validation, policy freeze, all four comparison policies, tables, report generation, source hashes and standalone Plotly output. It is a functional smoke test, not the full evaluation.

The full depth-forecast experiment uses five training seeds, five validation seeds and 50 fresh evaluation seeds across eight scenarios. Implementation hashes are checked against the frozen policy before evaluation. Its report and manifest are under `reports/alpha`.

The full run completed: **1,600 comparison runs**, including **400 alpha runs** of 4,000 events each. Alpha produced **292 profitable, 64 losing and 44 flat** outcomes. Mean net P&L was **30.50 tick-shares**; the worst run lost **28.36**. A seed-cluster bootstrap gave a pooled profitable-fraction interval of **68.8%–76.8%**. Latency and combined stress had nonpositive average P&L.

The post-run audit confirmed every alpha position was liquidated, executed volume equaled twice the completed one-share round-trip count, fees matched scenario rates, gross-mid P&L decomposed into net P&L plus execution shortfall and fees, example paths reconciled realized/unrealized accounting, and the source and frozen-policy hashes remained unchanged. Machine-readable checks are in `reports/alpha/VERIFICATION.json`.

All **160 historical tape hashes** from the earlier market-making experiment were regenerated and matched exactly. This independently verifies that the simulator and scenario generator were not altered to make the new strategy profitable; see `reports/alpha/generator_verification.json`.

## Practical limits

The prepared Linux CI expansion builds the native library and runs tests plus small experiments. GitHub refused the workflow edit because the available credentials lack workflow-write permission, so the active hosted workflow still runs the Python suite. See `docs/CI.md` and the ready-to-apply patch. The existing dashboard was not changed or newly exercised in this extension. No throughput benchmark or real-market validation was performed.

An attempted local browser preview of the generated figure was blocked by the browser environment's inability to reach the local HTTP server. HTML generation completed, but this extension does not claim a visual browser inspection.

## Publication checks · November 13, 2026

The fresh GitHub checkout passed **31 tests** with the compiled C++ library enabled. This includes a new regression check that source hashes are identical across LF/CRLF checkouts and use portable path separators. The frozen full model also completed a small evaluation through the portable hash guard; the native maker experiment completed its own smoke run.

The first published commit, `514b140be1a691becf4dba8f1f7d03b90d8e079c`, passed the existing hosted CI workflow. Expanded native/smoke CI coverage is prepared in `docs/ci-update.patch` and awaits workflow-write permission.

Original evaluation manifests and the frozen model snapshot are preserved. Publication changes only the source-hash serialization and adds a regression test, package metadata and exported walkthroughs. Coefficients, the selected margin and historical result CSVs are unchanged. The full 400-run alpha study was not rerun during publication because forecast and trading calculations did not change.
