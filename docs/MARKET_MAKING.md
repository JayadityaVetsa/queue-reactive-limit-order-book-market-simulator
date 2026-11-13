# Execution and research notes

The experiment asks whether inventory control improves outcomes after adverse selection and trading costs. `market_making.py` reuses the existing aggregate `OrderBook` to generate background flow; it adds shadow FIFO execution and a separate average-cost ledger. The old standalone `QueueTracker` remains available to existing users. It is not claimed to be integrated into the aggregate venue.

## Quote rule

Both policies quote five shares with a 40-share hard inventory cap. The baseline centers a fixed half-spread of 0.5 ticks on the observed mid. The inventory policy moves that center to `mid - skew * inventory`. Bid prices round downward and asks upward to the half-integer price grid, then clamp to the current same-side best so the decision remains passive. Replacements occur every five events. Quotes outside the visible ladder or crossing the opposite best on arrival are rejected. The hard cap and quoting schedule are shared controls, not advantages reserved for inventory management.

This is a deliberately simple inventory penalty, inspired by the reservation-price intuition in [Avellaneda and Stoikov](https://www.math.nyu.edu/~avellane/HighFrequencyTrading.pdf). It does not solve their stochastic control problem or claim their optimality result. The existing book follows a simplified [queue-reactive model](https://arxiv.org/abs/1312.0563); these experiments use synthetic intensities rather than an empirical calibration.

## Accounting

For signed quantity `dq`, execution price `p`, and fee `f` per share:

```
cash -= dq * p + abs(dq) * f
inventory += dq
equity = cash + inventory * mid
equity = realized_net_of_fees + inventory * (mid - average_entry)
```

Average entry is volume weighted on additions; reductions realize the difference; reversals reset the cost basis on the residual position. Fees enter realized P&L immediately. The terminal executable estimate subtracts `abs(inventory) * (0.5 + fee)`. It is an estimate with unlimited liquidation depth, not an actual exchange order. Drawdown is the maximum decline from a marked-equity high starting at zero.

## Why C++17 here

The C ABI primitive consumes eligible market quantity against queue ahead and then the resting order. It uses 64-bit integer quantities, caller-owned state, and no allocation. Python provides a readable reference, scenario generation, accounting, experiment orchestration and plotting. `ctypes` permits direct parity checks without a binding dependency.

This is a small native extension, not a native matching engine. Calling one primitive per event through `ctypes` may cost more than it saves. No throughput improvement is claimed. A useful next optimization would batch replay into native code after profiling. Pure C would also work for this primitive; C++ leaves room for an eventual price-time-priority engine without requiring a rewrite today.

Build with CMake, or directly on a MinGW-equipped Windows machine:

```powershell
g++ -std=c++17 -O2 -Wall -Wextra -Werror -shared native/execution.cpp -o execution.dll
$env:LOB_NATIVE = (Resolve-Path execution.dll)
python -m pytest tests/unit/test_market_making.py
python scripts/market_making_experiment.py --native execution.dll --output reports/native
```

On Linux use `-fPIC -shared` and `execution.so`; on macOS use `-dynamiclib` and `execution.dylib`. CMake writes the library under the build directory (possibly a configuration subdirectory). Pass its full path to `--native` and `LOB_NATIVE`.

## Reading this project in an interview

Start with the held-out table and one losing scenario. Trace a fill through better-price depth, queue ahead, latency, inventory and fees. Explain why a lower inventory path need not earn more. Then discuss which assumptions would need real data: cancel priority, informed flow, replenishment, impact and physical latency. These are research questions to defend, not evidence about a particular firm's internal infrastructure.

Probability calibration is deferred until the execution assumptions and market-making results have been reviewed. Adding a predictor now would make it harder to distinguish a quoting improvement from a modeling artifact.
