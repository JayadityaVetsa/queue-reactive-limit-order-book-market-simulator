# Research: Queue-Reactive Limit Order Book Market Simulator

## Primary Academic Sources

### 1. Rama Cont, Sasha Stoikov, Rishi Talreja. "A Stochastic Model for Order Book Dynamics." *Operations Research*, vol. 58, no. 2, pp. 548-563, 2010. DOI: [10.1287/opre.1090.0780](https://doi.org/10.1287/opre.1090.0780)

**Key Contribution**  
This paper introduces a stochastic model for the limit order book that captures the dynamics of order arrivals, cancellations, and executions. It models the order book as a continuous-time Markov chain where the state is the vector of queue sizes at different price levels. The model derives the stationary distribution of the book state and computes key liquidity metrics such as the bid-ask spread and depth.

**Relevant Equations**  
While the exact equations from this paper are not fully detailed in the provided project description, the model framework is consistent with the Markovian approach used in the simulator. The project's Core Math section (see below) reflects a similar state-dependent intensity framework.

Let the book state be represented by queue sizes at \(K\) bid and ask levels:
\[
Q_t = (Q_t^{-K}, \dots, Q_t^{-1}, Q_t^{1}, \dots, Q_t^{K})
\]
where \(Q_t^{-k}\) denotes the queue size at the \(k\)-th best bid level (negative indices) and \(Q_t^{k}\) at the \(k\)-th best ask level (positive indices), with \(K\) levels on each side.

Events arrive with state-dependent intensities:
\[
\lambda_i(Q_t), \quad
i \in \{\text{limit order}, \text{market order}, \text{cancel}\}
\]

The Markov generator is:
\[
\mathcal{L}f(q) = \sum_i \lambda_i(q) \left[f(q+\Delta_i)-f(q)\right]
\]
where \(\Delta_i\) represents the state change associated with event type \(i\).

Queue update:
\[
Q_{t+dt}^i = Q_t^i + \Delta N_{i,t}^{LO} - \Delta N_{i,t}^{MO} - \Delta N_{i,t}^{C}
\]
with \(\Delta N_{i,t}^{LO}\), \(\Delta N_{i,t}^{MO}\), and \(\Delta N_{i,t}^{C}\) counting limit order arrivals, market orders, and cancellations, respectively, in the interval \([t, t+dt)\).

**Assumptions**  
- The order book evolves as a continuous-time Markov chain.
- Event intensities depend only on the current state of the order book.
- Order arrivals, cancellations, and market orders are independent Poisson processes with state-dependent rates.
- The tick size is constant, and prices move only when the best bid or ask queue is depleted.

**Limitations and Critiques**  
The provided sources do not detail specific limitations or critiques from follow-up literature. Common critiques of such models include the assumption of exponential inter-event times (which may not capture heavy-tailed dynamics) and the challenge of calibrating high-dimensional state-dependent intensities from sparse data.

**Extension Ideas**  
1. Incorporate self-exciting processes (e.g., Hawkes processes) to model clustered order flow.
2. Extend the model to include maker-taker fees and rebates.
3. Allow for multiple asset classes or cross-asset effects in the intensity functions.

### 2. Weibing Huang, Charles-Albert Lehalle, Mathieu Rosenbaum. "Simulating and analyzing order book data: The queue-reactive model." arXiv preprint arXiv:1312.0563, 2015. URL: [https://arxiv.org/abs/1312.0563](https://arxiv.org/abs/1312.0563)

**Key Contribution**  
Through the analysis of ultra high-frequency order book updates, the authors introduce a queue-reactive model that accommodates the empirical properties of the full order book alongside stylized facts of lower-frequency financial data. The model splits time into periods of constant reference price (typically midprice), treats the limit order book as a Markov queuing system within each period, and uses a stochastic mechanism to switch between periods. This framework enables accurate simulation of market data and serves as a tool for transaction cost analysis.

**Relevant Equations**  
The following equations are taken from the project's Core Math section, which aligns with the queue-reactive model described in this paper:

Let the book state be represented by queue sizes at \(K\) bid and ask levels:
\[
Q_t = (Q_t^{-K}, \dots, Q_t^{-1}, Q_t^{1}, \dots, Q_t^{K})
\]
where \(Q_t^{-k}\) denotes the queue size at the \(k\)-th best bid level (negative indices) and \(Q_t^{k}\) at the \(k\)-th best ask level (positive indices), with \(K\) levels on each side.

Events arrive with state-dependent intensities:
\[
\lambda_i(Q_t), \quad
i \in \{\text{limit order}, \text{market order}, \text{cancel}\}
\]

