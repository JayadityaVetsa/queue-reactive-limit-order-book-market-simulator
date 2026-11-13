"""Train, freeze, and evaluate a cost-gated depth-forecast strategy."""
from __future__ import annotations

import argparse
from dataclasses import replace
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

from lob_sim.alpha_strategy import DepthForecast, fit_forecast, replay_alpha
from lob_sim.market_making import SCENARIOS, make_tape, replay


ROOT = Path(__file__).resolve().parents[1]
POLICIES = ("fixed", "inventory", "alpha", "opposite_signal")
TOLERANCE = 1e-7


def source_hashes():
    files = sorted((ROOT / "src/lob_sim").glob("*.py")) + [Path(__file__)]
    # Git checkouts can change line endings and path separators across hosts.
    # Hash canonical source text so a frozen policy remains usable on Linux.
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
            for p in files}


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def load_model(value):
    return DepthForecast(**{key: value[key] for key in
                            ("coefficients", "volume_scale", "horizon", "latency", "ridge", "observations")})


def prepare(args):
    training_seeds = list(range(100, 100 + args.train_seeds))
    validation_seeds = list(range(200, 200 + args.validation_seeds))
    tapes = [make_tape(sc, seed, args.train_events) for sc in SCENARIOS for seed in training_seeds]
    models = {lag: fit_forecast(tapes, horizon=20, latency=lag) for lag in (0, 8)}
    print("Fitted depth-only forecasts; validating four cost margins.", flush=True)
    candidates = (0.0, 0.25, 0.5, 0.75)
    rows = []
    for sc in SCENARIOS:
        for seed in validation_seeds:
            tape = make_tape(sc, seed, args.events)
            for margin in candidates:
                result, _ = replay_alpha(tape, sc, models[sc.latency], margin=margin)
                rows.append(dict(scenario=sc.name, seed=seed, margin=margin, **result))
    validation = pd.DataFrame(rows)
    validation.to_csv(args.output / "validation.csv", index=False)
    scores = validation.groupby("margin").liquidation_pnl.mean()
    best = float(scores.idxmax())
    active = bool(scores.loc[best] > 0)
    frozen = dict(models={str(k): v.to_dict() for k, v in models.items()}, margin=best,
                  active=active, training_seeds=training_seeds, validation_seeds=validation_seeds,
                  train_events=args.train_events, validation_events=args.events,
                  development_seeds=[30, 31, 40, 41, 42, 50, 51, 52, 53, 54],
                  candidate_margins=candidates, selection="maximum mean validation net P&L; cash if all <= 0",
                  validation_scores={str(k): float(v) for k, v in scores.items()},
                  clip_size=1, horizon=20, ridge=10.0, source_sha256=source_hashes())
    write_json(args.output / "frozen_policy.json", frozen)
    print(f"Frozen margin={best:g}, active={active}; validation mean={scores.loc[best]:.3f} tick-shares.", flush=True)


def cash_result(tape):
    result, path = replay_alpha(tape, replace(SCENARIOS[0], latency=0),
                                DepthForecast((0.0,) * 16, 18.0, 20, 0, 10.0, 0))
    return result, path


