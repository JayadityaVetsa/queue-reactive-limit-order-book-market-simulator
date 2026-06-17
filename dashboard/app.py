"""Beginner-friendly Streamlit dashboard for the queue-reactive LOB simulator."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_DIR = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(DASHBOARD_DIR) not in sys.path:
    sys.path.insert(0, str(DASHBOARD_DIR))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lob_sim.simulator import QueueReactiveSimulator, SimulationConfig  # noqa: E402
from lob_sim.types import Side  # noqa: E402
from guide_content import render_research_guide  # noqa: E402


st.set_page_config(page_title="Queue-Reactive LOB Simulator", layout="wide")

st.markdown(
    """
    <style>
    .main .block-container {padding-top: 1.25rem; max-width: 1320px;}
    div[data-testid="metric-container"] {
        border: 1px solid #dde3ea; border-radius: 8px; padding: 12px;
        background: #fbfcfe;
    }
    .small-note {
        color: #46515f; font-size: 0.94rem; line-height: 1.45;
        border-left: 4px solid #1565c0; padding: 0.55rem 0.8rem;
        background: #f6f9fd; border-radius: 4px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def build_ladder_frame(sim: QueueReactiveSimulator) -> pd.DataFrame:
    rows = []
    for level in range(sim.book.levels, 0, -1):
        rows.append(
            {
                "Side": "Ask",
                "Level": level,
                "Price": sim.book.price_at(Side.ASK, level),
                "Volume": sim.book.asks[level - 1],
            }
        )
    for level in range(1, sim.book.levels + 1):
        rows.append(
            {
                "Side": "Bid",
                "Level": level,
                "Price": sim.book.price_at(Side.BID, level),
                "Volume": sim.book.bids[level - 1],
            }
        )
    return pd.DataFrame(rows)


def event_mix(events: pd.DataFrame) -> pd.DataFrame:
    if events.empty:
        return pd.DataFrame({"event_type": [], "count": []})
    return (
        events["event_type"]
        .value_counts()
        .rename_axis("event_type")
        .reset_index(name="count")
        .sort_values("event_type")
    )


with st.sidebar:
    page = st.radio(
        "Page",
        ["Simulator", "Research Guide"],
        help="Use Research Guide for the beginner walkthrough. Use Simulator to run the fake market.",
    )
    if page == "Research Guide":
        render_research_guide()
        st.stop()
    st.divider()
    st.header("Run A Fake Market")
    st.caption("These controls create a simulated order book. This is not live market data and no ticker is being priced.")

    seed = st.number_input(
        "Seed",
        min_value=1,
        max_value=1_000_000,
        value=7,
        help="A repeatable random starting point. Use the same seed to reproduce the exact same fake market path.",
    )
    duration = st.slider(
        "Duration",
        60,
        3600,
        600,
        step=60,
        help="How many simulated seconds the fake market runs.",
    )
    max_events = st.slider(
        "Max events",
        1_000,
        100_000,
        25_000,
        step=1_000,
        help="The maximum number of order book events: new orders, cancellations, and market orders.",
    )
    levels = st.slider(
        "Book levels",
        2,
        10,
        5,
        help="How many price steps to track on each side. Level 1 is closest to the current market price.",
    )
    initial_depth = st.slider(
        "Initial depth",
        20,
        500,
        100,
        step=10,
        help="How much buy and sell volume starts at each price level. Higher depth means a thicker, harder-to-move market.",
    )
    mean_order_size = st.slider(
        "Mean order size",
        1,
        50,
        12,
        help="The typical size of each fake order. Larger orders remove or add more volume at once.",
    )
    base_limit_rate = st.slider(
        "Limit order rate",
        1.0,
        20.0,
        8.0,
        step=0.5,
        help="How often new resting buy/sell orders arrive and add liquidity to the book.",
    )
    base_market_rate = st.slider(
        "Market order rate",
        0.5,
        10.0,
        2.4,
        step=0.1,
        help="How often aggressive orders arrive and consume liquidity immediately.",
    )
    base_cancel_rate = st.slider(
        "Cancel rate",
        0.5,
        10.0,
        2.1,
        step=0.1,
        help="How often resting orders disappear before trading. High cancellation makes liquidity less stable.",
    )
    run = st.button("Run simulation", type="primary", width="stretch")

config = SimulationConfig(
    seed=int(seed),
    duration=float(duration),
    max_events=int(max_events),
    levels=int(levels),
    initial_depth=int(initial_depth),
    replenish_depth=int(initial_depth),
    mean_order_size=float(mean_order_size),
    base_limit_rate=float(base_limit_rate),
    base_market_rate=float(base_market_rate),
    base_cancel_rate=float(base_cancel_rate),
)

if run or "sim" not in st.session_state:
    st.session_state.sim = QueueReactiveSimulator(config).run()

sim = st.session_state.sim
snapshots = sim.snapshots_df()
events = sim.events_df()
trades = sim.trades_df()
stats = sim.statistics()
ladder = build_ladder_frame(sim)

st.title("Queue-Reactive Limit Order Book Simulator")
st.info("New here? Choose `Research Guide` in the sidebar Page selector for the beginner walkthrough.")
st.markdown(
    """
    <div class="small-note">
    This is a fake exchange simulator. You do not enter a stock ticker here, and it does not estimate a company's value.
    It shows how orders queue up, cancel, trade, and sometimes push the simulated price up or down.
    </div>
    """,
    unsafe_allow_html=True,
)

with st.expander("Start here: what am I looking at?", expanded=True):
    st.write(
        "A limit order book is a queue of people willing to buy below the market and sell above the market. "
        "This dashboard lets you change how busy, thin, or aggressive the fake market is, then watch the book evolve."
    )
    st.dataframe(
        pd.DataFrame(
            [
                ["Limit order", "Adds liquidity", "Someone waits in line to buy or sell at a chosen price."],
                ["Market order", "Removes liquidity", "Someone wants to trade now and consumes the best available queue."],
                ["Cancel", "Removes liquidity", "Someone leaves the queue before trading."],
                ["Price move", "Best queue depleted", "If the nearest buy or sell queue is emptied, the midprice moves one tick."],
            ],
            columns=["Thing", "Effect", "Plain English"],
        ),
        width="stretch",
        hide_index=True,
    )

metric_cols = st.columns(6)
metric_cols[0].metric("Events", f"{int(stats['events']):,}", help="Total simulated order book events processed.")
metric_cols[1].metric("Trades", f"{int(stats['trades']):,}", help="Executions caused by market orders.")
metric_cols[2].metric("Price moves", f"{int(stats['price_moves']):,}", help="How many times a best bid or ask queue was depleted.")
metric_cols[3].metric("Final midprice", f"{stats['final_midprice']:.2f}", help="The fake midprice at the end of the run.")
metric_cols[4].metric("Mean bid depth", f"{stats['mean_bid_depth']:.1f}", help="Average total buy-side volume across tracked levels.")
metric_cols[5].metric("Mean ask depth", f"{stats['mean_ask_depth']:.1f}", help="Average total sell-side volume across tracked levels.")

tab_overview, tab_book, tab_events, tab_trades = st.tabs(
    ["Market Story", "Order Book", "Events", "Trades"]
)

with tab_overview:
    left, right = st.columns([1.35, 1.0])
    with left:
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=snapshots["timestamp"],
                y=snapshots["midprice"],
                mode="lines",
                name="Midprice",
                line=dict(color="#1565c0", width=2),
            )
        )
        fig.update_layout(
            title="Fake Midprice Path",
            height=380,
            margin=dict(l=10, r=10, t=45, b=10),
            xaxis_title="Simulated seconds",
            yaxis_title="Midprice",
        )
        st.plotly_chart(fig, width="stretch")
        st.caption("The midprice moves only when the nearest buy or sell queue is depleted.")

    with right:
        mix = event_mix(events)
        mix_fig = go.Figure(
            go.Bar(
                x=mix["event_type"],
                y=mix["count"],
                marker_color=["#2e7d32", "#1565c0", "#c62828"][: len(mix)],
            )
        )
        mix_fig.update_layout(
            title="What Kind Of Events Happened?",
            height=380,
            margin=dict(l=10, r=10, t=45, b=10),
            xaxis_title="Event type",
            yaxis_title="Count",
        )
        st.plotly_chart(mix_fig, width="stretch")
        st.caption("Limit orders add liquidity. Market orders and cancels remove it.")

    depth_fig = go.Figure()
    depth_fig.add_trace(
        go.Scatter(
            x=snapshots["timestamp"],
            y=snapshots["bid_depth"],
            mode="lines",
            name="Buy-side depth",
            line=dict(color="#0f9d58"),
        )
    )
    depth_fig.add_trace(
        go.Scatter(
            x=snapshots["timestamp"],
            y=snapshots["ask_depth"],
            mode="lines",
            name="Sell-side depth",
            line=dict(color="#c62828"),
        )
    )
    depth_fig.update_layout(
        title="Liquidity Through Time",
        height=330,
        margin=dict(l=10, r=10, t=45, b=10),
        xaxis_title="Simulated seconds",
        yaxis_title="Queued volume",
        legend=dict(orientation="h"),
    )
    st.plotly_chart(depth_fig, width="stretch")

