# 🚀 Crypto Analyzer — Professional Algorithmic Trading Platform

A comprehensive, production-ready cryptocurrency trading platform featuring advanced technical analysis, machine learning predictions, professional backtesting, paper trading, and live trading capabilities.

> **⚠️ Disclaimer:** This project is for educational and research purposes only. Cryptocurrency trading involves substantial risk of loss. You are solely responsible for your own trading decisions, compliance, taxes, and any losses incurred. Never invest more than you can afford to lose.

---

## ✨ Key Features

### 📈 **Advanced Technical Analysis**
- **50+ Technical Indicators**: SMA, EMA, RSI, MACD, Bollinger Bands, Ichimoku, ADX, Stochastic, CCI, Williams %R, ATR, Keltner Channels, Donchian Channels, SuperTrend, Vortex, and many more
- **Multiple Indicator Categories**: Trend, Momentum, Volatility, Volume indicators
- **Custom Indicator Framework**: Easy to add your own indicators

### 🤖 **Machine Learning Integration**
- **Price Prediction Models**: Random Forest, Gradient Boosting, Ensemble methods
- **Automated Feature Engineering**: 40+ features from OHLCV data
- **Direction Prediction**: Predict market direction (up/down/neutral)
- **Model Training & Evaluation**: Built-in training and evaluation metrics

### 💼 **Professional Trading Strategies**
- **Pre-built Strategies**:
  - SMA Crossover
  - EMA Crossover
  - RSI Mean Reversion
  - MACD Strategy
  - Bollinger Bands
  - Multi-Indicator (combines RSI + MACD + Bollinger Bands)
- **Easy Strategy Development**: Simple base class for creating custom strategies
- **Strategy Backtesting**: Test strategies on historical data before deploying

### 🎯 **Comprehensive Risk Management**
- **Position Sizing**: Intelligent position sizing based on risk parameters
- **Stop Loss & Take Profit**: Automatic stop loss and take profit execution
- **Trailing Stops**: Dynamic trailing stop loss
- **Daily Limits**: Maximum daily loss and trade limits
- **Risk Metrics**: Sharpe Ratio, Sortino Ratio, VaR, CVaR calculations
- **Drawdown Protection**: Maximum drawdown limits

### 📊 **Professional Backtesting Engine**
- **Realistic Simulation**: Accurate fee and slippage modeling
- **Comprehensive Metrics**:
  - Return metrics: Total Return, CAGR
  - Risk metrics: Volatility, Sharpe, Sortino, Max Drawdown
  - Trade statistics: Win Rate, Avg Win/Loss, Profit Factor, Expectancy
- **Trade-by-Trade Analysis**: Detailed trade history and analysis
- **Visual Reports**: Automated generation of performance charts

### 📉 **Advanced Analytics & Reporting**
- **Equity Curve Visualization**: Beautiful equity and drawdown charts
- **Returns Analysis**: Distribution plots, box plots, monthly heatmaps
- **Trade Analysis**: Cumulative PnL, win/loss ratios, trade size distribution
- **Export Capabilities**: CSV exports for further analysis
- **Automated Report Generation**: One-command comprehensive reports

### 🏦 **Multi-Asset Portfolio Management**
- **Multi-Symbol Support**: Trade multiple cryptocurrencies simultaneously
- **Position Tracking**: Real-time position tracking and PnL calculation
- **Cash Management**: Sophisticated cash and margin management
- **Portfolio Metrics**: Real-time portfolio value and performance tracking

### 🔗 **Exchange Integration**
- **Binance Support**: Full Binance integration (spot trading)
- **Testnet Support**: Test strategies on testnet before live trading
- **Extensible Architecture**: Easy to add more exchanges (Coinbase, Kraken, etc.)
- **REST API**: Full API support for data and trading

### 🎮 **Three Trading Modes**
1. **Backtesting**: Test strategies on historical data
2. **Paper Trading**: Simulate real-time trading without real money
3. **Live Trading**: Execute real trades with proper risk management

---

## 🧱 Project Structure

