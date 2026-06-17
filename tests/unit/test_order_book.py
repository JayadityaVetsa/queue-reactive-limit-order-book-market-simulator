from lob_sim.order_book import OrderBook
from lob_sim.types import Side


def test_limit_cancel_and_market_order_update_depths():
    book = OrderBook(levels=3, initial_depth=10, replenish_depth=10)
    book.apply_limit_order(Side.BID, level=2, volume=5)
    assert book.get_queue_size(Side.BID, 2) == 15

    removed = book.apply_cancel(Side.BID, level=2, volume=7)
    assert removed == 7
    assert book.get_queue_size(Side.BID, 2) == 8

    trades = book.apply_market_order(Side.BID, volume=12, timestamp=1.0)
    assert sum(trade.volume for trade in trades) == 12
    assert book.get_queue_size(Side.ASK, 1) == 8
    assert book.price_moves == 1
    assert book.midprice == 100.01


def test_bid_depletion_moves_midprice_down_one_tick():
    book = OrderBook(levels=2, tick_size=0.25, initial_depth=5, replenish_depth=5)
    book.apply_market_order(Side.ASK, volume=5, timestamp=1.0)
    assert book.price_moves == 1
    assert book.midprice == 99.75


def test_snapshot_contains_research_metrics():
    book = OrderBook(levels=2, initial_depth=10)
    snap = book.snapshot(0.5)
    assert snap.spread_ticks == 1
    assert snap.bid_depth == 20
    assert snap.ask_depth == 20
    assert snap.imbalance == 0.0
