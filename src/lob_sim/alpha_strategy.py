"""Cost-gated directional trading from a depth-only, latency-aware forecast.

This is an aggressive liquidity-taking strategy, not passive market making.
The forecast sees displayed depths only. Future prices are training labels and
evaluation marks; neither is exposed to the live prediction interface.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Iterable

import numpy as np
import pandas as pd

from lob_sim.market_making import Ledger, Scenario, TapeEvent


FEATURE_NAMES = (
    "intercept", "imbalance_1", "imbalance_2", "imbalance_4", "imbalance_8",
    *(f"log_depth_difference_{i}" for i in range(1, 9)),
    "sweep_difference_1", "sweep_difference_2", "sweep_difference_4",
)


def depth_features(bids: tuple[int, ...], asks: tuple[int, ...], scale: float) -> np.ndarray:
    """A signed feature changes sign when bid and ask depths are exchanged."""
    if scale <= 0 or not math.isfinite(scale):
        raise ValueError("feature scale must be finite and positive")
    b = np.asarray((tuple(bids) + (0,) * 8)[:8], dtype=float)
    a = np.asarray((tuple(asks) + (0,) * 8)[:8], dtype=float)
    if (b < 0).any() or (a < 0).any():
        raise ValueError("depth cannot be negative")
    cb, ca = np.cumsum(b), np.cumsum(a)
    levels = np.array([0, 1, 3, 7])
    imbalance = (cb[levels] - ca[levels]) / (cb[levels] + ca[levels] + 1)
    sweeps = np.exp(-ca[[0, 1, 3]] / scale) - np.exp(-cb[[0, 1, 3]] / scale)
    return np.concatenate(([1.0], imbalance, np.log1p(b) - np.log1p(a), sweeps))


@dataclass(frozen=True)
class DepthForecast:
    coefficients: tuple[float, ...]
    volume_scale: float
    horizon: int
    latency: int
    ridge: float
    observations: int

    def predict(self, bids: tuple[int, ...], asks: tuple[int, ...]) -> float:
        return float(depth_features(bids, asks, self.volume_scale) @ self.coefficients)

    def to_dict(self) -> dict:
        return dict(asdict(self), feature_names=FEATURE_NAMES)


def fit_forecast(tapes: Iterable[tuple[TapeEvent, ...]], horizon: int = 20,
                 latency: int = 0, ridge: float = 10.0) -> DepthForecast:
    """Fit expected mid movement from entry arrival to a scheduled exit arrival.

    One model is fitted for each supported execution latency, using the same
    training tapes. No scenario name, drift, future flow or future depth is an
    input. The sweep feature's volume scale is estimated on training data only.
    """
    tapes = tuple(tapes)
    if horizon <= 0 or latency < 0 or ridge <= 0:
        raise ValueError("invalid forecast settings")
    market_volumes = [e.volume for tape in tapes for e in tape if e.side]
    if not market_volumes:
        raise ValueError("training requires market orders")
    scale = float(np.mean(market_volumes))
    xx = np.zeros((len(FEATURE_NAMES), len(FEATURE_NAMES)))
    xy = np.zeros(len(FEATURE_NAMES))
    observations = 0
    for tape in tapes:
        count = len(tape) - latency - horizon
        if count <= 0:
            continue
        x = np.array([depth_features(e.bids, e.asks, scale) for e in tape[:count]])
        y = np.array([tape[i + latency + horizon].mid - tape[i + latency].mid
                      for i in range(count)])
        xx += x.T @ x
        xy += x.T @ y
        observations += count
    if not observations:
        raise ValueError("training tapes are shorter than the label horizon")
    coefficients = np.linalg.solve(xx + ridge * np.eye(len(FEATURE_NAMES)), xy)
    return DepthForecast(tuple(float(c) for c in coefficients), scale, horizon,
                         latency, ridge, observations)


def cross_book(ledger: Ledger, quantity: int, event: TapeEvent, fee: float) -> tuple[int, float]:
    """Sweep displayed prices; charge fees and depth-dependent slippage."""
    direction = 1 if quantity > 0 else -1
    depths = event.asks if direction == 1 else event.bids
    remaining, shortfall = abs(quantity), 0.0
    for level, depth in enumerate(depths):
        fill = min(remaining, depth)
        if fill:
            offset = level + 0.5
            ledger.trade(direction * fill, event.mid + direction * offset, fee)
            shortfall += fill * offset
            remaining -= fill
        if not remaining:
            break
    return direction * (abs(quantity) - remaining), shortfall


def replay_alpha(tape: tuple[TapeEvent, ...], scenario: Scenario, model: DepthForecast,
                 margin: float = 0.5, size: int = 1) -> tuple[dict, pd.DataFrame]:
    """Hold one position for the forecast horizon; never add to a losing trade.

    Entry and exit instructions incur the same configured latency. A neutral
    forecast means cash. A pending order is not reconsidered using future data.
    The final event is reserved for a real displayed-depth liquidation.
    """
    if not tape or size < 1 or margin < 0 or not math.isfinite(margin):
        raise ValueError("invalid strategy settings")
    if model.latency != scenario.latency or scenario.fee < 0:
        raise ValueError("forecast latency must match execution; fee must be non-negative")
    ledger = Ledger()
    pending_entry = None
    exit_due = None
    shortfall = peak = drawdown = 0.0
    predictions = [model.predict(e.bids, e.asks) for e in tape]
    round_trips = 0
    rows = []
    required_edge = 1.0 + 2 * scenario.fee + margin
    for i, event in enumerate(tape):
        did_exit = False
        # Exit is committed to a holding horizon at entry decision time. There
        # is no favorable-price waiting rule and no knowledge of future returns.
        if (exit_due is not None and i >= exit_due) or i == len(tape) - 1:
            if ledger.inventory:
                _, cost = cross_book(ledger, -ledger.inventory, event, scenario.fee)
                shortfall += cost
                if not ledger.inventory:
                    round_trips += 1
            if not ledger.inventory:
                exit_due = None
            did_exit = True
            if i == len(tape) - 1:
                pending_entry = None
        if pending_entry is not None and pending_entry[0] <= i:
            _, quantity = pending_entry
            _, cost = cross_book(ledger, quantity, event, scenario.fee)
            shortfall += cost
            pending_entry = None
        if (not ledger.inventory and pending_entry is None and exit_due is None and not did_exit
                and i + model.latency + model.horizon < len(tape) - 1):
            forecast = predictions[i]
            if abs(forecast) > required_edge:
                quantity = size if forecast > 0 else -size
                exit_due = i + model.latency + model.horizon
                if model.latency:
                    pending_entry = (i + model.latency, quantity)
                else:
                    _, cost = cross_book(ledger, quantity, event, scenario.fee)
                    shortfall += cost
        equity = ledger.cash + ledger.inventory * event.after
        peak = max(peak, equity)
        drawdown = max(drawdown, peak - equity)
        rows.append(dict(event=i, mid=event.after, inventory=ledger.inventory, equity=equity,
                         realized=ledger.realized, unrealized=ledger.unrealized(event.after),
                         fees=ledger.fees, fills=ledger.fills, forecast=predictions[i],
                         required_edge=required_edge))
    # A shallow final ladder can leave residual inventory for large clip sizes;
    # never silently mark it as liquidated. The standard one-share clip exits.
    if ledger.inventory:
        raise ValueError("insufficient final displayed liquidity to liquidate; reduce size")
    return dict(pnl=ledger.cash, liquidation_pnl=ledger.cash, realized=ledger.realized,
                unrealized=0.0, fees=ledger.fees, drawdown=drawdown, fills=ledger.fills,
                volume=ledger.volume, final_inventory=0,
                mean_abs_inventory=sum(abs(r["inventory"]) for r in rows) / len(rows),
                round_trips=round_trips, execution_shortfall=shortfall,
                gross_mid_pnl=ledger.cash + ledger.fees + shortfall), pd.DataFrame(rows)