```
crypto/
├── README.md
├── LICENSE
├── requirements.txt
├── setup.py
├── .gitignore
├── config/
│   ├── default.yml           # Default configuration
│   └── secrets.example.yml   # Example secrets file
├── data/
│   ├── historical/           # Historical data cache
│   └── cache/                # General cache
├── src/
│   ├── core/
│   │   ├── engine.py         # Main trading engine
│   │   ├── portfolio.py      # Portfolio management
│   │   └── risk.py           # Risk management
│   ├── exchanges/
│   │   ├── base.py           # Base exchange interface
│   │   └── binance_adapter.py # Binance implementation
│   ├── strategies/
│   │   ├── base.py           # Base strategy class
│   │   ├── sma_cross.py      # SMA crossover strategy
│   │   ├── ema_cross.py      # EMA crossover strategy
│   │   ├── rsi_strategy.py   # RSI strategy
│   │   ├── macd_strategy.py  # MACD strategy
│   │   ├── bollinger_bands.py # Bollinger Bands strategy
│   │   └── multi_indicator.py # Multi-indicator strategy
│   ├── backtest/
│   │   └── runner.py         # Backtesting engine
│   ├── indicators/
│   │   └── indicators.py     # 50+ technical indicators
│   ├── ml/
│   │   └── predictor.py      # ML price prediction
│   └── utils/
│       ├── config.py         # Configuration management
│       └── analytics.py      # Analytics and visualization
├── scripts/
│   ├── backtest.py          # Backtesting script
│   ├── paper.py             # Paper trading script
│   └── trade.py             # Live trading script
├── tests/                   # Unit tests
├── logs/                    # Trading logs
└── reports/                 # Generated reports
```

---

## ✅ Requirements

- **Python 3.10+**
- Exchange account (for live/paper trading)
- API keys with trading permissions (for live trading)

---

## 🚀 Quick Start

### 1️⃣ Installation

```bash
# Clone repository
git clone https://github.com/yourusername/crypto.git
cd crypto

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2️⃣ Configuration

```bash
# Copy configuration files
cp config/default.yml config/local.yml
cp config/secrets.example.yml config/secrets.yml
```

Edit `config/local.yml` for your strategy and risk parameters:

```yaml
mode: backtest  # backtest | paper | live
exchange: binance
symbols:
  - BTC/USDT
  - ETH/USDT

strategy:
  name: multi_indicator  # Choose your strategy
  params:
    rsi_period: 14
    rsi_oversold: 30
    rsi_overbought: 70
    threshold: 2  # Require 2+ indicator confirmations

risk:
  max_position_pct: 0.10       # Max 10% per position
  use_stop_loss: true
  stop_loss_pct: 0.02          # 2% stop loss
  max_daily_loss_pct: 0.05     # Max 5% daily loss

fees:
  taker: 0.001
  maker: 0.0006
slippage_bps: 5

backtest:
  initial_capital: 10000
  start_date: "2023-01-01"
  end_date: "2024-01-01"
  timeframe: "1h"
```

Edit `config/secrets.yml` for API credentials:

```yaml
binance:
  api_key: "your_api_key_here"
  api_secret: "your_api_secret_here"
  testnet: true  # Use testnet for testing
```

### 3️⃣ Run Backtest

```bash
# Basic backtest
python scripts/backtest.py --config config/local.yml

# With custom parameters
python scripts/backtest.py \
  --config config/local.yml \
  --start 2023-01-01 \
  --end 2024-01-01 \
  --symbol BTC/USDT \
  --strategy multi_indicator \
  --report
```

**Example Output:**
```
============================================================
Running Backtest: MultiIndicatorStrategy
Symbol: BTC/USDT
Period: 2023-01-01 to 2024-01-01
Initial Capital: $10,000.00
============================================================

EQUITY METRICS:
  Initial Capital:      $10,000.00
  Final Equity:         $12,450.00
  Total Return:         24.50%
  CAGR:                 23.80%

RISK METRICS:
  Volatility:           18.50%
  Sharpe Ratio:         1.45
  Sortino Ratio:        2.10
  Max Drawdown:         -8.30%

TRADE STATISTICS:
  Total Trades:         45
  Win Rate:             58.00%
  Avg Win:              $120.00
  Avg Loss:             $-65.00
  Profit Factor:        1.85
  Expectancy:           $54.44
```

### 4️⃣ Paper Trading

Test with real-time data but simulated orders:

```bash
python scripts/paper.py --config config/local.yml
```

### 5️⃣ Live Trading

**⚠️ USE WITH EXTREME CAUTION ⚠️**

```bash
python scripts/trade.py --config config/local.yml
```

---

## 📚 Available Strategies

### 1. **SMA Crossover** (`sma_cross`)
Classic moving average crossover strategy.

```yaml
strategy:
  name: sma_cross
  params:
    fast: 20    # Fast SMA period
    slow: 50    # Slow SMA period
