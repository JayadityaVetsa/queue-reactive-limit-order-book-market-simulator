# Tasks: Queue-Reactive Limit Order Book Market Simulator

**Instructions**: Work through this list top to bottom. Each task is designed to be completed in 1–4 hours. Tags indicate the phase, type, and difficulty.

---

## Phase 1: Environment Setup, Data Acquisition, and Paper Reproduction (Weeks 1-2)

### Setup Tasks
- [ ] [setup] [easy] Initialize GitHub repository with README, .gitignore, and MIT license.
- [ ] [setup] [easy] Set up C++ development environment: install compiler (GCC 11+ or Clang 12+), CMake, and Git.
- [ ] [setup] [easy] Set up Python development environment: install Python 3.9+, pip, and virtualenv.
- [ ] [setup] [medium] Create virtual environment and install required Python packages: polars, numpy, scipy, pyarrow, pytest.
- [ ] [setup] [medium] Install Google Test framework for C++ unit testing.
- [ ] [setup] [easy] Initialize repository structure: create directories `src/`, `data/`, `docs/`, `scripts/`, `tests/`.
- [ ] [setup] [easy] Add a basic CMakeLists.txt file for building the core library.
- [ ] [setup] [easy] Add a pyproject.toml or requirements.txt for Python dependencies.
- [ ] [setup] [easy] Configure GitHub Actions CI workflow for building and testing.

### Data Acquisition Tasks
- [ ] [setup] [medium] Research and select a sample historical order book dataset (e.g., LOBSTER sample data for AAPL or MSFT).
- [ ] [setup] [medium] Write a script `scripts/download_sample_data.sh` to download and verify the sample dataset.
- [ ] [setup] [medium] Execute the download script and store the sample data in `data/sample/`.
- [ ] [setup] [medium] Examine the dataset format and document the schema in `docs/datasets.md`.

### Paper Reproduction Tasks
- [ ] [research] [medium] Read Cont et al. (2010) and note the key equations and results to reproduce (e.g., Figure 2: stationary distribution of bid-ask spread).
- [ ] [research] [easy] Write a Python script `scripts/reproduce_cont_2010.py` that loads the sample data and computes the empirical spread distribution.
- [ ] [research] [medium] Run the reproduction script and compare the output to the paper's figure (qualitative match within 10%).
- [ ] [research] [easy] Document any discrepancies and note potential reasons (data differences, calibration period).
- [ ] [research] [easy] Commit the reproduction script and results to the repository.

## Phase 2: Core Event Engine and Order Book State (Weeks 3-4)

### Order Book Implementation
- [ ] [impl] [medium] Define the `OrderBook` class in `src/core/order_book.hpp` with template parameter `K` (number of levels).
- [ ] [impl] [medium] Implement the constructor, destructor, and basic getters (midprice, spread, queue size).
- [ ] [impl] [medium] Implement `apply_limit_order(level, side, volume)` to add volume to the specified queue.
- [ ] [impl] [medium] Implement `apply_market_order(volume, side)` to walk the book and remove volume, returning executed volume and average price.
- [ ] [impl] [medium] Implement `apply_cancel(level, side, volume)` to remove volume from a specific queue.
- [ ] [impl] [medium] Add helper functions: `is_best_bid_empty()`, `is_best_ask_empty()`, `get_best_bid_level()`, `get_best_ask_level()`.
- [ ] [impl] [easy] Add bounds checking for level indices and throw exceptions on invalid input.

### Event Engine Implementation
- [ ] [impl] [medium] Define the `EventEngine` class in `src/core/event_engine.hpp`.
- [ ] [impl] [medium] Implement a priority queue (e.g., std::priority_queue) to store events sorted by timestamp.
- [ ] [impl] [medium] Define the `Event` struct with fields: timestamp, type, side, level, volume.
- [ ] [impl] [medium] Implement `schedule_event(timestamp, event, )` to insert an event into the queue.
- [ ] [impl] [medium] Implement `run_simulation(duration)` to process events until the simulation clock reaches `duration`.
- [ ] [impl] [medium] Implement `get_current_time()` and `clear()` methods.
- [ ] [impl] [easy] Ensure the engine is deterministic: no reliance on system clock or random number generation for event ordering.

### Unit Tests for Core
- [ ] [test] [medium] Write Google Test suite for `OrderBook`: test limit order application, market order execution, cancel operations.
- [ ] [test] [medium] Write Google Test suite for `EventEngine`: test event scheduling, FIFO processing, time advancement.
- [ ] [test] [medium] Implement a test fixture that provides a sample order book and event sequence.
- [ ] [test] [medium] Run the unit tests and ensure they pass.
- [ ] [test] [easy] Measure unit test coverage using gcov or similar; aim for >90% on core modules.

