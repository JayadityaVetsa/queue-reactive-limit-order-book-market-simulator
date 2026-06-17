"""Synthetic data helpers used when public LOB data is unavailable."""

from __future__ import annotations

import pandas as pd

from lob_sim.simulator import QueueReactiveSimulator, SimulationConfig


def generate_sample_events(path: str, seed: int = 11, events: int = 2_500) -> pd.DataFrame:
    """Generate a reproducible queue-reactive sample event file."""

    config = SimulationConfig(seed=seed, max_events=events, duration=300.0)
    sim = QueueReactiveSimulator(config).run()
    df = sim.events_df()
    df.to_csv(path, index=False)
    return df