```

### 2. **EMA Crossover** (`ema_cross`)
Exponential moving average crossover for faster signals.

```yaml
strategy:
  name: ema_cross
  params:
    fast: 12
    slow: 26
```

### 3. **RSI Strategy** (`rsi_strategy`)
Mean reversion strategy based on RSI.

```yaml
strategy:
  name: rsi_strategy
  params:
    period: 14
    oversold: 30
    overbought: 70
```

### 4. **MACD Strategy** (`macd_strategy`)
Trend-following strategy using MACD.

```yaml
strategy:
  name: macd_strategy
  params:
    fast: 12
    slow: 26
    signal: 9
```

### 5. **Bollinger Bands** (`bollinger_bands`)
Mean reversion using Bollinger Bands.

```yaml
strategy:
  name: bollinger_bands
  params:
    period: 20
    std_dev: 2.0
```

### 6. **Multi-Indicator** (`multi_indicator`)
**Recommended**: Combines multiple indicators for robust signals.

```yaml
strategy:
  name: multi_indicator
  params:
    rsi_period: 14
    rsi_oversold: 30
    rsi_overbought: 70
    macd_fast: 12
    macd_slow: 26
    macd_signal: 9
    bb_period: 20
    bb_std: 2.0
    threshold: 2  # Require 2+ confirmations
```

---

## 🧠 Creating Custom Strategies

Create `src/strategies/my_strategy.py`:

```python
from src.strategies.base import Strategy
import pandas as pd

