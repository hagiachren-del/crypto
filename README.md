# Crypto — Automated Trading Platform

An automated crypto trading platform for building, backtesting, paper-trading, and deploying algorithmic strategies across major exchanges.

> **Disclaimer:** This project is for educational and research purposes. Crypto trading is risky. You are responsible for your own decisions, compliance, taxes, and losses.

---

## ✨ Features

* **Strategy Engine**

  * Plug-in strategies (momentum, mean reversion, market making, etc.)
  * Config-driven parameters for fast iteration
* **Backtesting**

  * Historical simulation with configurable fees/slippage
  * Performance metrics: CAGR, Sharpe/Sortino, max drawdown, win rate
* **Paper Trading**

  * Real-time market data with simulated fills
* **Live Trading**

  * Exchange connectors (spot / perp depending on adapter)
  * Risk management: position sizing, max exposure, stop-loss / take-profit
* **Portfolio & Execution**

  * Multi-asset portfolio support
  * Order types: market, limit, post-only, reduce-only (adapter permitting)
* **Observability**

  * Structured logs, trade journal, optional alerts
* **Extensible Architecture**

  * Add exchanges, data sources, and strategies without touching core

---

## 🧱 Project Structure

```
crypto/
├─ README.md
├─ config/
│  ├─ default.yml
│  └─ secrets.example.yml
├─ data/
│  ├─ historical/
│  └─ cache/
├─ src/
│  ├─ core/
│  │  ├─ engine.py
│  │  ├─ portfolio.py
│  │  └─ risk.py
│  ├─ exchanges/
│  │  ├─ base.py
│  │  └─ <exchange_adapter>.py
│  ├─ strategies/
│  │  ├─ base.py
│  │  └─ <your_strategy>.py
│  ├─ backtest/
│  │  └─ runner.py
│  └─ utils/
├─ scripts/
│  ├─ backtest.py
│  ├─ paper.py
│  └─ trade.py
└─ tests/
```

> Folder names may differ slightly depending on your implementation—update this section to match.

---

## ✅ Requirements

* Python `3.10+`
* An exchange account for live trading (optional)
* API keys with **trading enabled** for live mode

---

## 🚀 Quick Start

### 1) Clone & install

```bash
git clone https://github.com/<your-username>/crypto.git
cd crypto
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2) Configure

Copy example configs:

```bash
cp config/default.yml config/local.yml
cp config/secrets.example.yml config/secrets.yml
```

Edit:

* `config/local.yml` — strategy, symbols, risk limits, environment
* `config/secrets.yml` — API keys (never commit this file)

Example `config/local.yml`:

```yml
mode: backtest  # backtest | paper | live
exchange: binance
symbols: [BTC/USDT, ETH/USDT]

strategy:
  name: sma_cross
  params:
    fast: 20
    slow: 50

risk:
  max_position_pct: 0.10
  max_daily_loss_pct: 0.03
  use_stop_loss: true
  stop_loss_pct: 0.02

fees:
  taker: 0.0006
  maker: 0.0002
slippage_bps: 5
```

---

## 🧪 Backtesting

Run a backtest:

```bash
python scripts/backtest.py --config config/local.yml --start 2022-01-01 --end 2024-01-01
```

Outputs:

* Console summary
* `reports/` performance charts (if enabled)
* `logs/trades.csv` trade-by-trade history

---

## 📝 Paper Trading

```bash
python scripts/paper.py --config config/local.yml
```

Paper mode uses live market data but **does not place real orders**. Great for proving a strategy before live deployment.

---

## 💸 Live Trading

> **Warning:** Live mode places real orders and can lose money quickly. Start small.

```bash
python scripts/trade.py --config config/local.yml
```

Recommended:

* Use subaccounts
* Start with minimal capital
* Enable conservative risk limits

---

## 🧠 Writing a Strategy

Create `src/strategies/my_strategy.py`:

```python
from strategies.base import Strategy

class MyStrategy(Strategy):
    def on_candle(self, candle):
        # candle: {open, high, low, close, volume, timestamp}
        signal = self.compute_signal(candle)

        if signal == "buy":
            self.buy()
        elif signal == "sell":
            self.sell()
```

Register it in your config:

```yml
strategy:
  name: my_strategy
  params:
    foo: 123
```

---

## 🔐 Security Notes

* **Never commit API keys**
* Use read-only keys for data/backtests
* Restrict IPs if your exchange supports it
* Keep position/risk caps on by default

---

## 📊 Metrics Glossary (short)

* **Sharpe**: risk-adjusted return vs volatility
* **Max Drawdown**: worst peak-to-trough decline
* **Win Rate**: % of profitable trades
* **Expectancy**: avg profit per trade accounting for losses

---

## 🛣️ Roadmap

* [ ] More exchange adapters
* [ ] Web dashboard
* [ ] Walk-forward optimization
* [ ] Multi-timeframe strategies
* [ ] Trade replay & visualization

---

## 🤝 Contributing

PRs welcome!

1. Fork the repo
2. Create a feature branch
3. Add tests where possible
4. Open a pull request with a clear description

---

## 📄 License

MIT License — see `LICENSE` for details.

---

## 📬 Contact

Questions or ideas? Open an issue or start a discussion in the repo.
