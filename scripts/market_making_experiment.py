"""Run tuning and held-out comparisons; write the tables behind the report."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import platform
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from lob_sim.execution import NativeExecution, consume
from lob_sim.market_making import SCENARIOS, make_tape, replay


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--events", type=int, default=4000)
    parser.add_argument("--seeds", type=int, default=20)
    parser.add_argument("--output", type=Path, default=Path("reports/market_making"))
    parser.add_argument("--native", type=Path)
    args = parser.parse_args()
    if args.events < 100 or args.seeds < 2:
        parser.error("use at least 100 events and two evaluation seeds")
    args.output.mkdir(parents=True, exist_ok=True)
    executor = NativeExecution(args.native) if args.native else consume
    tuning_seeds = list(range(10, 15))
    evaluation_seeds = list(range(2000, 2000 + args.seeds))
    candidates = (0.0, 0.025, 0.05, 0.1)
    tuning = []
    for scenario in SCENARIOS[:4]:
        for seed in tuning_seeds:
            tape = make_tape(scenario, seed, args.events)
            for skew in candidates:
                result, _ = replay(tape, scenario, skew=skew, executor=executor)
                tuning.append(dict(scenario=scenario.name, seed=seed, skew=skew, **result))
    tuning_df = pd.DataFrame(tuning)
    # Explicit risk budget: penalize average inventory in tick-shares per step.
    tuning_df["objective"] = tuning_df.liquidation_pnl - 0.5 * tuning_df.mean_abs_inventory
    scores = tuning_df.groupby("skew").objective.mean()
    selected = float(scores.idxmax())
    tuning_df.to_csv(args.output / "tuning.csv", index=False)
    results, sample_paths, hashes = [], {}, {}
    for scenario in SCENARIOS:
        for seed in evaluation_seeds:
            tape = make_tape(scenario, seed, args.events)
            hashes[f"{scenario.name}:{seed}"] = hashlib.sha256(repr(tape).encode()).hexdigest()
            for policy, skew in (("fixed", 0.0), ("inventory", selected)):
                result, path = replay(tape, scenario, skew=skew, executor=executor)
                results.append(dict(scenario=scenario.name, seed=seed, policy=policy, **result))
                if seed == evaluation_seeds[0]:
                    path.to_csv(args.output / f"path_{scenario.name}_{policy}.csv", index=False)
                    sample_paths[scenario.name, policy] = path
    runs = pd.DataFrame(results)
    runs.to_csv(args.output / "runs.csv", index=False)
    summary = runs.groupby(["scenario", "policy"]).mean(numeric_only=True).drop(columns="seed")
    summary.to_csv(args.output / "summary.csv")
    paired = runs.pivot(index=["scenario", "seed"], columns="policy", values="liquidation_pnl")
    paired["difference"] = paired.inventory - paired.fixed
    paired.to_csv(args.output / "paired.csv")
    fig = make_subplots(rows=2, cols=2, subplot_titles=("Held-out liquidation P&L", "Average absolute inventory", "Combined stress · seed 2000", "Inventory · same path"))
    for policy, color in (("fixed", "#345b78"), ("inventory", "#bd6835")):
        means = summary.xs(policy, level="policy").reindex([s.name for s in SCENARIOS])
        for col, metric in ((1, "liquidation_pnl"), (2, "mean_abs_inventory")):
            fig.add_trace(go.Bar(x=means.index, y=means[metric], name=policy,
                                 marker_color=color, showlegend=col == 1), row=1, col=col)
        path = sample_paths["combined", policy]
        fig.add_trace(go.Scatter(x=path.event, y=path.equity, line_color=color,
                                name=policy, showlegend=False), row=2, col=1)
        fig.add_trace(go.Scatter(x=path.event, y=path.inventory, line_color=color,
                                name=policy, showlegend=False), row=2, col=2)
    fig.update_layout(template="plotly_white", title="Inventory control under execution frictions", height=850,
                      font=dict(family="Arial", size=12), barmode="group")
    fig.update_yaxes(title_text="tick-shares", row=1, col=1)
    fig.update_yaxes(title_text="shares", row=1, col=2)
    fig.write_html(args.output / "comparison.html", include_plotlyjs=True)
    manifest = dict(events=args.events, tuning_seeds=tuning_seeds, evaluation_seeds=evaluation_seeds,
                    candidates=candidates, selected_skew=selected,
                    objective="mean(liquidation_pnl - 0.5 * mean_abs_inventory)",
                    scenarios=[asdict(s) for s in SCENARIOS], python=platform.python_version(),
                    numpy=np.__version__, pandas=pd.__version__,
                    backend="native" if args.native else "python", tape_sha256=hashes)
    sources = list((Path(__file__).resolve().parents[1] / "src/lob_sim").glob("*.py"))
    sources += [Path(__file__), Path(__file__).resolve().parents[1] / "native/execution.cpp"]
    manifest["source_sha256"] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    lines = ["# Inventory control: held-out experiment", "",
             f"Selected skew: **{selected:g} ticks/share**. {args.seeds} held-out seeds per scenario; {args.events} events per run.", "",
             "The score was selected on seeds 10–14 using quiet, trend, and volatility scenarios. Seeds 1000–1019 were used during implementation debugging. Seeds 2000 onward were reserved for this final evaluation after those corrections. Stress scenarios were not used to tune the parameter.", "",
             "P&L is in tick-shares. Terminal liquidation charges half a tick plus the scenario fee on remaining inventory. Differences below are paired by seed; intervals are mean ± 1.96 standard errors, approximate rather than exact confidence guarantees.", "",
             "| Scenario | Fixed P&L | Inventory P&L | Paired difference ± 1.96 SE | Mean abs. inventory, fixed → inventory |", "|---|---:|---:|---:|---:|"]
    for scenario in SCENARIOS:
        name = scenario.name
        delta = paired.xs(name).difference
        fixed, inv = summary.loc[name, "fixed"], summary.loc[name, "inventory"]
        error = 1.96 * delta.std(ddof=1) / np.sqrt(len(delta))
        lines.append(f"| {name} | {fixed.liquidation_pnl:.1f} | {inv.liquidation_pnl:.1f} | {delta.mean():+.1f} ± {error:.1f} | {fixed.mean_abs_inventory:.1f} → {inv.mean_abs_inventory:.1f} |")
    winners = [s for s in paired.index.get_level_values(0).unique() if paired.xs(s).difference.mean() > 0]
    losers = [s for s in paired.index.get_level_values(0).unique() if paired.xs(s).difference.mean() < 0]
    lines += ["", "## Reading the result", "",
              "Positive average paired differences: " + (", ".join(winners) or "none") + ".",
              "Negative average paired differences: " + (", ".join(losers) or "none") + ".", "",
              f"The inventory policy underperformed the fixed policy in {int((paired.difference < 0).sum())} of {len(paired)} paired runs. It had negative liquidation P&L in {int(((runs.policy == 'inventory') & (runs.liquidation_pnl < 0)).sum())} of {int((runs.policy == 'inventory').sum())} runs. Reducing losses is not the same as establishing a profitable strategy.", "",
              "Inventory control changes which trades execute. Lower inventory alone is not evidence of better returns: skew can surrender spread income, and it can sell too early into a rising market or buy into a falling one. Inspect fees, drawdown and signed ten-event markouts in summary.csv alongside P&L. Negative markout means the price moved against the passive fill, including the entry spread.", "",
              "## Assumptions that can reverse the conclusion", "",
              "This is a shadow-order experiment on synthetic flow. Quotes join behind displayed background depth. Market volume must clear better prices and queue ahead; touching a quote is insufficient. Cancellations receive no queue credit. Replacements lose priority. One replacement may be in flight; the previous quote remains executable until arrival. The inventory cap applies to both policies and is checked again at execution.", "",
              "The background book replenishes mechanically. Volatility and drift additionally translate the reference ladder; informed flow is correlated with those subsequent moves. This mechanism is deliberately a stress test, not a fitted price model. The maker does not alter price formation or other traders' decisions. The eight-level ladder bounds eligible quote placement; terminal liquidation ignores depth and impact. Event latency has no calibrated mapping to microseconds. Drawdown uses marked equity before hypothetical terminal liquidation. No capital-based return or annualized Sharpe is reported.", "",
              "## Reproduce and inspect", "",
              "Run `python scripts/market_making_experiment.py` from the project root. Open comparison.html for interactive plots. runs.csv contains every evaluation result; tuning.csv contains every candidate; paired.csv preserves seed pairing; manifest.json records settings, tape digests, source hashes and versions. Path CSVs show the first held-out seed, not a selected best path. A selected skew of zero means tuning preferred the baseline; do not replace it to manufacture an improvement.", ""]
    (args.output / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Selected skew={selected:g}; wrote {args.output / 'REPORT.md'}")


if __name__ == "__main__":
    main()