def evaluate(args):
    frozen_path = args.output / "frozen_policy.json"
    frozen_bytes = frozen_path.read_bytes()
    frozen = json.loads(frozen_bytes)
    if frozen["source_sha256"] != source_hashes():
        raise ValueError("implementation changed since policy freeze; prepare again before evaluation")
    seeds = list(range(3000, 3000 + args.seeds))
    assert not set(seeds).intersection(frozen["training_seeds"] + frozen["validation_seeds"])
    models = {int(k): load_model(v) for k, v in frozen["models"].items()}
    rows, paths, tape_hashes = [], {}, {}
    for sc in SCENARIOS:
        for seed in seeds:
            tape = make_tape(sc, seed, args.events)
            tape_hashes[f"{sc.name}:{seed}"] = hashlib.sha256(repr(tape).encode()).hexdigest()
            for policy in POLICIES:
                if policy in ("fixed", "inventory"):
                    result, path = replay(tape, sc, size=1, limit=8,
                                          skew=0.0 if policy == "fixed" else 0.5)
                elif not frozen["active"]:
                    result, path = cash_result(tape)
                else:
                    model = models[sc.latency]
                    if policy == "opposite_signal":
                        model = replace(model, coefficients=tuple(-x for x in model.coefficients))
                    result, path = replay_alpha(tape, sc, model, margin=frozen["margin"])
                rows.append(dict(scenario=sc.name, seed=seed, policy=policy, **result))
                if seed == seeds[0]:
                    path.to_csv(args.output / f"path_{sc.name}_{policy}.csv", index=False)
                    paths[sc.name, policy] = path
        print(f"Evaluated {sc.name} on {len(seeds)} fresh seeds.", flush=True)
    runs = pd.DataFrame(rows)
    runs.to_csv(args.output / "runs.csv", index=False)
    summary_rows = []
    for (scenario, policy), group in runs.groupby(["scenario", "policy"]):
        p = group.liquidation_pnl
        summary_rows.append(dict(scenario=scenario, policy=policy, mean_pnl=float(p.mean()),
                                 median_pnl=float(p.median()), p10_pnl=float(p.quantile(0.1)),
                                 worst_pnl=float(p.min()), best_pnl=float(p.max()),
                                 profitable=int((p > TOLERANCE).sum()), losing=int((p < -TOLERANCE).sum()),
                                 flat=int((p.abs() <= TOLERANCE).sum()), runs=len(p),
                                 win_rate=float((p > TOLERANCE).mean()),
                                 mean_volume=float(group.volume.mean()), mean_fees=float(group.fees.mean()),
                                 mean_drawdown=float(group.drawdown.mean()),
                                 mean_abs_inventory=float(group.mean_abs_inventory.mean())))
    summary = pd.DataFrame(summary_rows).set_index(["scenario", "policy"])
    summary.to_csv(args.output / "summary.csv")
    paired = runs.pivot(index=["scenario", "seed"], columns="policy", values="liquidation_pnl")
    paired["alpha_minus_inventory"] = paired.alpha - paired.inventory
    paired.to_csv(args.output / "paired.csv")
    manifest = dict(events=args.events, evaluation_seeds=seeds,
                    frozen_policy_sha256=hashlib.sha256(frozen_bytes).hexdigest(),
                    source_sha256=source_hashes(), tape_sha256=tape_hashes,
                    python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__,
                    win_tolerance=TOLERANCE, terminal="actual depth-sweeping exit for alpha; estimate for makers",
                    baseline_clip=1, baseline_inventory_cap=8, baseline_inventory_skew=0.5,
                    pooled_interval="seed-cluster bootstrap; all eight scenarios travel together")
    write_json(args.output / "manifest.json", manifest)
    plot_results(args, runs, summary, paths)
    write_report(args, frozen, runs, summary, paired)


def plot_results(args, runs, summary, paths):
    fig = make_subplots(rows=2, cols=2, subplot_titles=(
        "Net P&L after fees and liquidation", "Profitable runs · flat runs count as failures",
        "Combined stress · first evaluation seed", "Combined stress · position"))
    colors = {"fixed": "#687c91", "inventory": "#b78555", "alpha": "#087f75", "opposite_signal": "#ad4c58"}
    order = [s.name for s in SCENARIOS]
    for policy in POLICIES:
        frame = summary.xs(policy, level="policy").reindex(order)
        fig.add_trace(go.Bar(x=order, y=frame.mean_pnl, name=policy, marker_color=colors[policy]), row=1, col=1)
        fig.add_trace(go.Bar(x=order, y=100 * frame.win_rate, name=policy,
                             marker_color=colors[policy], showlegend=False), row=1, col=2)
        for col, metric in ((1, "equity"), (2, "inventory")):
            path = paths["combined", policy]
            fig.add_trace(go.Scatter(x=path.event, y=path[metric], name=policy,
                                     line_color=colors[policy], showlegend=False), row=2, col=col)
    fig.update_layout(template="plotly_white", barmode="group", height=900,
                      title="Can a depth forecast cover the cost of trading?", font=dict(family="Arial", size=12))
    fig.update_yaxes(title_text="tick-shares", row=1, col=1)
    fig.update_yaxes(title_text="percent", range=[0, 105], row=1, col=2)
    fig.write_html(args.output / "comparison.html", include_plotlyjs=True)


