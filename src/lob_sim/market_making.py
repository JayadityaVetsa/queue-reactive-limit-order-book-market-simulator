"""Paired market-making experiments on an exogenous queue-reactive event tape.

The maker is a shadow participant: its orders never alter the background tape.
This isolates policy comparisons, but excludes endogenous impact and competition.
Prices below are in ticks, including half-tick best quotes; cash is in tick-shares.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import random
from typing import Callable

import pandas as pd

from lob_sim.execution import consume
from lob_sim.order_book import OrderBook
from lob_sim.types import Side


@dataclass(frozen=True)
class Scenario:
    name: str
    drift: float = 0.0
    volatility: float = 0.0
    informed: float = 0.0
    latency: int = 0
    fee: float = 0.02


SCENARIOS = (
    Scenario("quiet"),
    Scenario("uptrend", drift=0.035),
    Scenario("downtrend", drift=-0.035),
    Scenario("volatility_switch", volatility=0.32),
    Scenario("informed", volatility=0.15, informed=0.65),
    Scenario("latency", volatility=0.15, informed=0.65, latency=8),
    Scenario("costs", fee=0.30),
    Scenario("combined", drift=-0.035, volatility=0.32, informed=0.65, latency=8, fee=0.30),
)


@dataclass(frozen=True)
class TapeEvent:
    mid: float
    after: float
    side: int  # +1 buys from maker ask; -1 sells to maker bid; 0 is no market order
    volume: int
    bids: tuple[int, ...]
    asks: tuple[int, ...]


def make_tape(scenario: Scenario, seed: int, events: int) -> tuple[TapeEvent, ...]:
    """Generate once per seed, then replay unchanged for every policy."""
    rng = random.Random(seed)
    book = OrderBook(levels=8, tick_size=1.0, midprice=10000.0,
                     initial_depth=20, replenish_depth=20)
    tape = []
    for i in range(events):
        mid = book.midprice
        bids, asks = tuple(book.bids), tuple(book.asks)
        shock = (rng.choice((-1, 1)) if rng.random() <
                 scenario.volatility * (1 if i >= events // 2 else 0.1) else 0)
        drift = (1 if scenario.drift > 0 else -1) if rng.random() < abs(scenario.drift) else 0
        future = shock + drift
        event_draw, side_draw, informed_draw = rng.random(), rng.random(), rng.random()
        side = 1 if side_draw < 0.5 else -1
        if future and informed_draw < scenario.informed:
            side = 1 if future > 0 else -1
        volume = max(1, int(rng.expovariate(1 / 18)))
        if event_draw < 0.48:
            book.apply_market_order(Side.BID if side == 1 else Side.ASK, volume)
        else:
            passive = Side.BID if side == 1 else Side.ASK
            level = rng.randint(1, book.levels)
            if event_draw < 0.80:
                book.apply_limit_order(passive, level, volume)
            else:
                book.apply_cancel(passive, level, volume)
            side = 0
        book.midprice += future
        tape.append(TapeEvent(mid, book.midprice, side, volume, bids, asks))
    return tuple(tape)


@dataclass
class Ledger:
    inventory: int = 0
    average: float = 0.0
    cash: float = 0.0
    realized: float = 0.0  # includes all fees, even on opening trades
    fees: float = 0.0
    fills: int = 0
    volume: int = 0

    def trade(self, quantity: int, price: float, fee: float) -> None:
        old = self.inventory
        if old and old * quantity < 0:
            closed = min(abs(old), abs(quantity))
            self.realized += closed * (price - self.average) * (1 if old > 0 else -1)
        new = old + quantity
        if old == 0 or old * quantity > 0:
            self.average = (abs(old) * self.average + abs(quantity) * price) / abs(new)
        elif new == 0:
            self.average = 0.0
        elif old * new < 0:
            self.average = price
        cost = abs(quantity) * fee
        self.realized -= cost
        self.fees += cost
        self.cash -= quantity * price + cost
        self.inventory = new
        self.fills += 1
        self.volume += abs(quantity)

    def unrealized(self, mid: float) -> float:
        return self.inventory * (mid - self.average)


@dataclass
class Quote:
    price: float
    ahead: int
    remaining: int


def replay(tape: tuple[TapeEvent, ...], scenario: Scenario, skew: float = 0.0,
           half_spread: float = 0.5, size: int = 5, limit: int = 40,
           refresh: int = 5, executor: Callable = consume) -> tuple[dict, pd.DataFrame]:
    if not tape or size <= 0 or limit < size or refresh <= 0 or half_spread < 0.5 or skew < 0:
        raise ValueError("invalid replay parameters or empty tape")
    ledger = Ledger()
    quotes: dict[int, Quote] = {}
    pending = None
    rows = []
    peak = drawdown = 0.0
    markouts = []
    for i, event in enumerate(tape):
        # One replacement in flight. Existing orders remain live until arrival.
        if i % refresh == 0 and pending is None:
            center = event.mid - skew * ledger.inventory
            bid = min(event.mid - 0.5, math.floor(center - half_spread - 0.5) + 0.5)
            ask = max(event.mid + 0.5, math.ceil(center + half_spread - 0.5) + 0.5)
            pending = (i + scenario.latency, bid, ask)
        if pending is not None and pending[0] <= i:
            _, bid, ask = pending
            quotes = {}
            for direction, price, depths in ((-1, bid, event.bids), (1, ask, event.asks)):
                # Post-only: reject quotes crossing the current opposite best.
                if (direction == -1 and price >= event.mid + 0.5) or (direction == 1 and price <= event.mid - 0.5):
                    continue
                distance = (price - event.mid) * direction
                index = int(round(distance - 0.5))
                if index < 0 or index >= len(depths):
                    continue
                capacity = limit + direction * ledger.inventory
                if capacity > 0:
                    quotes[direction] = Quote(price, depths[index], min(size, capacity))
            pending = None
        if event.side in quotes:
            quote = quotes[event.side]
            depths = event.asks if event.side == 1 else event.bids
            # Subtract background quantity at strictly better prices. Orders
            # behind our queue never advance our priority; cancellations do not.
            better = sum(depth for level, depth in enumerate(depths)
                         if (event.mid + event.side * (level + 0.5) - quote.price) * event.side < -1e-9)
            eligible = max(0, event.volume - better)
            capacity = limit + event.side * ledger.inventory
            fill, quote.ahead = executor(eligible, quote.ahead, min(quote.remaining, capacity))
            if fill:
                ledger.trade(-event.side * fill, quote.price, scenario.fee)
                quote.remaining -= fill
                horizon_mid = tape[min(i + 10, len(tape) - 1)].after
                markouts.append((-event.side * (horizon_mid - quote.price), fill))
        equity = ledger.cash + ledger.inventory * event.after
        peak = max(peak, equity)
        drawdown = max(drawdown, peak - equity)
        rows.append(dict(event=i, mid=event.after, inventory=ledger.inventory, equity=equity,
                         realized=ledger.realized, unrealized=ledger.unrealized(event.after),
                         fees=ledger.fees, fills=ledger.fills))
    final = rows[-1]
    # Executable terminal estimate: one half-tick crossing plus fee per share.
    liquidation = abs(ledger.inventory) * (0.5 + scenario.fee)
    return dict(pnl=final["equity"], liquidation_pnl=final["equity"] - liquidation,
                realized=ledger.realized, unrealized=final["unrealized"], fees=ledger.fees,
                drawdown=drawdown, fills=ledger.fills, volume=ledger.volume,
                final_inventory=ledger.inventory,
                mean_abs_inventory=sum(abs(r["inventory"]) for r in rows) / len(rows),
                markout_10=sum(m * n for m, n in markouts) / max(1, sum(n for _, n in markouts))), pd.DataFrame(rows)
