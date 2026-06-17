# Data Sources: Queue-Reactive Limit Order Book Market Simulator

This document details the data sources required for calibrating, validating, and testing the limit order book simulator. It includes primary sources for historical order book data, secondary sources for reference prices and metadata, and fallback strategies for synthetic data generation.

---

## 1. Primary Data Sources

### 1.1 LOBSTER Data
**Description**:  
LOBSTER (Limit Order Book Reconstruction System) provides reconstructed limit order book data for various US equities and futures. The data includes every order book event (limit orders, market orders, cancellations) with timestamps at the nanosecond level, along with the resulting best bid and ask prices and sizes.

**What It Contains**:  
- Message files: chronological list of events (type, side, price, volume).  
- Order book files: snapshots of the best bid and ask levels at each event.  
- Optional: executed trades and directional changes.

**Where to Get It**:  
- Official website: [https://lobster.wiwi.hu-berlin.de](https://lobster.wiwi.huwi.hu-berlin.de)  
- Direct download (requires registration): [https://lobster.wiwi.hu-berlin.de/data](https://lobster.wiwi.hu-berlin.de/data)  
- Sample data (free for research): [https://lobster.wiwi.hu-berlin.de/sampledata](https://lobster.wiwi.hu-berlin.de/sampledata)

**Format**:  
- CSV files with no header. Columns vary by file type:  
  - `YYYYMMDD_MSGBK_XX.txt`: `[time, type, side, price, volume]`  
    - `time`: seconds since midnight (integer, multiply by 10^9 for nanoseconds if needed).  
    - `type`: 1=limit order, 2=market order, 3=cancel, 4=limit order that could not be fully executed (i.e., partially executed and then canceled), 5=market order that could not be fully executed (i.e., partially executed), etc. (see LOBSTER documentation for full codes).  
    - `side`: 1=bid (buy), 2=ask (sell).  
    - `price`: price level as an integer (number of ticks from a reference).  
    - `volume`: number of shares (or contracts, depending on the asset).  
  - `YYYYMMDD_OBBOOK_XX.txt`: `[time, bid_price_1, bid_vol_1, ..., ask_price_1, ask_vol_1, ...]` for multiple levels.

**Size**:  
- One day of data for a liquid stock (e.g., AAPL) is approximately 1-2 GB for message files and similar for order book files.  
- Sample data is much smaller (a few MB).

**Licensing**:  
- LOBSTER data is free for academic research upon registration. Commercial use requires a license.  
- For this project, we assume academic/research use. Check the LOBSTER data use agreement for details.

**How to Parse It**:  
- Use the provided Python scripts in the `scripts/` directory (see `download_data.sh` and `calibrate.py`).  
- Parse using `pandas.read_csv` with no header and assign column names.  
- Convert timestamps to datetime objects if needed for analysis.  
- Filter to regular trading hours (e.g., 9:30 AM to 4:00 PM EST) to avoid overnight gaps.

**Known Quirks and Preprocessing Steps**:  
- LOBSTER uses a reference price; the actual price is `reference_price + (price_level * tick_size)`. The reference price and tick size are provided in the metadata.  
- Some event types (4, 5) represent partial executions; treat them as limit orders that could not be fully executed (type 4) or market orders that could not be fully executed (type 5).  
- Data may contain out-of-sequence timestamps due to exchange delays; sort by timestamp before processing.  
- Remove events with invalid prices or volumes (e.g., zero or negative).  
- Aggregate multiple events at the same timestamp if necessary (though LOBSTER guarantees uniqueness).

### 1.2 Kaggle Limit Order Book Datasets
**Description**:  
Kaggle hosts several limit order book datasets, often derived from LOBSTER or other sources, suitable for machine learning and simulation testing.

**What It Contains**:  
- Similar to LOBSTER: event-level data or aggregated order book snapshots.  
- May include additional features like volume imbalance, order flow toxicity, etc.

**Where to Get It**:  
- Kaggle website: [https://www.kaggle.com](https://www.kaggle.com)  
- Search for "limit order book" or "LOBSTER".  
- Example dataset: [https://www.kaggle.com/datasets/shayanfh/stock-limit-order-book-data](https://www.kaggle.com/datasets/shayanfh/stock-limit-order-book-data) (AAPL 2014)

**Format**:  
- Typically CSV files with headers. Columns may include: `timestamp`, `event_type`, `side`, `price`, `volume`, `bid_price_1`, `bid_vol_1`, `ask_price_1`, `ask_vol_1`, etc.

**Size**:  
- Varies; sample datasets are often 10-100 MB for ease of use on Kaggle.

**Licensing**:  
- Varies by dataset; many are released under CC0 or CC-BY licenses for academic use. Check the specific dataset license.

**How to Parse It**:  
- Load with `pandas.read_csv` (header present).  
- Map column names to a unified schema.  
- Convert timestamps to datetime.

**Known Quirks and Preprocessing Steps**:  
- May require renaming columns to match the expected schema.  
- Ensure timestamp format is consistent (e.g., UNIX milliseconds vs. string).  
- Check for missing values and handle appropriately (e.g., forward fill or drop).  
- Verify that price levels correspond to the correct tick size.

### 1.3 NASDAQ TotalView-ITCH / ITCH 5.0
**Description**:  
NASDAQ provides the ITCH protocol, a binary feed that contains all orders, executions, and messages for NASDAQ-listed securities. TotalView-ITCH is the historical product.

**What It Contains**:  
- Every event: order add, order delete, order replace, order execute, trade, cross, etc.  
- Timestamped to the nanosecond.

**Where to Get It**:  
- NASDAQ Historical Data Products: [https://www.nasdaq.com/solutions/nordic-historical-data](https://www.nasdaq.com/solutions/nordic-historical-data)  
- Requires a commercial subscription; not free.  
- Sample files may be available for research purposes via academic partnerships.

**Format**:  
- Binary packets; each message starts with a length byte and a message type byte.  
- Detailed specification: [NASDAQ ITCH 5.0 Specification](https://www.nasdaq.com/documents/itch5.0.pdf)

**Size**:  
- One day of data for a single symbol can be several GB.

**Licensing**:  
- Commercial license required for use.  
- Not suitable for open-source projects without permission.

**How to Parse It**:  
- Use a binary parser (e.g., `construct` library in Python or custom C++ code).  
- Parse each message type according to the specification.  
- Convert to a canonical event format (limit order, market order, cancel) for the simulator.

**Known Quirks and Preprocessing Steps**:  
- ITCH includes many message types; only a subset are needed for the simulator (add, delete, execute, trade).  
- Orders can be modified (replace) rather than cancelled and re-submitted; handle replaces as a delete followed by an add.  
- Cross trades and opening/closing auctions may require special handling.  
- Refer to the ITCH specification for detailed field definitions.

### 1.4 Synthetic Data (Fallback Strategy)
**Description**:  
If obtaining real historical data is prohibitive due to cost, licensing, or availability, synthetic data can be generated using calibrated parameters from a known model or by simulating from the queue-reactive model itself.

**What It Contains**:  
- Artificially generated limit order book events that mimic statistical properties of real data (e.g., spread distribution, depth profile, order flow intensities).

**Where to Get It**:  
- Generated in-house using the simulator's calibration and simulation modules.  
- Alternative: use open-source simulators like `lox` or `gobster` to generate synthetic LOB data.

**Format**:  
- Same as real data: CSV files with columns `[timestamp, type, side, price, volume]`.

**Size**:  
- Arbitrary; can be scaled to desired length (e.g., 1 million events for testing).

**Licensing**:  
- Generated data inherits the license of the simulator (MIT or Apache 2.0).  
- No external licensing concerns.

**How to Parse It**:  
- Same as real data; no special parsing needed.

**Known Quirks and Preprocessing Steps**:  
- Synthetic data may not capture all nuances of real market microstructure (e.g., order flow correlation, news impacts).  
- Validate synthetic data against known stylized facts before using for calibration.  
- Use synthetic data primarily for algorithm development and testing; validate final results on real data if possible.

---

## 2. Secondary Data Sources

### 2.1 Reference Prices and Market Data
**Description**:  
For validating price dynamics, reference prices such as the midprice from the consolidated tape or the national best bid and offer (NBBO) can be useful.

**What It Contains**:  
- Timestamped best bid and ask prices and volumes from all exchanges (NBBO).  
- Trades and quotes.

**Where to Get It**:  
- WRDS (Wharton Research Data Services): [https://wrds-www.wharton.upenn.edu](https://wrds-www.wharton.upenn.edu) (requires subscription)  
- Polygon.io: [https://polygon.io](https://polygon.io) (free tier available)  
- Tiingo: [https://www.tiingo.com](https://www.tiingo.com) (free tier available)  
- IEX Cloud: [https://iexcloud.io](https://iexcloud.io) (free tier available)

**Format**:  
- CSV or JSON via API.  
- Columns: `timestamp`, `bid_price`, `bid_size`, `ask_price`, `ask_size`.

**Size**:  
- Varies; one day of NBBO data for a single symbol is approximately 10-50 MB.

**Licensing**:  
- Varies by provider; check terms of service.  
- Free tiers often have rate limits and delayed data.

**How to Parse It**:  
- Load via API client library or download CSV.  
- Align timestamps with order book data for validation.

**Known Quirks and Preprocessing Steps**:  
- NBBO updates only when the best bid or ask changes; may need to fill forward for simulation timestamps.  
- Ensure timestamp timezone consistency (usually UTC or EST).  
- Filter to regular trading hours.

### 2.2 Reference Data: Tick Size and Lot Size
**Description**:  
Knowing the tick size (minimum price increment) and lot size (minimum trade size) is essential for realistic simulation.

**What It Contains**:  
- Exchange-specific trading rules.

**Where to Get It**:  
- Exchange websites:  
  - NASDAQ: [https://www.nasdaq.com/market-stocks/stock-screening](https://www.nasdaq.com/market-stocks/stock-screening)  
  - NYSE: [https://www.nyse.com/markets/hours-calendars]  
  - Alternatively, use financial data providers like Bloomberg or Reuters (subscription required).

**Format**:  
- Typically documented in PDF guides or available via API.

**Size**:  
- Negligible (a few KB per symbol).

**Licensing**:  
- Publicly available information; free to use.

**How to Parse It**:  
- Manual entry or scrape from exchange websites (if allowed).  
- Store in a configuration file (e.g., `config/instrument_specs.yaml`).

**Known Quirks and Preprocessing Steps**:  
- Tick size may vary by price level (e.g., sub-penny pricing for certain stocks).  
- Lot size may be 100 shares (round lot) but odd lots are allowed.  
- For simplicity, assume a constant tick size (e.g., $0.01) and lot size of 1 share; adjust as needed for specific assets.

---

## 3. Data Acquisition and Preprocessing Scripts

The repository includes helper scripts in the `scripts/` directory to streamline data acquisition and preprocessing:

- `scripts/download_data.sh`:  
  - Downloads sample data from LOBSTER or Kaggle (configurable via arguments).  
  - Verifies file integrity using checksums (if provided).  
  - Extracts archives if necessary.

- `scripts/preprocess_data.py`:  
  - Loads raw data files (LOBSTER message and order book files).  
  - Converts to a unified CSV format with columns: `[timestamp, event_type, side, price, volume]`.  
  - Filters to regular trading hours (configurable start and end times).  
  - Removes invalid entries (negative prices/volumes, out-of-range timestamps).  
  - Saves processed data to `data/processed/` for use by the calibration and validation modules.

- `scripts/validate_data.py`:  
  - Checks the processed data for basic properties:  
    - Monotonic timestamps (after sorting).  
    - Event type distribution.  
    - Price levels within expected range.  
    - Volume statistics.  
  - Generates a summary report (HTML or PDF) for quick inspection.

### How to Use the Scripts
1. Run `./scripts/download_data.sh --symbol AAPL --date 2024-01-02` to download a day of LOBSTER sample data for AAPL.  
2. Run `python scripts/preprocess_data.py --input data/sample/ --output data/processed/` to convert the raw data.  
3. Run `python scripts/validate_data.py --input data/processed/` to inspect the data quality.  
4. Use the processed data in `data/processed/` as input to the calibration module (`scripts/calibrate.py`).

---

## 4. Data Storage Recommendations

- **Raw Data**: Store in `data/raw/` (not tracked by Git due to size).  
- **Processed Data**: Store in `data/processed/` (can be large; consider using Git LFS if changes are frequent, but typically treat as immutable).  
- **Calibrated Parameters**: Store in `data/processed/` as JSON files (small, safe to track in Git).  
- **Sample Data for CI**: Keep a small subset (e.g., 10K events) in `data/sample/` for continuous integration testing (safe to track in Git).

---

## 5. Summary of Recommended Workflow

1. **Acquire Data**: Download a sample dataset from LOBSTER or Kaggle using `scripts/download_data.sh`.  
2. **Preprocess**: Convert to unified format and filter using `scripts/preprocess_data.py`.  
3. **Validate Quality**: Run `scripts/validate_data.py` to ensure data integrity.  
4. **Calibrate**: Estimate intensities using `scripts/calibrate.py` on the processed data.  
5. **Validate Simulation**: Run the simulator with calibrated parameters and compare to empirical statistics using `scripts/validate.py`.  
6. **Iterate**: If validation fails, revisit preprocessing or consider alternative data sources or augmentation techniques.

---

## 6. Fallback Strategy for Limited Free Data

If acquiring real data is not possible:

1. **Use Public Sample Data**: LOBSTER provides free sample data for several symbols (e.g., AAPL, MSFT) for one day. This is sufficient for development and testing.  
2. **Generate Synthetic Data**: Use the simulator itself to generate synthetic data:  
   - Assume a simple intensity model (e.g., constant intensities or linear in depth).  
   - Simulate a long sequence of events.  
   - Use this synthetic data to calibrate and validate—this serves as a sanity check for the simulator's internal consistency.  
3. **Leverage Open-Source Implementations**: Refer to open-source limit order book simulators (e.g., `lox`, `gobster`, `quantyst`) for example datasets and validation procedures.  
4. **Approach Academic Collaborators**: Reach out to university labs or research groups that may share data for non-commercial projects.

*Note: Always validate the simulator on real data before drawing conclusions about its effectiveness in live markets. Synthetic data is useful for development but may not capture all market microstructure complexities.*
