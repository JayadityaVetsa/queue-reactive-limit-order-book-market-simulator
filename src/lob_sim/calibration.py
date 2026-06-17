"""Empirical intensity calibration for queue-reactive simulations."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import pandas as pd

from lob_sim.order_book import OrderBook
from lob_sim.types import Event, EventType, Side


@dataclass
class IntensityTable:
    """State-dependent event intensities lambda_i(q)."""

    rates: dict[str, dict[str, float]] = field(default_factory=dict)
    fallback_rates: dict[str, float] = field(default_factory=dict)

    def rate(self, state_key: str, event_type: EventType) -> float:
        by_state = self.rates.get(state_key, {})
        return float(by_state.get(event_type.value, self.fallback_rates[event_type.value]))

    def to_json(self, path: str | Path) -> None:
        payload = {"rates": self.rates, "fallback_rates": self.fallback_rates}
        Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @classmethod
    def from_json(cls, path: str | Path) -> "IntensityTable":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(rates=payload["rates"], fallback_rates=payload["fallback_rates"])


class Calibrator:
    """Estimate lambda_i(q) = N_i(q) / T(q) from event data."""

    def __init__(
        self,
        levels: int = 5,
        tick_size: float = 0.01,
        initial_depth: int = 100,
        bin_size: int = 50,
    ) -> None:
        self.levels = levels
        self.tick_size = tick_size
        self.initial_depth = initial_depth
        self.bin_size = bin_size

    def fit(self, events: pd.DataFrame | Iterable[Event]) -> IntensityTable:
        event_list = self._coerce_events(events)
        if len(event_list) < 2:
            raise ValueError("at least two events are required for calibration")

        book = OrderBook(
            levels=self.levels,
            tick_size=self.tick_size,
            initial_depth=self.initial_depth,
        )
        state_times: defaultdict[str, float] = defaultdict(float)
        state_counts: defaultdict[str, Counter[str]] = defaultdict(Counter)
        total_counts: Counter[str] = Counter()
        total_time = max(event_list[-1].timestamp - event_list[0].timestamp, 1e-9)

        previous_time = event_list[0].timestamp
        for event in event_list:
            state = book.state_key(self.bin_size)
            dt = max(event.timestamp - previous_time, 0.0)
            state_times[state] += dt
            state_counts[state][event.event_type.value] += 1
            total_counts[event.event_type.value] += 1
            self._apply(book, event)
            previous_time = event.timestamp

        fallback = {
            event_type.value: max(total_counts[event_type.value] / total_time, 1e-9)
            for event_type in EventType
        }
        rates: dict[str, dict[str, float]] = {}
        for state, counts in state_counts.items():
            exposure = max(state_times[state], 1e-9)
            rates[state] = {
                event_type.value: max(counts[event_type.value] / exposure, 1e-9)
                for event_type in EventType
            }
        return IntensityTable(rates=rates, fallback_rates=fallback)

    def load_csv(self, path: str | Path) -> pd.DataFrame:
        return pd.read_csv(path)

    @staticmethod
    def _apply(book: OrderBook, event: Event) -> None:
        if event.event_type is EventType.LIMIT:
            book.apply_limit_order(event.side, event.level, event.volume)
        elif event.event_type is EventType.CANCEL:
            book.apply_cancel(event.side, event.level, event.volume)
        else:
            book.apply_market_order(event.side, event.volume, event.timestamp)

    @staticmethod
    def _coerce_events(events: pd.DataFrame | Iterable[Event]) -> list[Event]:
        if isinstance(events, pd.DataFrame):
            has_order_id = "order_id" in events.columns
            return [
                Event(
                    timestamp=float(row.timestamp),
                    event_type=EventType(str(row.event_type)),
                    side=Side(str(row.side)),
                    level=int(row.level),
                    volume=int(row.volume),
                    order_id=(
                        None
                        if not has_order_id or pd.isna(row.order_id)
                        else str(row.order_id)
                    ),
                )
                for row in events.itertuples(index=False)
            ]
        return sorted(list(events), key=lambda item: item.timestamp)