class MyStrategy(Strategy):
    """My custom trading strategy"""

    def __init__(self, params: dict):
        super().__init__(params)
        self.my_param = params.get('my_param', 10)

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate trading signals"""
        signals = pd.Series(0, index=data.index)

        # Your logic here
        # signals[condition] = 1   # Buy signal
        # signals[condition] = -1  # Sell signal

        return signals
```

Register in config:

```yaml
strategy:
  name: my_strategy
  params:
    my_param: 10
```

---

## 🤖 Machine Learning Features

### Train a Prediction Model

```python
from src.ml.predictor import PricePredictor
from src.exchanges.binance_adapter import BinanceAdapter

# Initialize
exchange = BinanceAdapter()
exchange.connect()

# Get historical data
data = exchange.get_ohlcv('BTC/USDT', '1h', limit=1000)

# Train model
predictor = PricePredictor(model_type='ensemble')
metrics = predictor.train(data, target_horizon=1)

print(f"R² Score: {metrics['ensemble_r2_score']:.4f}")

# Make predictions
prediction = predictor.predict(data)
direction = predictor.predict_direction(data)

print(f"Predicted price: ${prediction:.2f}")
print(f"Direction: {direction}")
```

---

## 📊 Analytics & Reporting

Generate comprehensive reports:

```bash
python scripts/backtest.py --config config/local.yml --report
```

This creates:
- `reports/equity_curve.png` - Equity and drawdown charts
- `reports/returns_distribution.png` - Returns histogram and box plot
- `reports/monthly_returns.png` - Monthly returns heatmap
- `reports/trade_analysis.png` - Trade analysis dashboard
- `reports/metrics.csv` - Performance metrics
- `reports/trades.csv` - All trades
- `reports/equity_curve.csv` - Equity curve data

---

## 📈 Technical Indicators Reference

### Trend Indicators
- Simple Moving Average (SMA)
- Exponential Moving Average (EMA)
- Weighted Moving Average (WMA)
- Double Exponential Moving Average (DEMA)
- Triple Exponential Moving Average (TEMA)
- MACD (Moving Average Convergence Divergence)
- ADX (Average Directional Index)
- Ichimoku Cloud
- SuperTrend
- Parabolic SAR

### Momentum Indicators
- RSI (Relative Strength Index)
- Stochastic Oscillator
- CCI (Commodity Channel Index)
- Williams %R
- ROC (Rate of Change)
- MFI (Money Flow Index)
- Awesome Oscillator

### Volatility Indicators
- Bollinger Bands
- ATR (Average True Range)
- Keltner Channels
- Donchian Channels
- Standard Deviation

### Volume Indicators
- OBV (On-Balance Volume)
- VWAP (Volume Weighted Average Price)
- AD Line (Accumulation/Distribution)
- CMF (Chaikin Money Flow)

### Advanced Indicators
- Vortex Indicator
- Elder Ray Index
- Heikin-Ashi Candles
- Pivot Points
- Fibonacci Retracements
- Z-Score
- Correlation

---

## 🔧 Advanced Configuration

### Risk Management Parameters

```yaml
risk:
  # Position sizing
  max_position_pct: 0.10          # Max 10% per position
  max_total_exposure_pct: 0.50    # Max 50% total exposure
  risk_per_trade_pct: 0.01        # Risk 1% per trade

  # Stop loss / Take profit
  use_stop_loss: true
  stop_loss_pct: 0.02             # 2% stop loss
  use_take_profit: true
  take_profit_pct: 0.05           # 5% take profit
  trailing_stop: true
  trailing_stop_pct: 0.03         # 3% trailing stop

  # Daily limits
  max_daily_loss_pct: 0.05        # Max 5% daily loss
  max_daily_trades: 50            # Max 50 trades/day

  # Other
  max_leverage: 1.0               # No leverage
  max_drawdown_pct: 0.20          # 20% max drawdown
```

---

## 🔐 Security Best Practices

1. **Never commit API keys** - Always use `secrets.yml` (in .gitignore)
2. **Use testnet first** - Test thoroughly before live trading
3. **Read-only keys for backtesting** - Only enable trading for live mode
4. **IP restrictions** - Restrict API keys to your IP if possible
5. **Start small** - Use minimal capital when starting live trading
6. **Enable 2FA** - Always enable two-factor authentication
7. **Monitor regularly** - Keep an eye on your trades
8. **Conservative risk limits** - Start with conservative risk parameters

---

## 🧪 Testing

Run tests:

```bash
pytest tests/
```

---

## 📊 Performance Metrics Explained

- **CAGR**: Compound Annual Growth Rate - annualized return
- **Sharpe Ratio**: Risk-adjusted return (higher is better, >1 is good)
- **Sortino Ratio**: Like Sharpe but only considers downside volatility
- **Max Drawdown**: Largest peak-to-trough decline
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Gross profit / Gross loss (>1.5 is good)
- **Expectancy**: Average profit per trade
- **Volatility**: Standard deviation of returns (annualized)

---

## 🛣️ Roadmap

- [x] Core trading engine
- [x] 50+ technical indicators
- [x] Multiple trading strategies
- [x] Professional backtesting
- [x] Paper trading mode
- [x] Live trading mode
- [x] Risk management system
- [x] ML price prediction
- [x] Advanced analytics
- [ ] More exchange adapters (Coinbase, Kraken, FTX)
- [ ] Web dashboard
- [ ] Walk-forward optimization
- [ ] Multi-timeframe strategies
- [ ] Sentiment analysis integration
- [ ] On-chain metrics
- [ ] Telegram/Discord notifications
- [ ] Advanced order types (OCO, trailing)

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests if applicable
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

**DISCLAIMER**: This software is provided for educational purposes only. Trading cryptocurrencies involves substantial risk of loss and is not suitable for every investor. The developers are not responsible for any financial losses incurred.

---

## 📬 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/crypto/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/crypto/discussions)
- **Documentation**: See this README and code comments

---

## 🙏 Acknowledgments

Built with:
- [CCXT](https://github.com/ccxt/ccxt) - Cryptocurrency exchange integration
- [pandas](https://pandas.pydata.org/) - Data analysis
- [NumPy](https://numpy.org/) - Numerical computing
- [scikit-learn](https://scikit-learn.org/) - Machine learning
- [Matplotlib](https://matplotlib.org/) - Visualization

---

## ⚡ Quick Examples

### Example 1: Simple Backtest

```bash
python scripts/backtest.py \
  --start 2023-01-01 \
  --end 2024-01-01 \
  --symbol BTC/USDT \
  --strategy sma_cross \
  --report
```

### Example 2: Multi-Symbol Paper Trading

```bash
python scripts/paper.py \
  --config config/local.yml \
  --symbols BTC/USDT ETH/USDT BNB/USDT
```

### Example 3: Live Trading with Confirmation

```bash
python scripts/trade.py --config config/local.yml
# Will prompt for confirmation before starting
```

---

**Happy Trading! 🚀📈💰**

*Remember: Past performance does not guarantee future results. Always do your own research and never invest more than you can afford to lose.*
