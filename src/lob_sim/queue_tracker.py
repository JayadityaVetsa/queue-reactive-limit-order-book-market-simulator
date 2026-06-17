"""Queue position tracking for individual resting orders."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass

from lob_sim.types import Side


@dataclass
class TrackedOrder:
    order_id: str
    side: Side
    level: int
    volume: int


class QueueTracker:
    """Track FIFO positions and partial fills at each side/level queue."""

    def __init__(self) -> None:
        self._queues: dict[tuple[Side, int], deque[TrackedOrder]] = defaultdict(deque)
        self._orders: dict[str, TrackedOrder] = {}

    def insert_order(self, order_id: str, side: Side, level: int, volume: int) -> None:
        if order_id in self._orders:
            raise ValueError(f"duplicate order_id: {order_id}")
        if volume <= 0:
            raise ValueError("volume must be positive")
        order = TrackedOrder(order_id, side, level, volume)
        self._orders[order_id] = order
        self._queues[(side, level)].append(order)

    def remove_order(self, order_id: str, volume: int) -> int:
        if volume <= 0:
            raise ValueError("volume must be positive")
        order = self._orders[order_id]
        removed = min(order.volume, volume)
        order.volume -= removed
        if order.volume == 0:
            del self._orders[order_id]
            queue = self._queues[(order.side, order.level)]
            self._queues[(order.side, order.level)] = deque(
                item for item in queue if item.order_id != order_id
            )
        return removed

    def consume_front(self, side: Side, level: int, volume: int) -> list[tuple[str, int]]:
        fills: list[tuple[str, int]] = []
        queue = self._queues[(side, level)]
        remaining = volume
        while queue and remaining > 0:
            order = queue[0]
            fill = min(order.volume, remaining)
            order.volume -= fill
            remaining -= fill
            fills.append((order.order_id, fill))
            if order.volume == 0:
                queue.popleft()
                self._orders.pop(order.order_id, None)
        return fills

    def get_position(self, order_id: str) -> int:
        order = self._orders[order_id]
        ahead = 0
        for item in self._queues[(order.side, order.level)]:
            if item.order_id == order_id:
                return ahead
            ahead += item.volume
        raise KeyError(order_id)

    def get_volume_ahead(self, side: Side, level: int, position: int) -> int:
        if position < 0:
            raise ValueError("position must be non-negative")
        return sum(
            item.volume
            for index, item in enumerate(self._queues[(side, level)])
            if index < position
        )
