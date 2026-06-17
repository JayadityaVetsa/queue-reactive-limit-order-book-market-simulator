"""Calibrate queue-reactive intensities from event CSV data."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lob_sim.calibration import Calibrator  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(ROOT / "data" / "sample" / "sample_events.csv"))
    parser.add_argument("--output", default=str(ROOT / "data" / "processed" / "intensities.json"))
    args = parser.parse_args()

    calibrator = Calibrator()
    table = calibrator.fit(calibrator.load_csv(args.input))
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    table.to_json(args.output)
    print(f"wrote calibrated intensities to {args.output}")


if __name__ == "__main__":
    main()