def write_report(args, frozen, runs, summary, paired):
    alpha = runs[runs.policy == "alpha"]
    p = alpha.liquidation_pnl
    wins, losses, flats = int((p > TOLERANCE).sum()), int((p < -TOLERANCE).sum()), int((p.abs() <= TOLERANCE).sum())
    # Same seed drives correlated scenario paths. Resample seed clusters, not
    # individual scenario rows, when describing the pooled success fraction.
    clusters = alpha.assign(win=p > TOLERANCE).groupby("seed").win.mean().to_numpy()
    rng = np.random.default_rng(711)
    interval = np.quantile(rng.choice(clusters, size=(10000, len(clusters)), replace=True).mean(axis=1), [0.025, 0.975])
    lines = ["# Cost-gated order-book forecast", "",
             f"**Positive net P&L in {wins}/{len(p)} runs ({wins / len(p):.1%}); {losses} losses and {flats} flat runs.**",
             f"Mean net P&L: {p.mean():.2f} tick-shares; median: {p.median():.2f}; worst: {p.min():.2f}. "
             f"The seed-cluster bootstrap interval for the pooled profitable fraction is {interval[0]:.1%}–{interval[1]:.1%}.", "",
             "This evaluates a directional liquidity-taking strategy in the existing synthetic market. It does not establish a real-market trading edge. A flat or no-trade run is never counted as profitable.", "",
             "## What changed", "",
             "The earlier maker received fills with strongly negative subsequent markouts. Simply widening quotes did not reliably repair that on development tapes. The new policy predicts a 20-event midprice change from the displayed bid/ask depths. It crosses the spread only when that forecast exceeds a full round-trip spread, both fees, and a validation-selected safety margin. It then exits on a predetermined schedule, whether the trade won or lost.", "",
             f"Frozen margin: **{frozen['margin']:g} ticks**, with active trading **{frozen['active']}**. "
             "One-share positions keep the experiment small relative to displayed depth. Buys and sells sweep the actual visible ladder and pay per-share fees. Both entry and exit incur the configured latency. The forecast is trained on returns measured after that latency, so it cannot assume an old signal survives unchanged.", "",
             "## Fresh evaluation", "",
             f"{args.seeds} seeds per scenario, {args.events} events per run. Seeds begin at 3000. "
             "All policies see identical tapes. The old makers are scaled to one-share quotes and an eight-share cap; their inventory skew is scaled to 0.5 ticks/share. The new strategy voluntarily holds at most one share. Cash earns zero and is included as the economic hurdle.", "",
             "| Scenario | Profitable / total | Mean alpha P&L | Median | Worst | Fixed maker mean | Inventory maker mean | Opposite-signal mean |",
             "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for sc in SCENARIOS:
        a = summary.loc[sc.name, "alpha"]
        lines.append(f"| {sc.name} | {int(a.profitable)}/{int(a.runs)} | {a.mean_pnl:.2f} | {a.median_pnl:.2f} | {a.worst_pnl:.2f} | "
                     f"{summary.loc[(sc.name, 'fixed'), 'mean_pnl']:.2f} | {summary.loc[(sc.name, 'inventory'), 'mean_pnl']:.2f} | "
                     f"{summary.loc[(sc.name, 'opposite_signal'), 'mean_pnl']:.2f} |")
    mean_bad = [s.name for s in SCENARIOS if summary.loc[(s.name, "alpha"), "mean_pnl"] <= 0]
    majority_bad = [s.name for s in SCENARIOS if summary.loc[(s.name, "alpha"), "win_rate"] <= 0.5]
    lines += ["", "## Failures and uncertainty", "",
              "Scenarios with nonpositive average alpha P&L: " + (", ".join(mean_bad) or "none") + ".",
              "Scenarios without a strict majority of profitable runs: " + (", ".join(majority_bad) or "none") + ".", "",
              "Latency can erase the forecast before execution. Higher fees leave fewer viable entries. A positive pooled result can coexist with losses in stress regimes; inspect those rows rather than reporting only the aggregate success rate. The opposite-signal control enters on the same absolute forecast triggers and follows the same holding schedule, but flips direction. It tests whether the learned sign adds value beyond trade timing and small position size.", "",
              "## Research separation", "",
              f"Training seeds: {frozen['training_seeds']}. Validation seeds: {frozen['validation_seeds']}. "
              "Development probes used seeds 30–31, 40–42 and 50–54. Earlier market-making evaluation seeds 1000–1019 and 2000–2019 were already seen and are excluded from this final evaluation.", "",
              "Depth features use one-, two-, four- and eight-level imbalance, per-level log-depth differences and nonlinear sweep-depth features. Their volume scale comes from training data. Ridge regression (penalty 10) is fixed in advance. Separate latency-zero and latency-eight models use the same training tapes, with latency-aligned labels. No scenario name, next order, future depth or future price is a prediction input. Labels use strictly future prices from training tapes only. Complete paths, not interleaved rows, are allocated to splits.", "",
              "Four margins (0, 0.25, 0.5 and 0.75 ticks) are ranked by average validation net P&L across all scenarios. If none beats cash, the frozen policy abstains. The coefficient files, selection scores and implementation hashes are written before evaluating seeds 3000 onward. The model and selected margin remain unchanged throughout evaluation.", "",
              "## Model dependence", "",
              "The generator mechanically moves its reference price when queues deplete and replenishes depth. Displayed depth therefore contains predictive information by construction. The strategy monetizes that simulated relationship; the opposite-signal control does not turn it into empirical evidence. Future work needs external event data, a price-time-priority venue, impact, physical timestamps, and out-of-sample validation across real trading days. The one-share clip also means these results say nothing about capacity.", "",
              "The background market, informed-flow mechanism, volatility, latency and fees were not softened to obtain this result. The old shadow-maker execution remains conservative and separate. The new taker exits against visible depth rather than marking a residual position favorably. All reported profits include spread crossing, depth slippage and fees. No martingale sizing, averaging down, price-dependent exit delay, future-price entry signal, or annualized return is used.", "",
              "## Reproduce", "", "```bash", "python scripts/alpha_experiment.py --stage prepare",
              "python scripts/alpha_experiment.py --stage evaluate", "```", "",
              "Open comparison.html for plots. frozen_policy.json contains the deployable coefficients and selected margin. validation.csv preserves every candidate result. runs.csv includes every evaluation run; summary.csv includes win/loss/flat counts, fees, volume, drawdown and inventory. paired.csv preserves comparisons by seed. manifest.json records source hashes, frozen-policy digest and tape digests. Example path CSVs always use the first evaluation seed.", ""]
    (args.output / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Final alpha: {wins}/{len(p)} profitable, mean={p.mean():.3f} tick-shares.", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("prepare", "evaluate", "all"), default="all")
    parser.add_argument("--events", type=int, default=4000)
    parser.add_argument("--train-events", type=int, default=3000)
    parser.add_argument("--train-seeds", type=int, default=5)
    parser.add_argument("--validation-seeds", type=int, default=5)
    parser.add_argument("--seeds", type=int, default=50)
    parser.add_argument("--output", type=Path, default=Path("reports/alpha"))
    args = parser.parse_args()
    if min(args.events, args.train_events) < 100 or min(args.train_seeds, args.validation_seeds, args.seeds) < 2:
        parser.error("at least 100 events and two seeds per split are required")
    if args.train_seeds > 100 or args.validation_seeds > 100:
        parser.error("at most 100 seeds per development split; keep the seed ranges disjoint")
    args.output.mkdir(parents=True, exist_ok=True)
    if args.stage in ("prepare", "all"):
        prepare(args)
    if args.stage in ("evaluate", "all"):
        evaluate(args)


if __name__ == "__main__":
    main()