## Phase 3: Calibration Module and Empirical Validation Setup (Weeks 5-6)

### Calibrator Implementation
- [ ] [impl] [medium] Define the `Calibrator` class in `src/calibration/calibrator.hpp`.
- [ ] [impl] [medium] Implement the constructor that takes a discretization strategy (e.g., binning by total depth).
- [ ] [impl] [medium] Implement `fit(data)`: iterate over historical events, update counts \(N_i(q)\) and times \(T(q)\) for each state.
- [ ] [impl] [medium] Implement `save_parameters(path)` and `load_parameters(path)` using JSON serialization.
- [ ] [impl] [medium] Implement `get_intensity(event_type, state)` to return the estimated intensity.
- [ ] [impl] [easy] Add thread safety if needed (optional for Phase 3).

### State Discretization
- [ ] [impl] [medium] Design a state discretization function: map the full book state to a feature vector (e.g., [total_bid_depth, total_ask_depth, imbalance]).
- [ ] [impl] [medium] Implement binning or kernel density estimation to create a finite set of states.
- [ ] [impl] [easy] Ensure the discretization is reversible for simulation (store representative state for each bin).

### Validator Implementation
- [ ] [impl] [medium] Define the `Validator` class in `src/validation/validator.hpp` (create the validation directory).
- [ ] [impl] [medium] Implement `validate(simulator, empirical_data)`: run simulation with calibrated parameters and compute statistics.
- [ ] [impl] [medium] Implement statistic calculators: spread distribution, depth profile, queue depletion times, fill probability by position.
- [ ] [impl] [medium] Implement a report generator that outputs comparison plots and numerical summaries.
- [ ] [impl] [easy] Use existing Python plotting libraries (matplotlib, seaborn) for validation reports.

### Unit Tests for Calibration and Validation
- [ ] [test] [medium] Write unit tests for `Calibrator`: test that intensities are non-negative and sum to reasonable values.
- [ ] [test] [medium] Write unit tests for `Validator`: test that it returns a report with expected keys.
- [ ] [test] [medium] Create a small synthetic dataset for testing calibration accuracy.
- [ ] [test] [medium] Run the unit tests and ensure they pass.

## Phase 4: Matching Engine, Queue Tracking, and Price Move Logic (Weeks 7-8)

### Matching Engine Implementation
- [ ] [impl] [medium] Define the `MatchingEngine` class in `src/matching/matching_engine.hpp`.
- [ ] [impl] [medium] Implement `execute_market_order(volume, side)`: match against limit orders in the book, respecting price-time priority.
- [ ] [impl] [medium] Implement `execute_limit_order(price, volume, side)`: if price crosses the spread, execute immediately; otherwise, add to the book.
- [ ] [impl] [medium] Implement `get_best_bid()` and `get_best_ask()` returning price and volume.
- [ ] [impl] [easy] Handle edge cases: empty book, insufficient volume, self-trade prevention.

### Queue Tracker Implementation
- [ ] [impl] [medium] Define the `QueueTracker` class in `src/matching/queue_tracker.hpp`.
- [ ] [impl] [medium] Implement `insert_order(order_id, level, side, volume)`: add an order to the queue at the specified position.
- [ ] [impl] [medium] Implement `remove_order(order_id, level, side, volume)`: remove volume from a specific order's position.
- [ ] [impl] [medium] Implement `get_position(order_id)`: return the number of orders ahead of the given order.
- [ ] [impl] [medium] Implement `get_volume_ahead(level, side, position)`: return the total volume standing ahead.
- [ ] [impl] [easy] Ensure order IDs are unique and handle order modification (reduce volume) as a special case of remove and insert.

### Price Move Logic
- [ ] [impl] [medium] Integrate price move detection into the `OrderBook`: after each event, check if best bid or ask queue is empty.
- [ ] [impl] [medium] Implement tick size \(\delta\) as a configurable parameter.
- [ ] [impl] [medium] Update midprice when a price move occurs: \(S_{t+} = S_t \pm \delta\).
- [ ] [impl] [easy] Ensure price moves only happen when the respective queue is truly empty (volume zero).

