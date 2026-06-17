"""Validation metrics comparing simulated and empirical LOB statistics."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ValidationResult:
    metrics: dict[str, float]
    passed: bool


class Validator:
    """Compute stylized-fact validation metrics."""

    def compare_snapshots(
        self, simulated: pd.DataFrame, empirical: pd.DataFrame, tolerance: float = 0.10
    ) -> ValidationResult:
        keys = ["spread_ticks", "bid_depth", "ask_depth", "imbalance"]
        metrics: dict[str, float] = {}
        passed_items = []
        for key in keys:
            sim = simulated[key].astype(float).to_numpy()
            emp = empirical[key].astype(float).to_numpy()
            sim_mean = float(np.mean(sim))
            emp_mean = float(np.mean(emp))
            rel_error = (
                abs(sim_mean - emp_mean)
                if key == "imbalance"
                else abs(sim_mean - emp_mean) / max(abs(emp_mean), 1e-9)
            )
            ks_pvalue = _ks_2samp_pvalue(sim, emp) if len(sim) > 1 and len(emp) > 1 else 1.0
            metrics[f"{key}_sim_mean"] = sim_mean
            metrics[f"{key}_emp_mean"] = emp_mean
            metrics[f"{key}_rel_error"] = rel_error
            metrics[f"{key}_ks_pvalue"] = ks_pvalue
            passed_items.append(rel_error <= tolerance)
        return ValidationResult(metrics=metrics, passed=all(passed_items))

    def summarize_events(self, events: pd.DataFrame) -> dict[str, float]:
        if events.empty:
            return {"event_count": 0.0}
        counts = events["event_type"].astype(str).value_counts(normalize=True)
        return {
            "event_count": float(len(events)),
            "limit_share": float(counts.get("limit", 0.0)),
            "market_share": float(counts.get("market", 0.0)),
            "cancel_share": float(counts.get("cancel", 0.0)),
        }


def _ks_2samp_pvalue(sample_a: np.ndarray, sample_b: np.ndarray) -> float:
    """Approximate the two-sample Kolmogorov-Smirnov p-value.

    This keeps the simulator lightweight for local demos while preserving the
    validation signal used in the research notes.
    """

    a = np.sort(sample_a)
    b = np.sort(sample_b)
    values = np.concatenate([a, b])
    cdf_a = np.searchsorted(a, values, side="right") / len(a)
    cdf_b = np.searchsorted(b, values, side="right") / len(b)
    statistic = float(np.max(np.abs(cdf_a - cdf_b)))
    effective_n = len(a) * len(b) / (len(a) + len(b))
    return float(np.clip(2.0 * np.exp(-2.0 * effective_n * statistic * statistic), 0.0, 1.0))
