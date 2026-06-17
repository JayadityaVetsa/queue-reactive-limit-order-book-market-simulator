from pathlib import Path

from lob_sim.calibration import Calibrator, IntensityTable
from lob_sim.simulator import QueueReactiveSimulator, SimulationConfig
from lob_sim.types import EventType


def test_calibrator_returns_non_negative_rates(tmp_path: Path):
    sim = QueueReactiveSimulator(SimulationConfig(seed=4, duration=90, max_events=800)).run()
    table = Calibrator().fit(sim.events_df())

    for event_type in EventType:
        assert table.fallback_rates[event_type.value] > 0

    path = tmp_path / "params.json"
    table.to_json(path)
    loaded = IntensityTable.from_json(path)
    state = next(iter(table.rates))
    assert loaded.rate(state, EventType.LIMIT) > 0
