from lob_sim.simulator import QueueReactiveSimulator, SimulationConfig


def test_depth_stays_positive_after_many_depletions():
    sim = QueueReactiveSimulator(
        SimulationConfig(seed=42, duration=300, max_events=5_000, initial_depth=25)
    ).run()
    snapshots = sim.snapshots_df()
    assert (snapshots["bid_depth"] > 0).all()
    assert (snapshots["ask_depth"] > 0).all()
    assert snapshots["imbalance"].between(-1, 1).all()
