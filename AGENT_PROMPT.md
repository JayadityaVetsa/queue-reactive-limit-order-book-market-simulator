# Agent Prompt: Implement Queue-Reactive Limit Order Book Market Simulator

You are an expert software engineer tasked with building a high-fidelity limit order book simulator from scratch. Your goal is to produce a production-quality, well-tested, and documented simulator that meets the success criteria outlined in the project documentation. You must work autonomously, following the instructions below exactly. You have access to the file system and can read/write files, but you must not ask for clarification—you must proceed based on the information provided in this prompt and the files you create.

---

## 🎯 Project Goal

Build a calibrated event-driven limit order book simulator with queue position, order arrivals, cancellations, market orders, partial fills, and empirical validation against order book data.

The simulator must:
- Maintain a multi-level limit order book.
- Process limit orders, market orders, and cancellations.
- Track queue position and partial fills.
- Simulate price moves when best bid or ask queues deplete.
- Calibrate event intensities from historical order book events.
- Validate simulated market statistics against empirical statistics.
- Be deterministic under a fixed seed.
- Pass empirical validation tests (simulated statistics within 10% of empirical values for key metrics).
- Achieve a simulation throughput of >500,000 events per second on a modern CPU.

---

## 📁 Repository Structure

You must create the following directory and file structure. **Do not deviate from this structure.** Create all directories and empty files as placeholders first, then fill them in.

queue-reactive-lob-simulator/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.yml
│   │   └── feature_request.yml
│   └── PULL_REQUEST_TEMPLATE/
│       └── pr_template.md
├── data/
│   ├── raw/
│   ├── processed/
│   └── sample/
├── docs/
│   ├── architecture.md
│   ├── datasets.md
│   ├── plan.md
│   ├── research.md
│   └── tasks.md
├── scripts/
│   ├── calibrate.py
│   ├── validate.py
│   └── download_data.sh
├── src/
│   ├── core/
│   │   ├── order_book.hpp
│   │   ├── event_engine.hpp
│   │   ├── types.hpp
│   │   └── utils.hpp
│   ├── calibration/
│   │   ├── calibrator.cpp
│   │   ├── calibrator.hpp
│   │   └── calibrator_py.cpp
│   ├── matching/
│   │   ├── matching_engine.cpp
│   │   ├── matching_engine.hpp
│   │   ├── queue_tracker.cpp
│   │   └── queue_tracker.hpp
│   ├── python/
│   │   ├── __init__.py
│   │   ├── calibrator.py
│   │   ├── simulator.py
│   │   └── validator.py
│   └── utils/
│       ├── logger.hpp
│   │   └── config_parser.hpp
├── tests/
│   ├── unit/
│   │   ├── test_order_book.cpp
│   │   ├── test_event_engine.cpp
│   │   └── test_calibrator.cpp
│   ├── integration/
│   │   ├── test_simulation_loop.cpp
│   │   └── test_calibration_validation.py
│   └── empirical/
│       ├── test_spread_distribution.py
│   │   └── test_depth_profile.py
├── .gitignore
├── CMakeLists.txt
├── LICENSE
├── README.md
└── pyproject.toml

*Note*: If you choose to implement the core in Rust instead of C++, adjust the file extensions accordingly (`.rs` instead of `.cpp`/`.hpp`) and replace `CMakeLists.txt` with `Cargo.toml`. The Python layer and structure should remain similar.

---

## 🛠️ Coding Standards and Practices

### Language Choice
- **Core Engine**: Implement in **modern C++20** (or Rust 2021 edition if you prefer). Justify your choice in a comment at the top of `src/core/order_book.hpp` (or `src/core/order_book.rs`).  
  - *Recommended*: C++20 for performance and ease of pybind11 integration.
- **Research Layer**: **Python 3.9+** for calibration, validation, and scripting.

### Style and Formatting
- **C++**: Follow the Google C++ Style Guide. Use `clang-format` to format all `.cpp` and `.hpp` files.
- **Python**: Follow PEP 8. Use `black` and `flake8` to format all `.py` files.
- **Shell Scripts**: Follow Google Shell Style Guide.
- **Markdown**: Use consistent heading levels and fenced code blocks with language tags.

### Dependency Management
- Use **CMake** for building the C++ core and running tests.
- Use **pip** and `pyproject.toml` or `requirements.txt` for Python dependencies.
- List all dependencies in the respective files.

### Testing Framework
- **C++ Unit Tests**: Google Test (gtest). Write tests in the `tests/unit/` directory.
- **Python Unit Tests**: pytest. Write tests in the `tests/` directory (both unit and empirical can be in Python).
- **Test Coverage**: Aim for >90% coverage on core modules (OrderBook, EventEngine, MatchingEngine) and >80% on calibration and validation.

### Documentation
- Every non-trivial function, class, and file must have a comment explaining its purpose and usage.
- Use Doxygen-style comments for C++ (`/** ... */`) and docstrings for Python (`""" ... """`).
- Keep `README.md` updated with badges, installation instructions, and usage examples.

