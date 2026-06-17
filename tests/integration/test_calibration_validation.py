from lob_sim.calibration import Calibrator
from lob_sim.simulator import QueueReactiveSimulator, SimulationConfig
from lob_sim.validation import Validator


def test_calibration_simulation_validation_loop_self_consistent():
    empirical = QueueReactiveSimulator(
        SimulationConfig(seed=21, duration=180, max_events=2_000)
    ).run()
    table = Calibrator().fit(empirical.events_df())

    simulated = QueueReactiveSimulator(
        SimulationConfig(seed=21, duration=180, max_events=2_000), table
    ).run()
    result = Validator().compare_snapshots(
        simulated.snapshots_df(), empirical.snapshots_df(), tolerance=0.35
    )

    assert result.passed
    assert result.metrics["bid_depth_rel_error"] < 0.35
