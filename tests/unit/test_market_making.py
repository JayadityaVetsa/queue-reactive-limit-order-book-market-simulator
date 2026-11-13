import os
import random

import pytest

from lob_sim.execution import NativeExecution, consume
from lob_sim.market_making import Ledger, SCENARIOS, Scenario, TapeEvent, make_tape, replay


def test_accounting_roundtrip_and_position_reversal():
    ledger = Ledger()
    for quantity, price in ((5, 100), (-8, 102), (1, 99), (2, 101)):
        ledger.trade(quantity, price, 0.1)
        assert ledger.cash + ledger.inventory * 103 == pytest.approx(ledger.realized + ledger.unrealized(103))
    assert ledger.inventory == 0
    assert ledger.realized == pytest.approx(15 - 1.6)


def test_fifo_partial_fill():
    assert consume(8, 10, 5) == (0, 2)
    assert consume(4, 2, 5) == (2, 0)
    assert consume(100, 0, 3) == (3, 0)


def test_replay_determinism_cap_and_accounting():
    tape = make_tape(SCENARIOS[-1], 7, 500)
    assert tape == make_tape(SCENARIOS[-1], 7, 500)
    result, path = replay(tape, SCENARIOS[-1], skew=0.05, limit=10)
    assert result == replay(tape, SCENARIOS[-1], skew=0.05, limit=10)[0]
    assert path.inventory.abs().max() <= 10
    assert (path.equity - path.realized - path.unrealized).abs().max() < 1e-7
    assert result["liquidation_pnl"] <= result["pnl"]


def test_touch_does_not_fill_and_latency_keeps_old_quote():
    # Initial ask joins behind ten shares. Five shares cannot reach the maker.
    touch = TapeEvent(100, 100, 1, 5, (10,), (10,))
    assert replay((touch,), Scenario("test"))[0]["fills"] == 0
    sweep = TapeEvent(100, 103, 1, 20, (10,), (10,))
    stale = TapeEvent(103, 103, 1, 20, (10,), (10,))
    _, path = replay((touch, sweep, stale), Scenario("test", latency=1), refresh=1)
    assert path.iloc[0].fills == 0
    assert path.iloc[1].inventory == -5


def test_deeper_quote_requires_better_depth_to_clear():
    event = TapeEvent(100, 100, 1, 19, (10, 10), (10, 10))
    assert replay((event,), Scenario("test"), half_spread=1.5)[0]["fills"] == 0
    sweep = TapeEvent(100, 100, 1, 23, (10, 10), (10, 10))
    assert replay((sweep,), Scenario("test"), half_spread=1.5)[0]["volume"] == 3


def test_future_markout_data_does_not_change_current_decisions():
    from dataclasses import replace
    tape = make_tape(SCENARIOS[-1], 2, 100)
    changed = tape[:50] + tuple(replace(e, mid=e.mid + 500, after=e.after + 500) for e in tape[50:])
    _, original = replay(tape, SCENARIOS[-1], skew=0.1)
    _, altered = replay(changed, SCENARIOS[-1], skew=0.1)
    assert original.iloc[:50].equals(altered.iloc[:50])


@pytest.mark.skipif(not os.environ.get("LOB_NATIVE"), reason="set LOB_NATIVE to the compiled library")
def test_native_reference_parity():
    native = NativeExecution(os.environ["LOB_NATIVE"])
    rng = random.Random(5)
    for _ in range(10000):
        args = rng.randint(0, 1000), rng.randint(0, 500), rng.randint(0, 100)
        assert native(*args) == consume(*args)
    tape = make_tape(SCENARIOS[-1], 11, 500)
    assert replay(tape, SCENARIOS[-1], executor=native)[0] == replay(tape, SCENARIOS[-1])[0]
