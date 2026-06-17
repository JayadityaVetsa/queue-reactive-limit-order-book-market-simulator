"""Command line interface for calibration, simulation, and validation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from lob_sim.calibration import Calibrator, IntensityTable
from lob_sim.simulator import QueueReactiveSimulator, SimulationConfig
from lob_sim.synthetic import generate_sample_events


def main() -> None:
    parser = argparse.ArgumentParser(prog="lob-sim")
    sub = parser.add_subparsers(dest="command", required=True)

    simulate = sub.add_parser("simulate", help="run a queue-reactive simulation")
    simulate.add_argument("--output", default="data/processed/simulation_events.csv")
    simulate.add_argument("--snapshots", default="data/processed/simulation_snapshots.csv")
    simulate.add_argument("--duration", type=float, default=600.0)
    simulate.add_argument("--max-events", type=int, default=25_000)
    simulate.add_argument("--seed", type=int, default=7)
    simulate.add_argument("--params")

    calibrate = sub.add_parser("calibrate", help="fit empirical intensities")
    calibrate.add_argument("--input", default="data/sample/sample_events.csv")
    calibrate.add_argument("--output", default="data/processed/intensities.json")

    sample = sub.add_parser("sample-data", help="generate synthetic sample events")
    sample.add_argument("--output", default="data/sample/sample_events.csv")
    sample.add_argument("--events", type=int, default=2_500)
    sample.add_argument("--seed", type=int, default=11)

    args = parser.parse_args()
    if args.command == "sample-data":
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        df = generate_sample_events(args.output, seed=args.seed, events=args.events)
        print(f"wrote {len(df)} events to {args.output}")
    elif args.command == "calibrate":
        df = Calibrator().load_csv(args.input)
        table = Calibrator().fit(df)
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        table.to_json(args.output)
        print(f"wrote intensities to {args.output}")
    elif args.command == "simulate":
        config = SimulationConfig(
            duration=args.duration, max_events=args.max_events, seed=args.seed
        )
        intensities = IntensityTable.from_json(args.params) if args.params else None
        sim = QueueReactiveSimulator(config, intensities).run()
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        sim.events_df().to_csv(args.output, index=False)
        sim.snapshots_df().to_csv(args.snapshots, index=False)
        print(json.dumps(sim.statistics(), indent=2))


if __name__ == "__main__":
    main()
