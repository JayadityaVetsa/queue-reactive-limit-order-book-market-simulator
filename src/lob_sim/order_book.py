"""Multi-level limit order book with queue-reactive price movement."""

from __future__ import annotations

from dataclasses import dataclass, field

from lob_sim.types import BookSnapshot, Side, Trade


@dataclass
class OrderBook:
    """Aggregated FIFO-style book state for K levels on each side.

    The simulator follows the queue-reactive convention: best ask depletion
    moves the midprice up one tick, while best bid depletion moves it down.
    Deeper queues shift inward and the far level is replenished.
    """

    levels: int = 5
    tick_size: float = 0.01
    midprice: float = 100.0
    initial_depth: int = 100
    replenish_depth: int = 100
    bids: list[int] = field(default_factory=list)
    asks: list[int] = field(default_factory=list)
    price_moves: int = 0

    def __post_init__(self) -> None:
        if self.levels < 1:
            raise ValueError("levels must be positive")
        if self.tick_size <= 0:
            raise ValueError("tick_size must be positive")
        if not self.bids:
            self.bids = [self.initial_depth for _ in range(self.levels)]
        if not self.asks:
            self.asks = [self.initial_depth for _ in range(self.levels)]
        if len(self.bids) != self.levels or len(self.asks) != self.levels:
            raise ValueError("bid and ask arrays must match levels")

    def clone(self) -> "OrderBook":
        """Return an independent copy of the book."""

        return OrderBook(
            levels=self.levels,
            tick_size=self.tick_size,
            midprice=self.midprice,
            initial_depth=self.initial_depth,
            replenish_depth=self.replenish_depth,
            bids=list(self.bids),
            asks=list(self.asks),
            price_moves=self.price_moves,
        )

    def queue(self, side: Side) -> list[int]:
        return self.bids if side is Side.BID else self.asks

    def get_queue_size(self, side: Side, level: int) -> int:
        self._check_level(level)
        return self.queue(side)[level - 1]

    def apply_limit_order(self, side: Side, level: int, volume: int) -> None:
        self._check_level(level)
        self._check_volume(volume)
        self.queue(side)[level - 1] += volume

    def apply_cancel(self, side: Side, level: int, volume: int) -> int:
        self._check_level(level)
        self._check_volume(volume)
        queue = self.queue(side)
        removed = min(queue[level - 1], volume)
        queue[level - 1] -= removed
        self._handle_depletion()
        return removed

    def apply_market_order(
        self, aggressor_side: Side, volume: int, timestamp: float = 0.0
    ) -> list[Trade]:
        """Consume the opposite side from best to worst level."""

        self._check_volume(volume)
        passive_side = aggressor_side.opposite
        queue = self.queue(passive_side)
        remaining = volume
        trades: list[Trade] = []
        for index in range(self.levels):
            if remaining <= 0:
                break
            available = queue[index]
            if available <= 0:
                continue
            fill = min(available, remaining)
            queue[index] -= fill
            remaining -= fill
            trades.append(
                Trade(
                    timestamp=timestamp,
                    price=self.price_at(passive_side, index + 1),
                    volume=fill,
                    aggressor_side=aggressor_side,
                )
            )
        self._handle_depletion()
        return trades

    def price_at(self, side: Side, level: int) -> float:
        self._check_level(level)
        offset = (level - 0.5) * self.tick_size
        return self.midprice - offset if side is Side.BID else self.midprice + offset

    @property
    def spread_ticks(self) -> int:
        return 1

    @property
    def bid_depth(self) -> int:
        return sum(self.bids)

    @property
    def ask_depth(self) -> int:
        return sum(self.asks)

    @property
    def imbalance(self) -> float:
        total = self.bid_depth + self.ask_depth
        return 0.0 if total == 0 else (self.bid_depth - self.ask_depth) / total

    def snapshot(self, timestamp: float) -> BookSnapshot:
        return BookSnapshot(
            timestamp=timestamp,
            midprice=self.midprice,
            spread_ticks=self.spread_ticks,
            bid_depth=self.bid_depth,
            ask_depth=self.ask_depth,
            imbalance=self.imbalance,
            best_bid=self.bids[0],
            best_ask=self.asks[0],
        )

    def state_key(self, bin_size: int = 50) -> str:
        """Discretize depth and imbalance for empirical intensities."""

        bid_bin = self.bid_depth // bin_size
        ask_bin = self.ask_depth // bin_size
        imbalance_bin = int((self.imbalance + 1.0) * 5)
        return f"bd={bid_bin}|ad={ask_bin}|imb={imbalance_bin}"

    def _handle_depletion(self) -> None:
        while self.asks[0] <= 0:
            self.midprice += self.tick_size
            self.price_moves += 1
            self.asks = self.asks[1:] + [self.replenish_depth]
            self.bids = [self.replenish_depth] + self.bids[:-1]
        while self.bids[0] <= 0:
            self.midprice -= self.tick_size
            self.price_moves += 1
            self.bids = self.bids[1:] + [self.replenish_depth]
            self.asks = [self.replenish_depth] + self.asks[:-1]

    def _check_level(self, level: int) -> None:
        if level < 1 or level > self.levels:
            raise ValueError(f"level must be in [1, {self.levels}]")

    @staticmethod
    def _check_volume(volume: int) -> None:
        if volume <= 0:
            raise ValueError("volume must be positive")