with tab_book:
    st.subheader("Current Fake Order Book")
    st.write(
        "The nearest ask queue is the cheapest place to buy immediately. "
        "The nearest bid queue is the highest place to sell immediately."
    )
    bid_rows = ladder[ladder["Side"] == "Bid"].copy()
    ask_rows = ladder[ladder["Side"] == "Ask"].copy()

    book_fig = go.Figure()
    book_fig.add_trace(
        go.Bar(
            y=[f"Bid L{row.Level} @ {row.Price:.2f}" for row in bid_rows.itertuples()],
            x=-bid_rows["Volume"],
            orientation="h",
            name="Bid volume",
            marker_color="#0f9d58",
        )
    )
    book_fig.add_trace(
        go.Bar(
            y=[f"Ask L{row.Level} @ {row.Price:.2f}" for row in ask_rows.itertuples()],
            x=ask_rows["Volume"],
            orientation="h",
            name="Ask volume",
            marker_color="#c62828",
        )
    )
    book_fig.update_layout(
        title="Book Ladder: Buy Queues Left, Sell Queues Right",
        height=430,
        barmode="relative",
        margin=dict(l=10, r=10, t=45, b=10),
        xaxis_title="Volume in queue",
        legend=dict(orientation="h"),
    )
    st.plotly_chart(book_fig, width="stretch")
    st.dataframe(ladder, width="stretch", hide_index=True)

with tab_events:
    st.subheader("Recent Simulated Events")
    st.write("Each row is one fake market action generated by the simulator.")
    st.dataframe(events.tail(500), width="stretch", hide_index=True)
    st.dataframe(
        pd.DataFrame(
            [
                ["timestamp", "When the event happened in simulated seconds."],
                ["event_type", "limit adds liquidity; market consumes liquidity; cancel removes resting liquidity."],
                ["side", "For limit/cancel, the affected side. For market, the aggressor side."],
                ["level", "Price level affected. Level 1 is closest to the current price."],
                ["volume", "Number of fake shares/contracts in the event."],
            ],
            columns=["Column", "Meaning"],
        ),
        width="stretch",
        hide_index=True,
    )

with tab_trades:
    st.subheader("Trades Created By Market Orders")
    if trades.empty:
        st.info("No trades were generated in this run. Increase market order rate or duration.")
    else:
        st.dataframe(trades.tail(500), width="stretch", hide_index=True)
    st.json(stats)

