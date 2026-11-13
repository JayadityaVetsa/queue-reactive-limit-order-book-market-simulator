# Inventory control: held-out experiment

Selected skew: **0.1 ticks/share**. 20 held-out seeds per scenario; 4000 events per run.

The score was selected on seeds 10–14 using quiet, trend, and volatility scenarios. Seeds 1000–1019 were used during implementation debugging. Seeds 2000 onward were reserved for this final evaluation after those corrections. Stress scenarios were not used to tune the parameter.

P&L is in tick-shares. Terminal liquidation charges half a tick plus the scenario fee on remaining inventory. Differences below are paired by seed; intervals are mean ± 1.96 standard errors, approximate rather than exact confidence guarantees.

| Scenario | Fixed P&L | Inventory P&L | Paired difference ± 1.96 SE | Mean abs. inventory, fixed → inventory |
|---|---:|---:|---:|---:|
| quiet | -2566.1 | -2042.1 | +524.0 ± 590.5 | 19.4 → 5.0 |
| uptrend | -3541.5 | -2127.1 | +1414.4 ± 1136.4 | 20.2 → 5.2 |
| downtrend | -2904.1 | -2142.5 | +761.6 ± 674.3 | 19.3 → 5.3 |
| volatility_switch | -2677.1 | -2105.2 | +571.8 ± 437.6 | 20.2 → 5.4 |
| informed | -2345.2 | -2173.2 | +172.0 ± 401.3 | 19.7 → 5.2 |
| latency | -784.9 | -534.5 | +250.4 ± 347.9 | 18.3 → 13.8 |
| costs | -3285.6 | -2601.3 | +684.2 ± 586.4 | 19.4 → 5.0 |
| combined | -2148.6 | -1871.1 | +277.5 ± 869.2 | 18.2 → 17.1 |

## Reading the result

Positive average paired differences: combined, costs, downtrend, informed, latency, quiet, uptrend, volatility_switch.
Negative average paired differences: none.

The inventory policy underperformed the fixed policy in 52 of 160 paired runs. It had negative liquidation P&L in 152 of 160 runs. Reducing losses is not the same as establishing a profitable strategy.

Inventory control changes which trades execute. Lower inventory alone is not evidence of better returns: skew can surrender spread income, and it can sell too early into a rising market or buy into a falling one. Inspect fees, drawdown and signed ten-event markouts in summary.csv alongside P&L. Negative markout means the price moved against the passive fill, including the entry spread.

## Assumptions that can reverse the conclusion

This is a shadow-order experiment on synthetic flow. Quotes join behind displayed background depth. Market volume must clear better prices and queue ahead; touching a quote is insufficient. Cancellations receive no queue credit. Replacements lose priority. One replacement may be in flight; the previous quote remains executable until arrival. The inventory cap applies to both policies and is checked again at execution.

The background book replenishes mechanically. Volatility and drift additionally translate the reference ladder; informed flow is correlated with those subsequent moves. This mechanism is deliberately a stress test, not a fitted price model. The maker does not alter price formation or other traders' decisions. The eight-level ladder bounds eligible quote placement; terminal liquidation ignores depth and impact. Event latency has no calibrated mapping to microseconds. Drawdown uses marked equity before hypothetical terminal liquidation. No capital-based return or annualized Sharpe is reported.

## Reproduce and inspect

Run `python scripts/market_making_experiment.py` from the project root. Open comparison.html for interactive plots. runs.csv contains every evaluation result; tuning.csv contains every candidate; paired.csv preserves seed pairing; manifest.json records settings, tape digests, source hashes and versions. Path CSVs show the first held-out seed, not a selected best path. A selected skew of zero means tuning preferred the baseline; do not replace it to manufacture an improvement.
