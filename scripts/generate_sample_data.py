"""Generate a small deterministic synthetic event sample for CI and demos."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lob_sim.synthetic import generate_sample_events  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(ROOT / "data" / "sample" / "sample_events.csv"))
    parser.add_argument("--events", type=int, default=2_500)
    parser.add_argument("--seed", type=int, default=11)
    args = parser.parse_args()
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    df = generate_sample_events(args.output, seed=args.seed, events=args.events)
    print(f"wrote {len(df)} events to {args.output}")


if __name__ == "__main__":
    main()
