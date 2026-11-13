from dataclasses import replace

import numpy as np
import pytest

from lob_sim.alpha_strategy import (DepthForecast, cross_book, depth_features,
                                    fit_forecast, replay_alpha)
from lob_sim.market_making import Ledger, SCENARIOS, Scenario, TapeEvent, make_tape


def constant_model(prediction=2.0, latency=0, horizon=20):
    return DepthForecast((prediction,) + (0.0,) * 15, 18.0, horizon, latency, 10.0, 0)


def path(direction=1, n=25):
    return tuple(TapeEvent(100 + direction * i, 100 + direction * (i + 1),
                           1, 5, (10,) * 8, (10,) * 8) for i in range(n))


def test_depth_signal_reflects_when_sides_exchange():
    bids, asks = (2, 4, 9, 20, 21, 22, 23, 24), (20, 15, 8, 7, 6, 5, 4, 3)
    original = depth_features(bids, asks, 18)
    flipped = depth_features(asks, bids, 18)
    assert original[0] == flipped[0] == 1
    np.testing.assert_allclose(original[1:], -flipped[1:])


def test_training_labels_start_at_order_arrival_not_send_time():
    tape = tuple(TapeEvent(i * i, 99999, 1, 10, (10,) * 8, (10,) * 8) for i in range(10))
    model = fit_forecast((tape,), horizon=2, latency=3, ridge=1)
    labels = [(i + 5) ** 2 - (i + 3) ** 2 for i in range(5)]
    assert model.observations == 5
    assert model.predict((10,) * 8, (10,) * 8) == pytest.approx(sum(labels) / 6)
    assert model.volume_scale == 10


def test_round_trip_pays_both_spreads_and_fees():
    result, rows = replay_alpha(path(), Scenario("test", fee=0.02), constant_model(), margin=0)
    assert result["pnl"] == pytest.approx(20 - 1 - 0.04)
    assert result["execution_shortfall"] == 1
    assert result["fees"] == pytest.approx(0.04)
    assert result["round_trips"] == 1
    assert result["final_inventory"] == 0
    assert rows.iloc[19].inventory == 1
    assert rows.iloc[20].inventory == 0
    assert (rows.equity - rows.realized - rows.unrealized).abs().max() < 1e-7


def test_short_can_win_and_wrong_signal_exits_at_a_loss():
    correct, _ = replay_alpha(path(-1), Scenario("test"), constant_model(-2), margin=0)
    wrong, rows = replay_alpha(path(-1), Scenario("test"), constant_model(2), margin=0)
    assert correct["pnl"] == pytest.approx(18.96)
    assert wrong["pnl"] == pytest.approx(-21.04)
    assert rows.iloc[20].inventory == 0


def test_latency_is_paid_at_entry_and_exit():
    result, rows = replay_alpha(path(n=28), Scenario("test", latency=2),
                                constant_model(latency=2), margin=0)
    assert rows.iloc[0].inventory == rows.iloc[1].inventory == 0
    assert rows.iloc[2].inventory == rows.iloc[21].inventory == 1
    assert rows.iloc[22].inventory == 0
    assert result["pnl"] == pytest.approx(18.96)


def test_cash_and_fee_gate_do_not_manufacture_wins():
    cash, _ = replay_alpha(path(), Scenario("test"), constant_model(0))
    expensive, _ = replay_alpha(path(), Scenario("test", fee=0.3), constant_model(1.5), margin=0)
    for result in (cash, expensive):
        assert result["pnl"] == result["volume"] == result["fills"] == 0


def test_market_order_sweeps_visible_depth_and_charges_slippage():
    ledger = Ledger()
    event = TapeEvent(100, 100, 0, 0, (1, 2), (1, 2))
    filled, shortfall = cross_book(ledger, 3, event, 0.1)
    assert filled == ledger.inventory == 3
    assert shortfall == 3.5
    assert ledger.cash == pytest.approx(-303.8)
    filled, _ = cross_book(ledger, -5, event, 0.1)
    assert filled == -3  # never invent liquidity beyond the visible book
    assert ledger.inventory == 0


def test_future_data_cannot_change_earlier_actions():
    tape = make_tape(SCENARIOS[-1], 77, 200)
    changed = tape[:80] + tuple(replace(e, mid=e.mid + 1000, after=e.after + 1000,
                                       bids=tuple(reversed(e.bids))) for e in tape[80:])
    model = constant_model(latency=8)
    _, original = replay_alpha(tape, SCENARIOS[-1], model, margin=0)
    _, altered = replay_alpha(changed, SCENARIOS[-1], model, margin=0)
    assert original.iloc[:80].equals(altered.iloc[:80])


def test_latency_model_mismatch_is_rejected():
    with pytest.raises(ValueError, match="latency"):
        replay_alpha(path(), Scenario("test", latency=8), constant_model())
