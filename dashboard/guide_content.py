"""Shared Research Guide content for the Streamlit dashboard."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lob_sim.simulator import QueueReactiveSimulator, SimulationConfig  # noqa: E402


def render_research_guide() -> None:
    """Render the beginner research guide."""

    st.title("Research Guide: What This Simulator Is Actually Doing")

    st.warning(
        "This project uses a fake, simulated order book. It is not connected to live market data, "
        "does not accept stock tickers, and does not estimate what a company is worth."
    )

    st.markdown(
        """
        This tool is about **market mechanics**. It helps you study how orders arrive,
        wait in queues, cancel, trade, and sometimes move the price.

        A normal investing question might be: *Is this stock cheap or expensive?*

        This simulator asks a different question: *If I try to trade, what might happen inside
        the exchange queue before I get filled?*
        """
    )

    st.header("1. The Order Book In Plain English")

    col_text, col_table = st.columns([1.05, 1.1])
    with col_text:
        st.write(
            "A limit order book is a stack of buy queues and sell queues. "
            "Buyers wait below the current market. Sellers wait above it. "
            "The closest buy queue is called the best bid. The closest sell queue is called the best ask."
        )
        st.markdown(
            """
            - **Bid**: someone waiting to buy.
            - **Ask**: someone waiting to sell.
            - **Spread**: the gap between best bid and best ask.
            - **Depth**: how much volume is waiting in the queues.
            - **Midprice**: halfway between best bid and best ask.
            """
        )

    with col_table:
        toy_book = pd.DataFrame(
            [
                ["Ask", 3, "$100.03", 80],
                ["Ask", 2, "$100.02", 110],
                ["Ask", 1, "$100.01", 60],
                ["Bid", 1, "$99.99", 75],
                ["Bid", 2, "$99.98", 140],
                ["Bid", 3, "$99.97", 90],
            ],
            columns=["Side", "Level", "Price", "Queued volume"],
        )
        st.dataframe(toy_book, width="stretch", hide_index=True)

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=["Bid L3", "Bid L2", "Bid L1"],
            x=[-90, -140, -75],
            orientation="h",
            name="Buy queues",
            marker_color="#0f9d58",
        )
    )
    fig.add_trace(
        go.Bar(
            y=["Ask L1", "Ask L2", "Ask L3"],
            x=[60, 110, 80],
            orientation="h",
            name="Sell queues",
            marker_color="#c62828",
        )
    )
    fig.update_layout(
        title="Toy Book Ladder: Buyers Wait On The Left, Sellers Wait On The Right",
        barmode="relative",
        height=330,
        xaxis_title="Queued volume",
        margin=dict(l=10, r=10, t=45, b=10),
    )
    st.plotly_chart(fig, width="stretch")

    st.header("2. The Mathematical Book State")
    st.write("The simulator stores the book as queue sizes across multiple price levels:")
    st.latex(r"Q_t = (Q_t^{-K}, \ldots, Q_t^{-1}, Q_t^{1}, \ldots, Q_t^{K})")
    st.markdown(
        """
        The negative indices are bid queues. The positive indices are ask queues.
        `K` is the number of levels you choose in the dashboard.
        """
    )

    st.header("3. The Three Event Types")
    st.dataframe(
        pd.DataFrame(
            [
                ["Limit order", "Adds volume", "A trader joins a queue and waits."],
                ["Market order", "Consumes volume", "A trader wants to trade now and hits the opposite queue."],
                ["Cancel", "Removes volume", "A trader leaves the queue before trading."],
            ],
            columns=["Event", "Book effect", "Plain English"],
        ),
        width="stretch",
        hide_index=True,
    )

    st.write("In the model, each event type has an arrival intensity:")
    st.latex(r"\lambda_i(Q_t), \quad i \in \{\text{limit}, \text{market}, \text{cancel}\}")
    st.write(
        "You can read intensity as: how likely this kind of event is to happen next, "
        "given the current shape of the book."
    )

    st.header("4. The Queue-Reactive Idea")
    st.markdown(
        """
        The model is called **queue-reactive** because the event probabilities react to the current queue state.

        Example intuition:
        - If the sell side is thin, buy market orders can more easily push price up.
        - If the book is very imbalanced, cancellations and market orders may become more important.
        - If queues are deep, price is harder to move.
        """
    )

    st.write("The continuous-time Markov model can be written with this generator:")
    st.latex(
        r"\mathcal{L}f(q) = \sum_i \lambda_i(q)\left[f(q + \Delta_i) - f(q)\right]"
    )
    st.write(
        "That looks scary, but the idea is simple: from the current book state, "
        "each event has a rate, and each event changes the book by some amount."
    )

    st.header("5. How Calibration Works")
    st.write(
        "Calibration means learning event rates from data. If historical data says a certain event "
        "often happened when the book looked a certain way, the simulator assigns that state a higher intensity."
    )
    st.latex(r"\hat{\lambda}_i(q) = \frac{N_i(q)}{T(q)}")
    st.dataframe(
        pd.DataFrame(
            [
                [r"N_i(q)", "How many times event type i happened when the book was in state q."],
                [r"T(q)", "How much time the historical book spent in state q."],
                [r"\hat{\lambda}_i(q)", "Estimated event rate for that state."],
            ],
            columns=["Symbol", "Meaning"],
        ),
        width="stretch",
        hide_index=True,
    )

    st.header("6. Why The Price Moves")
    st.write("In this simplified simulator, price moves when the nearest queue is emptied.")
    st.latex(
        r"""
        Q_t^a = 0 \Rightarrow S_{t+} = S_t + \delta
        \qquad
        Q_t^b = 0 \Rightarrow S_{t+} = S_t - \delta
        """
    )
    st.markdown(
        """
        - If the best ask is emptied, buyers consumed the nearest sell queue, so the price moves up one tick.
        - If the best bid is emptied, sellers consumed the nearest buy queue, so the price moves down one tick.
        """
    )

    st.header("7. A Quant Workflow")
    st.dataframe(
        pd.DataFrame(
            [
                [1, "Collect data", "Get order book events for a real instrument, or generate synthetic data for development."],
                [2, "Calibrate", "Estimate event intensities from the observed event stream."],
                [3, "Simulate", "Generate many possible fake market paths from those calibrated rates."],
                [4, "Test execution", "Place a strategy into the fake market and measure fills, slippage, and PnL."],
                [5, "Validate", "Compare simulated spread, depth, and price movement against empirical data."],
            ],
            columns=["Step", "Research action", "What it means"],
        ),
        width="stretch",
        hide_index=True,
    )

    st.header("8. What To Try In The Simulator")
    st.markdown(
        """
        Try these experiments on the main simulator page:

        - Increase **market order rate** and watch liquidity get consumed faster.
        - Increase **cancel rate** and notice that queues become less stable.
        - Increase **initial depth** and see that price moves become harder.
        - Increase **mean order size** and watch individual events have more impact.
        - Change the **seed** to generate a different fake market path.
        """
    )

    st.header("9. Mini Demo")
    demo = QueueReactiveSimulator(
        SimulationConfig(seed=3, duration=180, max_events=2_000, sample_every=10)
    ).run()
    snapshots = demo.snapshots_df()

    demo_fig = go.Figure()
    demo_fig.add_trace(
        go.Scatter(
            x=snapshots["timestamp"],
            y=snapshots["midprice"],
            mode="lines",
            name="Midprice",
            line=dict(color="#1565c0", width=2),
        )
    )
    demo_fig.add_trace(
        go.Scatter(
            x=snapshots["timestamp"],
            y=snapshots["imbalance"],
            mode="lines",
            name="Imbalance",
            yaxis="y2",
            line=dict(color="#6a1b9a", width=1.5),
        )
    )
    demo_fig.update_layout(
        title="Example: Price And Imbalance From One Fake Run",
        height=380,
        margin=dict(l=10, r=10, t=45, b=10),
        xaxis_title="Simulated seconds",
        yaxis=dict(title="Midprice"),
        yaxis2=dict(title="Imbalance", overlaying="y", side="right", range=[-1, 1]),
        legend=dict(orientation="h"),
    )
    st.plotly_chart(demo_fig, width="stretch")

    st.success(
        "Big picture: this tool is a fake exchange laboratory. The next natural project step is adding a strategy "
        "that places orders into this simulated book and measures fill rate, slippage, inventory, and PnL."
    )
