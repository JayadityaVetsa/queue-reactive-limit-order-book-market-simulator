"""Run an end-to-end simulation and write event/snapshot CSV files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lob_sim.simulator import QueueReactiveSimulator, SimulationConfig  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=int, default=25_000)
    parser.add_argument("--duration", type=float, default=600.0)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--outdir", default=str(ROOT / "data" / "processed"))
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    config = SimulationConfig(
        max_events=args.events,
        duration=args.duration,
        seed=args.seed,
    )
    sim = QueueReactiveSimulator(config).run()
    sim.events_df().to_csv(outdir / "simulation_events.csv", index=False)
    sim.snapshots_df().to_csv(outdir / "simulation_snapshots.csv", index=False)
    print(sim.statistics())


if __name__ == "__main__":
    main()