### Version Control
- Commit frequently with meaningful messages.
- Use a `.gitignore` file to exclude build artifacts, temporary files, and large data files.
- Never commit large raw data files (>10 MB); keep them in `data/raw/` and reference them via scripts.

---

## 🔧 Implementation Order

You **must** follow this order strictly. Do not skip ahead. Each step builds on the previous one.

### Step 0: Initialize the Repository
1. Create the directory structure listed above (all directories and empty placeholder files).
2. Initialize a Git repository: `git init`.
3. Create a `.gitignore` file with appropriate exclusions (e.g., `build/`, `*.o`, `*.pyc`, `data/raw/*`, `Doxyfile`, `__pycache__/`).
4. Write a basic `README.md` with project title and one-line description.
5. Commit: `git commit -m "Initialize repository structure"`.

### Step 1: Set Up Development Environment (Document in README)
1. Install required tools: C++ compiler (GCC 11+ or Clang 12+), CMake, Python 3.9+, pip, Google Test.
2. Create a Python virtual environment and install required packages: `polars`, `numpy`, `scipy`, `pyarrow`, `pytest`.
3. Update `README.md` with installation instructions.
4. Commit: `git commit -m "Document environment setup"`.

### Step 2: Acquire and Preprocess Sample Data
1. Use `scripts/download_data.sh` to download a sample LOBSTER dataset (e.g., AAPL for one day).
2. Write `scripts/preprocess_data.py` to convert raw data to a unified CSV format.
3. Write `scripts/validate_data.py` to check data quality.
4. Run the preprocessing and validation scripts on the sample data.
5. Commit: `git commit -m "Add data acquisition and preprocessing scripts"`.

### Step 3: Implement Core Order Book
1. Define `OrderBook` class in `src/core/order_book.hpp` with template parameter `K`.
2. Implement constructor, getters (midprice, spread, queue size), and basic modifiers (`apply_limit_order`, `apply_market_order`, `apply_cancel`).
3. Add bounds checking and error handling.
4. Write unit tests in `tests/unit/test_order_book.cpp`.
5. Run the tests and ensure they pass.
6. Commit: `git commit -m "Implement core OrderBook class"`.

### Step 4: Implement Event Engine
1. Define `EventEngine` class in `src/core/event_engine.hpp`.
2. Implement a priority queue for events, `schedule_event`, `run_simulation`, `get_current_time`, and `clear`.
3. Ensure deterministic processing (FIFO for same timestamp).
4. Write unit tests in `tests/unit/test_event_engine.cpp`.
5. Run the tests and ensure they pass.
6. Commit: `git commit -m "Implement EventEngine class"`.

### Step 5: Implement Calibration Module
1. Define `Calibrator` class in `src/calibration/calibrator.hpp`.
2. Implement `fit(data)` to compute empirical intensities \(\hat{\lambda}_i(q) = N_i(q) / T(q)\).
3. Implement `save_parameters` and `load_parameters` (JSON format).
4. Write unit tests in `tests/unit/test_calibrator.cpp`.
5. Run the tests and ensure they pass.
6. Commit: `git commit -m "Implement Calibrator class"`.

### Step 6: Implement Matching Engine and Queue Tracker
1. Define `MatchingEngine` class in `src/matching/matching_engine.hpp`.
2. Implement `execute_market_order(volume, side)`: match against limit orders in the book, respecting price-time priority.
3. Implement `execute_limit_order(price, volume, side)`: if price crosses the spread, execute immediately; otherwise, add to the book.
4. Define `QueueTracker` class in `src/matching/queue_tracker.hpp`.
5. Implement `insert_order(order_id, level, side, volume)`: add an order to the queue at the specified level and side.
6. Implement `remove_order(order_id, level, side, volume)`: remove volume from a specific order's position.
7. Implement `get_position(order_id)`: return the number of orders ahead of the given order.
8. Implement `get_volume_ahead(level, side, position)`: return the total volume standing ahead.
9. Write unit tests in `tests/unit/test_matching_engine.cpp` and `tests/unit/test_queue_tracker.cpp`.
10. Run the tests and ensure they pass.
11. Commit: `git commit -m "Implement MatchingEngine and QueueTracker"`.

### Step 7: Add Price Move Logic
1. Modify `OrderBook` to detect when best bid or ask queue is empty after an event.
2. Implement price move by \(\pm \delta\) (tick size) when a queue depletes.
3. Ensure midprice updates correctly.
4. Add unit tests for price move scenarios.
5. Commit: `git commit -m "Add price move logic on queue depletion"`.

### Step 8: Build Integration Layer (Python)
1. Implement `src/python/simulator.py` as a high-level interface to run simulations.
2. Implement `src/python/calibrator.py` and `src/python/validator.py` as wrappers for the C++ modules.
3. Expose the C++ core to Python using pybind11 (see `src/core/calibrator_py.cpp` as an example; you will need to create similar bindings for the order book and event engine).
   - *Alternative*: If using Rust, use `rust-cpython` or `PyO3`.