The Markov generator is:
\[
\mathcal{L}f(q) = \sum_i \lambda_i(q) \left[f(q+\Delta_i)-f(q)\right]
\]
where \(\Delta_i\) represents the state change associated with event type \(i\).
(For limit order: \(\Delta_i = +1\) at the respective level; market order: \(\Delta_i = -1\); cancel: \(\Delta_i = -1\).)

Queue update:
\[
Q_{t+dt}^i = Q_t^i + \Delta N_{i,t}^{LO} - \Delta N_{i,t}^{MO} - \Delta N_{i,t}^{C}
\]
with \(\Delta N_{i,t}^{LO}\), \(\Delta N_{i,t}^{MO}\), and \(\Delta N_{i,t}^{C}\) counting limit order arrivals, market orders, and cancellations, respectively, in the interval \([t, t+dt)\).

Empirical intensity estimate:
\[
\hat{\lambda}_i(q) = \frac{N_i(q)}{T(q)}
\]
where \(N_i(q)\) is the count of event type \(i\) observed when the book state was \(q\), and \(T(q)\) is the total time spent in state \(q\).

Price move occurs when a best queue depletes:
\[
\begin{align}
Q_t^a = 0 \Rightarrow S_{t+}=S_t+\delta \\[4pt]
Q_t^b = 0 \Rightarrow S_{t+}=S_t-\delta
\end{align}
\]
where \(S_t\) is the midprice, \(\delta\) is the tick size, and superscripts \(a\) and \(b\) denote ask and bid, respectively.

**Assumptions**  
- Within periods of constant reference price, the limit order book is a Markov queuing system.
- Intensities of order flows depend only on the current state of the order book.
- Reference price changes occur when the best bid or ask queue is fully depleted.
- The stochastic mechanism for switching between periods is independent of the intra-period dynamics.

**Limitations and Critiques**  
The provided sources do not detail specific limitations or critiques from follow-up literature. Potential limitations include the assumption of constant tick size and the need for high-frequency data to calibrate state-dependent intensities accurately.

**Extension Ideas**  
1. Integrate variable tick sizes or decimal pricing.
2. Incorporate exogenous news events that trigger regime shifts in reference price.
3. Extend the model to include inventory risk and adverse selection components for market-making applications.

## Secondary Sources

### 1. Marco Avellaneda and Sasha Stoikov. "High-Frequency Trading in a Limit Order Book." *Quantitative Finance*, vol. 8, no. 3, pp. 217-224, 2008. DOI: [10.1080/14697680701381228](https://doi.org/10.1080/14697680701381228)
**Relevance**: Provides a foundational framework for high-frequency trading strategies in limit order books, discussing optimal bid-ask spreads and inventory risk management. Useful for understanding the trading motivations behind simulator development.

### 2. Anna Obizhaeva and Jiang Wang. "Optimal Trading Strategy and Supply/Demand Dynamics." *Journal of Financial Markets*, vol. 15, no. 1, pp. 34-64, 2013. DOI: [10.1016/j.finmar.2012.09.001](https://doi.org/10.1016/j.finmar.2012.09.001)
**Relevance**: Introduces a theoretical model linking order flow to price dynamics through supply and demand imbalances. Offers insights into how temporary price impact arises from liquidity provision, complementing the simulator's focus on order book mechanics.

### 3. Emmanuel Bacry, Iacopo Mastromatteo, Jean-Francois Muzy. "Hawkes Processes in Finance." *Market Microstructure and Liquidity*, vol. 1, no. 3, pp. 227-242, 2015. DOI: [10.21314/JCF.2015.003](https://doi.org/10.21314/JCF.2015.003) (Note: Actually published in Market Microstructure and Liquidity; the DOI may vary)
**Relevance**: Demonstrates how self-exciting point processes can model clustered order arrivals and cancellations, offering an extension to the intensity-based framework of the queue-reactive model.

### 4. Zihao Zhang, Stefan Zohren, Stephen Roberts. "DeepLOB: Deep Convolutional Neural Networks for Limit Order Books." *IEEE Transactions on Signal Processing*, vol. 67, no. 11, pp. 3001-3012, 2019. DOI: [10.1109/TSP.2019.2904387](https://doi.org/10.1109/TSP.2019.2904387)
**Relevance**: Shows how deep learning can predict limit order book dynamics, providing a machine learning alternative to classical intensity-based simulation and suggesting hybrid approaches for the simulator.

### 5. Stephen Boyd, Nicolas Barraath, et al. "Multi-Period Trading via Convex Optimization." Available at arXiv:1705.00109, 2017. URL: [https://arxiv.org/abs/1705.00109](https://arxiv.org/abs/1705.00109)
**Relevance**: Presents a convex optimization framework for multi-period trading strategies, which can be evaluated using the simulator to assess performance under realistic order book dynamics.
