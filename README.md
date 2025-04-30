# 📈 Python Stock Trading Bot – Interactive Brokers

This is a high-performance automated stock trading bot built in Python using the **Interactive Brokers API (IB API)**. It leverages **multithreading** and **asynchronous functions** (`asyncio`) to handle real-time market data, execute trades, and manage positions with minimal latency.

---

## ⚙️ Key Features

- 🔁 **Real-Time Market Data Streaming**  
  Subscribes to live quotes using Interactive Brokers’ TWS or IB Gateway.

- ⚡ **Asynchronous Order Execution**  
  Uses `asyncio` to send and monitor trade orders concurrently with market data processing.

- 🧵 **Multithreaded Event Handling**  
  Separates data ingestion, decision-making logic, and order execution into independent threads for responsive performance.

- 📊 **Strategy Framework (Pluggable)**  
  Easily integrate your own custom strategies — including momentum, mean reversion, or technical indicator-based systems.

- 🛑 **Risk Management Tools**  
  Includes stop-loss, position sizing, and exposure tracking.

- 📄 **Logging & Audit Trail**  
  All trades, errors, and system actions are timestamped and logged for review and debugging.

---

## 🛠️ Tech Stack

- `Python 3.10+`
- `IB API` via `ib_insync`
- `asyncio`, `threading`, `queue`
- `pandas`, `numpy`, `logging`
- Optional: `matplotlib` or `plotly` for strategy visualization

---

