"""Benchmark the Python queue-reactive simulation loop."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lob_sim.simulator import QueueReactiveSimulator, SimulationConfig  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=int, default=100_000)
    args = parser.parse_args()
    config = SimulationConfig(
        seed=99,
        duration=1e9,
        max_events=args.events,
        sample_every=max(1_000, args.events // 100),
    )
    start = time.perf_counter()
    sim = QueueReactiveSimulator(config).run()
    elapsed = time.perf_counter() - start
    eps = len(sim.events) / elapsed
    print(
        {
            "events": len(sim.events),
            "seconds": round(elapsed, 4),
            "events_per_second": round(eps),
        }
    )


if __name__ == "__main__":
    main()
