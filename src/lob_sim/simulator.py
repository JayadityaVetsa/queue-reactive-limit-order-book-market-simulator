"""Event-driven queue-reactive limit order book simulator."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import random

import pandas as pd

from lob_sim.calibration import IntensityTable
from lob_sim.order_book import OrderBook
from lob_sim.types import BookSnapshot, Event, EventType, Side, Trade


@dataclass(frozen=True)
class SimulationConfig:
    levels: int = 5
    tick_size: float = 0.01
    initial_midprice: float = 100.0
    initial_depth: int = 100
    replenish_depth: int = 100
    seed: int = 7
    duration: float = 600.0
    max_events: int = 25_000
    base_limit_rate: float = 8.0
    base_market_rate: float = 2.4
    base_cancel_rate: float = 2.1
    mean_order_size: float = 12.0
    sample_every: int = 10
    bin_size: int = 50


class QueueReactiveSimulator:
    """Generate continuous-time Markov order book event paths."""

    def __init__(
        self,
        config: SimulationConfig | None = None,
        intensities: IntensityTable | None = None,
    ) -> None:
        self.config = config or SimulationConfig()
        self.intensities = intensities
        self.rng = random.Random(self.config.seed)
        self._level_cdf = self._build_level_cdf()
        self.book = self._fresh_book()
        self.events: list[Event] = []
        self.trades: list[Trade] = []
        self.snapshots: list[BookSnapshot] = []

    def run(self) -> "QueueReactiveSimulator":
        t = 0.0
        self.events.clear()
        self.trades.clear()
        self.snapshots = [self.book.snapshot(t)]

        for index in range(self.config.max_events):
            rates = self._rates()
            total_rate = sum(rates.values())
            if total_rate <= 0:
                break
            t += self.rng.expovariate(total_rate)
            if t > self.config.duration:
                break

            event_type = self._choose_event_type(rates, total_rate)
            side = self._choose_side(event_type)
            level = self._choose_level(event_type)
            volume = self._choose_volume()
            event = Event(t, event_type, side, level, volume)
            self._apply(event)
            self.events.append(event)
            if index % self.config.sample_every == 0:
                self.snapshots.append(self.book.snapshot(t))

        self.snapshots.append(self.book.snapshot(t))
        return self

    def reset(self) -> None:
        self.rng = random.Random(self.config.seed)
        self.book = self._fresh_book()
        self.events.clear()
        self.trades.clear()
        self.snapshots.clear()

    def statistics(self) -> dict[str, float]:
        snapshots = self.snapshots_df()
        if snapshots.empty:
            return {}
        total_volume = sum(trade.volume for trade in self.trades)
        return {
            "events": float(len(self.events)),
            "trades": float(len(self.trades)),
            "traded_volume": float(total_volume),
            "final_midprice": float(self.book.midprice),
            "price_moves": float(self.book.price_moves),
            "mean_spread_ticks": float(snapshots["spread_ticks"].mean()),
            "mean_bid_depth": float(snapshots["bid_depth"].mean()),
            "mean_ask_depth": float(snapshots["ask_depth"].mean()),
            "mean_imbalance": float(snapshots["imbalance"].mean()),
        }

    def events_df(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "timestamp": event.timestamp,
                    "event_type": event.event_type.value,
                    "side": event.side.value,
                    "level": event.level,
                    "volume": event.volume,
                    "order_id": event.order_id,
                }
                for event in self.events
            ]
        )

    def trades_df(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "timestamp": trade.timestamp,
                    "price": trade.price,
                    "volume": trade.volume,
                    "aggressor_side": trade.aggressor_side.value,
                }
                for trade in self.trades
            ]
        )

    def snapshots_df(self) -> pd.DataFrame:
        return pd.DataFrame([asdict(snapshot) for snapshot in self.snapshots])

    def _fresh_book(self) -> OrderBook:
        return OrderBook(
            levels=self.config.levels,
            tick_size=self.config.tick_size,
            midprice=self.config.initial_midprice,
            initial_depth=self.config.initial_depth,
            replenish_depth=self.config.replenish_depth,
        )

    def _rates(self) -> dict[EventType, float]:
        if self.intensities is not None:
            state = self.book.state_key(self.config.bin_size)
            return {event_type: self.intensities.rate(state, event_type) for event_type in EventType}

        imbalance = self.book.imbalance
        thin_ask = 1.0 + max(0.0, -imbalance)
        thin_bid = 1.0 + max(0.0, imbalance)
        return {
            EventType.LIMIT: self.config.base_limit_rate * (1.0 + 0.25 * abs(imbalance)),
            EventType.MARKET: self.config.base_market_rate * (thin_ask + thin_bid) / 2.0,
            EventType.CANCEL: self.config.base_cancel_rate * (1.0 + 0.5 * abs(imbalance)),
        }

    def _choose_event_type(
        self, rates: dict[EventType, float], total_rate: float
    ) -> EventType:
        draw = self.rng.random() * total_rate
        cumulative = 0.0
        for event_type, rate in rates.items():
            cumulative += rate
            if draw <= cumulative:
                return event_type
        return EventType.CANCEL

    def _choose_side(self, event_type: EventType) -> Side:
        imbalance = self.book.imbalance
        if event_type is EventType.LIMIT:
            bid_probability = 0.5 - 0.18 * imbalance
        elif event_type is EventType.MARKET:
            bid_probability = 0.5 + 0.22 * imbalance
        else:
            bid_probability = 0.5 + 0.15 * imbalance
        bid_probability = max(0.1, min(0.9, bid_probability))
        return Side.BID if self.rng.random() < bid_probability else Side.ASK

    def _choose_level(self, event_type: EventType) -> int:
        if event_type is EventType.MARKET:
            return 1
        draw = self.rng.random()
        for level, cutoff in enumerate(self._level_cdf, start=1):
            if draw <= cutoff:
                return level
        return self.config.levels

    def _choose_volume(self) -> int:
        return max(1, int(self.rng.expovariate(1.0 / self.config.mean_order_size)))

    def _apply(self, event: Event) -> None:
        if event.event_type is EventType.LIMIT:
            self.book.apply_limit_order(event.side, event.level, event.volume)
        elif event.event_type is EventType.CANCEL:
            self.book.apply_cancel(event.side, event.level, event.volume)
        else:
            self.trades.extend(
                self.book.apply_market_order(event.side, event.volume, event.timestamp)
            )

    def _build_level_cdf(self) -> list[float]:
        weights = [2.718281828459045 ** (-0.75 * idx) for idx in range(self.config.levels)]
        total = sum(weights)
        cumulative = 0.0
        cdf: list[float] = []
        for weight in weights:
            cumulative += weight / total
            cdf.append(cumulative)
        cdf[-1] = 1.0
        return cdf
