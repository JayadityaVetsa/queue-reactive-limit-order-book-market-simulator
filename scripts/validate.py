"""Validate a simulated run against a reference snapshot CSV."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lob_sim.validation import Validator  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulated", default=str(ROOT / "data" / "processed" / "simulation_snapshots.csv"))
    parser.add_argument("--empirical", default=str(ROOT / "data" / "processed" / "simulation_snapshots.csv"))
    args = parser.parse_args()

    result = Validator().compare_snapshots(
        pd.read_csv(args.simulated), pd.read_csv(args.empirical)
    )
    print(json.dumps({"passed": result.passed, "metrics": result.metrics}, indent=2))


if __name__ == "__main__":
    main()