4. Write unit tests for the Python wrappers.
5. Commit: `git commit -m "Add Python research layer with pybind11 bindings"`.

### Step 9: Implement Validation and Reporting
1. Define `Validator` class in `src/validation/validator.hpp` (create the directory).
2. Implement statistic calculators: spread distribution, depth profile, queue depletion times, fill probability by position.
3. Implement a report generator that outputs numerical summaries and plots (use matplotlib in Python).
4. Write unit tests for the validator.
5. Commit: `git commit -m "Implement Validator class and reporting"`.

### Step 10: Create End-to-End Workflow Scripts
1. Write `scripts/calibrate.py`: loads data, runs calibration, saves parameters.
2. Write `scripts/validate.py`: loads data and calibrated parameters, runs simulation, computes statistics, generates validation report.
3. Ensure the scripts work end-to-end on the sample data.
4. Commit: `git commit -m "Add end-to-end calibration and validation scripts"`.

### Step 11: Performance Benchmarking and Optimization
1. Build the simulator in Release mode (`-DCMAKE_BUILD_TYPE=Release`).
2. Write a simple benchmark that times the processing of 1 million events.
3. Identify bottlenecks using a profiler (e.g., `perf`, `gprof`, or Visual Studio Profiler).
4. Optimize hotspots: consider cache-friendly data structures, minimize allocations, and use `reserve()` where applicable.
5. Re-run benchmarks and ensure throughput >500,000 events per second.
6. Commit: `git commit -m "Optimize for performance; achieve >500k events/sec"`.

### Step 12: Write Comprehensive Unit and Integration Tests
1. Write integration tests in `tests/integration/` that test the full workflow: calibration → simulation → validation.
2. Write empirical validation tests in `tests/empirical/` that compare simulator output to real data (use the sample data for now).
3. Ensure all tests pass and measure coverage (>90% desired).
4. Commit: `git commit -m "Add integration and empirical validation tests"`.

### Step 13: Finalize Documentation
1. Update `README.md` with:
   - Badges for build status, test coverage, and license.
   - Clear installation instructions.
   - Usage examples (C++ and Python).
   - Results and benchmarks section (fill with actual numbers from Step 11).
2. Ensure `ARCHITECTURE.md`, `DATASETS.md`, `PLAN.md`, `RESEARCH.md`, and `TASKS.md` are complete and accurate.
3. Add `CONTRIBUTING.md` and `CODE_OF_CONDUCT.md`.
4. Set up GitHub Actions CI workflow (`.github/workflows/ci.yml`) that builds, tests, and validates on push.
5. Commit: `git commit -m "Finalize documentation and add CI"`.

### Step 14: Release Preparation
1. Tag the release: `git tag v0.1.0`.
2. Write release notes summarizing features and known limitations.
3. Ensure the repository is ready for public consumption.
4. Commit: `git commit -m "Prepare release v0.1.0"`.

---

## 🧱 What to Do When Stuck

If you encounter a problem you cannot solve after 30 minutes of effort:

1. **Consult the Documentation**: Re-read the relevant sections of `ARCHITECTURE.md`, `PLAN.md`, and `RESEARCH.md`.
2. **Check the Code**: Look for similar implementations in the codebase you’ve already written.
3. **Write a Test First**: Sometimes writing a failing test clarifies the expected behavior.
4. **Isolate the Problem**: Create a minimal reproducible example (MRE) in a separate file.
5. **Try a Different Approach**: If one method isn’t working, consider an alternative design (e.g., swapping a linked list for a vector).
6. **Use Rubber Duck Debugging**: Explain the problem out loud or in writing.
7. **If Still Stuck**: Make a reasonable assumption, document it as a TODO or FIXME comment, and move on to the next task. You can return to it later with fresh eyes.

**Never** leave a task incomplete due to being stuck without documenting your assumption and moving forward.

---

## ✅ Verification Criteria

Before considering the project complete, you must verify the following:

1. **Code Quality**: All code is formatted, linted, and free of obvious errors.
2. **Tests Pass**: All unit, integration, and empirical validation tests pass.
3. **Performance**: The simulator achieves >500,000 events per second on a modern CPU (measure and record the result).
4. **Determinism**: Two runs with the same seed and data produce identical output.
5. **Validation**: Simulated statistics (spread distribution, depth profile, etc.) are within 10% of empirical values on the sample data.
6. **Documentation**: All required `.md` files are present and complete.
7. **Repository Structure**: Matches the structure described in this prompt exactly.
8. **No Placeholders**: No file contains `[TBD]`, `TODO`, or `FIXME` without a clear plan to address it (except for expected future work documented in `README.md`).

---

## 🚀 Final Instructions

Begin by creating the directory structure and initializing the Git repository. Then, follow the implementation order step by step. Do not skip steps. Work steadily and commit frequently. When you have completed Step 14, you have successfully built the simulator.

Good luck, and happy coding!