### Unit Tests for Matching and Tracking
- [ ] [test] [medium] Write unit tests for `MatchingEngine`: test market order execution, limit order insertion, and cancellation interactions.
- [ ] [test] [medium] Write unit tests for `QueueTracker`: test insert, remove, position tracking, and volume ahead queries.
- [ ] [test] [medium] Create integration scenarios: simulate a sequence of limit orders, market orders, and cancels; verify expected fills and queue states.
- [ ] [test] [medium] Run the unit tests and ensure they pass.

## Phase 5: Integration, Testing, and Performance Benchmarking (Weeks 9-10)

### Integration Tasks
- [ ] [impl] [medium] Create a main simulation loop in `src/python/simulator.py` that ties together calibration, event generation, and core engine.
- [ ] [impl] [medium] Implement a configuration system (YAML/JSON) for simulator parameters (K, tick size, data paths, random seed).
- [ ] [impl] [medium] Ensure the simulator can run in two modes: calibration-only and simulation-with-validation.
- [ ] [impl] [easy] Add command-line interface (CLI) for running the simulator with optional arguments.
- [ ] [impl] [easy] Write a script `scripts/run_simulation.py` that demonstrates an end-to-end workflow.

### Testing Tasks
- [ ] [test] [medium] Expand unit test suite to cover integration scenarios (e.g., calibration → simulation → validation).
- [ ] [test] [medium] Write property-based tests (using hypothes.is or rapidcheck) for invariants like cash and inventory conservation.
- [ ] [test] [medium] Implement a test suite for the CLI scripts.
- [ ] [test] [medium] Run all tests and ensure they pass; measure overall coverage (>90% desired).

### Performance Benchmarking Tasks
- [ ] [test] [medium] Design a benchmark suite that measures events per second and latency.
- [ ] [impl] [medium] Implement instrumentation in the `EventEngine` to record processing times.
- [ ] [test] [medium] Run benchmarks on varying dataset sizes (10K, 100K, 1M events) and record results.
- [ ] [test] [medium] Identify bottlenecks using a profiler (e.g., gprof, perf, or valgrind).
- [ ] [impl] [medium] Optimize hotspots: consider cache-friendly data structures, minimize memory allocations, and use reserve() where applicable.
- [ ] [test] [medium] Re-run benchmarks after optimization and compare to targets (>500k events/sec).

### Release Preparation Tasks
- [ ] [impl] [easy] Tag the release candidate (e.g., v0.1.0) in GitHub.
- [ ] [impl] [easy] Create a release notes summary highlighting features and known limitations.
- [ ] [impl] [easy] Upload binaries or provide instructions for building from source.

## Phase 6: Documentation Polish and Final Benchmarking (Weeks 11-12)

### Documentation Tasks
- [ ] [docs] [easy] Update `README.md` with badges for build status, coverage, and license.
- [ ] [docs] [easy] Fill in the "Results and Benchmarks" section of `README.md` with actual numbers from Phase 5.
- [ ] [docs] [easy] Ensure `ARCHITECTURE.md` is complete and accurate.
- [ ] [docs] [easy] Ensure `TASKS.md` is complete and accurate.
- [ ] [docs] [easy] Ensure `RESEARCH.md` is complete and accurate.
- [ ] [docs] [easy] Ensure `DATASETS.md` is complete and accurate (see next file).
- [ ] [docs] [easy] Add a `CONTRIBUTING.md` file with guidelines for contributors.
- [ ] [docs] [easy] Add a `CODE_OF_CONDUCT.md` file.
- [ ] [docs] [easy] Set up GitHub Issues and Pull Request templates.

### Final Validation Tasks
- [ ] [test] [medium] Run the final validation suite on a larger, out-of-sample dataset.
- [ ] [test] [medium] Generate a validation report comparing simulated vs. empirical statistics (spread, depth, fill probability, price move impact).
- [ ] [test] [medium] Ensure that key metrics are within 10% of empirical values (as per success criteria).
- [ ] [test] [easy] Document any deviations and note potential improvements in `README.md`.

### Cleanup and Finalization Tasks
- [ ] [docs] [easy] Remove any temporary or debug files from the repository.
- [ ] [impl] [easy] Ensure all code is formatted consistently (run clang-format or black).
- [ ] [impl] [easy] Run a final linting check (cppcheck, pylint) and fix warnings.
- [ ] [impl] [easy] Verify that the repository builds and passes tests on a clean environment (e.g., GitHub Actions).
- [ ] [docs] [easy] Announce the release on relevant platforms (e.g., Reddit r/algotrading, QuantStack Exchange).

```

# End of TASKS.md
