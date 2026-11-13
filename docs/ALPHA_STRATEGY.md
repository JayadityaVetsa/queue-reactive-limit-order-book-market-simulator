# The cost-gated depth strategy

The strategy asks a concrete question: does the current order book predict a large enough price move to pay for entering and exiting a position?

It is a directional liquidity taker. It buys at the ask or sells at the bid when the expected price movement covers costs. The earlier passive market makers remain comparison policies.

## What it observes

At the beginning of an event, the policy reads displayed bid and ask quantities. It computes:

- Imbalance over the first one, two, four and eight levels: `(bid depth - ask depth) / (bid depth + ask depth + 1)`.
- The difference in log depth between bids and asks at each level.
- Three nonlinear depth features that represent how easily a market order might sweep the near side. Their volume scale is the average market-order size in the training data.

A ridge regression turns these features into an expected price change, in ticks, over a 20-event holding period. Thick bids and thin asks often predict upward moves in this synthetic queue-depletion model; the regression learns the strength and combination of those relationships. The forecast is an expected move, not a claim that the next trade must move the price.

For latency `L`, the training target is:

```
mid_at_event(t + L + 20) - mid_at_event(t + L)
```

Only the depth observed at `t` is a feature. There are separate models for zero-event and eight-event latency. This keeps the prediction horizon aligned with the period during which a position can actually be held.

## The trading rule

With a one-tick quoted spread, crossing the spread once to enter and again to exit costs one tick per share. Both trades also pay fees. The policy therefore requires:

```
abs(expected_move) > 1 tick + 2 * fee_per_share + safety_margin
```

Four margins are evaluated on validation paths; the frozen selection is 0.5 ticks in the documented full run. At the standard fee of 0.02 ticks/share, the entry threshold is 1.54 ticks. At the high fee of 0.30, it is 2.10 ticks.

A positive forecast above the threshold opens a one-share long. A negative forecast below the negative threshold opens a one-share short. A smaller forecast leaves the policy in cash. There is at most one position or pending entry at a time.

The exit is scheduled when the entry instruction is sent. Both instructions incur latency. The policy holds the resulting position for 20 events and then exits regardless of profit or loss. It does not double down or postpone losing exits. Position size stays fixed.

## One example

Suppose the current mid is 100.00 ticks and the forecast is an upward move of 2.00 ticks. With a 0.02 fee and 0.50 margin, that exceeds the 1.54-tick threshold.

With zero latency, the policy buys one share at 100.50. If the mid is 102.00 at the scheduled exit, it sells at 101.50. The round trip earns `101.50 - 100.50 - 0.04 = 0.96` tick-shares after fees.

If the mid instead falls to 99.00, the scheduled sale occurs at 98.50 and the loss is `98.50 - 100.50 - 0.04 = -2.04`. The model can be wrong; its threshold is not a guaranteed profit bound.

With latency, the entry price is the ask when the instruction arrives, not the ask from the decision event. Exits work the same way. Larger clips sweep deeper displayed levels and pay the associated slippage; the standard experiment uses one share. The last event is reserved for an actual displayed-depth liquidation if needed.

## What counts as success

Every evaluation path appears in the run table. A run is profitable only if its net P&L exceeds `1e-7` tick-shares; this tolerance prevents floating-point dust from being counted as a win. A no-trade run is flat, not profitable. Mean P&L, median, worst loss, fees, traded volume, drawdown and inventory appear alongside the profitable fraction.

The policy is compared with fixed-spread and inventory-aware makers and an opposite-signal control. That control takes the other direction on the same triggers and holding schedule. Cash has zero P&L. The maker comparison uses one-share quotes and an eight-share inventory cap; the alpha strategy voluntarily uses a one-share maximum position, so risk exposures differ.

Training uses whole synthetic paths from seeds 100–104. Margin selection uses seeds 200–204. The model, margin, source hashes and validation scores are saved before seeds 3000–3049 are evaluated. Earlier development seeds and old market-making evaluation seeds are excluded from this fresh evaluation. The forecast stays fixed throughout evaluation.

This tests new paths from known scenario families. Every scenario family is represented during training and validation; there is no claim of generalization to an unseen market mechanism or a held-out real trading day.

The same seed can produce correlated paths across scenarios, including identical quiet and higher-cost market paths. The pooled profitable-fraction interval resamples whole seed clusters, carrying all eight scenarios together. It does not pretend all scenario/seed results are independent.

## Why this can work here

The synthetic exchange moves the reference price when a queue depletes. Current depth therefore helps predict price changes. The strategy monetizes that modeled relationship only when its estimated size exceeds costs. Passive makers suffer from buying before downward price moves and selling before upward ones; the new policy takes the predicted direction instead.

This mechanism is part of the simulator's construction. It is not evidence that the coefficients transfer to an exchange. Real data may contain competition, impact, cancellations, hidden liquidity and rapidly decaying signals that remove the edge. Latency and combined stress can still cause flat or losing results in the synthetic study. Read the complete [evaluation report](../reports/alpha/REPORT.md) before drawing conclusions about robustness.

## Code and reproduction

`src/lob_sim/alpha_strategy.py` contains the feature functions, ridge fit, depth-sweeping execution and trading state machine. `scripts/alpha_experiment.py` separates preparation from evaluation:

```bash
python scripts/alpha_experiment.py --stage prepare
python scripts/alpha_experiment.py --stage evaluate
```

The evaluation rejects a frozen policy if the implementation hashes have changed. For a small integration check, use `--events 200 --train-events 200 --train-seeds 2 --validation-seeds 2 --seeds 2 --output reports/alpha_smoke` with the default `--stage all`. A small smoke run is a functionality check, not the documented experiment.

Published source hashes use repository-relative paths and normalize CRLF line endings to LF. The original evaluation snapshots are retained as `frozen_policy.original.json` and `manifest.original.json`; the portable manifests record this metadata-only migration. The learned coefficients and result tables are identical.
