from lob_sim.simulator import QueueReactiveSimulator, SimulationConfig


def test_simulator_is_deterministic_under_fixed_seed():
    config = SimulationConfig(seed=123, duration=120, max_events=1_000)
    first = QueueReactiveSimulator(config).run()
    second = QueueReactiveSimulator(config).run()

    assert first.events_df().equals(second.events_df())
    assert first.snapshots_df().equals(second.snapshots_df())


def test_simulator_produces_usable_statistics():
    sim = QueueReactiveSimulator(SimulationConfig(duration=60, max_events=500)).run()
    stats = sim.statistics()
    assert stats["events"] > 0
    assert stats["mean_bid_depth"] > 0
    assert stats["mean_ask_depth"] > 0
    assert "final_midprice" in stats


def test_repeated_run_resets_state_and_stays_inside_horizon():
    sim = QueueReactiveSimulator(SimulationConfig(seed=5, duration=0.1, max_events=1000))
    first = sim.run().snapshots_df().copy()
    assert first.timestamp.max() <= 0.1
    assert sim.run().snapshots_df().equals(first)
