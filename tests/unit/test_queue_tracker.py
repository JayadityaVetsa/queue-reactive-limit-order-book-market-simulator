from lob_sim.queue_tracker import QueueTracker
from lob_sim.types import Side


def test_queue_positions_and_partial_fills():
    tracker = QueueTracker()
    tracker.insert_order("a", Side.BID, 1, 10)
    tracker.insert_order("b", Side.BID, 1, 7)
    tracker.insert_order("c", Side.BID, 1, 3)

    assert tracker.get_position("b") == 10
    assert tracker.consume_front(Side.BID, 1, 12) == [("a", 10), ("b", 2)]
    assert tracker.get_position("b") == 0
    assert tracker.get_position("c") == 5


def test_remove_order_deletes_when_empty():
    tracker = QueueTracker()
    tracker.insert_order("x", Side.ASK, 2, 4)
    assert tracker.remove_order("x", 10) == 4
    try:
        tracker.get_position("x")
    except KeyError:
        pass
    else:
        raise AssertionError("empty order should be removed")


def test_get_volume_ahead_sums_only_orders_before_position():
    tracker = QueueTracker()
    tracker.insert_order("a", Side.ASK, 1, 10)
    tracker.insert_order("b", Side.ASK, 1, 7)
    tracker.insert_order("c", Side.ASK, 1, 3)

    assert tracker.get_volume_ahead(Side.ASK, 1, 0) == 0
    assert tracker.get_volume_ahead(Side.ASK, 1, 1) == 10
    assert tracker.get_volume_ahead(Side.ASK, 1, 2) == 17
