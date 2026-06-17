from lob_sim.simulator import QueueReactiveSimulator, SimulationConfig


def test_spread_distribution_is_one_tick_in_queue_reactive_reference_model():
    sim = QueueReactiveSimulator(SimulationConfig(seed=9, duration=120, max_events=1_000)).run()
    snapshots = sim.snapshots_df()
    assert snapshots["spread_ticks"].nunique() == 1
    assert snapshots["spread_ticks"].iloc[0] == 1
