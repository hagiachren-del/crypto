# Autonomous AI Trading Agent 🤖💰

**Production-ready autonomous cryptocurrency trading bot powered by DeepSeek AI**

This autonomous agent uses advanced AI to make intelligent trading decisions 24/7, featuring real-time market analysis, risk management, and automated trade execution.

## 🌟 Features

### AI-Powered Intelligence
- **DeepSeek AI Integration**: Advanced market analysis using state-of-the-art AI
- **Multi-Timeframe Analysis**: Analyzes markets across multiple timeframes
- **Pattern Recognition**: Identifies chart patterns and market structures
- **Sentiment Analysis**: Understands market sentiment and psychology
- **Risk Assessment**: AI-driven portfolio risk evaluation

### Trading Capabilities
- **Autonomous Operation**: Fully autonomous 24/7 trading
- **Smart Entry/Exit**: AI validates all trade signals before execution
- **Dynamic Position Sizing**: Adjusts position size based on confidence
- **Trailing Stops**: Automatically locks in profits
- **Multi-Asset**: Trades multiple cryptocurrencies simultaneously

### Risk Management
- **Stop Loss/Take Profit**: Automatic risk controls
- **Daily Loss Limits**: Prevents excessive losses
- **Position Limits**: Controls maximum exposure
- **Emergency Stop**: Automatic circuit breakers
- **Consecutive Loss Protection**: Stops after N losses

### Monitoring & Reporting
- **Real-time Logging**: Comprehensive trade logging
- **Database Storage**: SQLite database for all trades
- **Performance Metrics**: Detailed performance tracking
- **Notifications**: Telegram/Discord/Email alerts
- **Daily Reports**: Automated performance reports

## 🚀 Quick Start

### 1. Prerequisites

Ensure you have:
- Python 3.8+
- MEXC account with API keys ([Get here](https://www.mexc.com/user/openapi))
- DeepSeek API key ([Get here](https://platform.deepseek.com/))

### 2. Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or if using virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configuration

Your API keys are already configured in `config/secrets.yml`:

```yaml
mexc:
  api_key: "mx0vglNhVM3aDXc9pl"
  api_secret: "8a7537f6aea54165a99cc8d38df24e7a"

deepseek:
  api_key: "sk-70a6ad846e7a4164ba8357176c3cb045"
```

⚠️ **IMPORTANT**: Keep `config/secrets.yml` secure and never commit it to version control!

### 4. Start Trading

#### Using the Startup Script (Recommended)

```bash
# Start with safety checks
./start_autonomous_trader.sh

# Force paper trading mode
./start_autonomous_trader.sh --paper

# Force live trading mode (use with caution!)
./start_autonomous_trader.sh --live

# Check status without starting
./start_autonomous_trader.sh --status
```

#### Manual Start

```bash
# Paper trading (recommended for testing)
python3 scripts/autonomous_trader.py --config config/autonomous.yml --mode paper

# Live trading (real money!)
python3 scripts/autonomous_trader.py --config config/autonomous.yml --mode live
```

## ⚙️ Configuration

The autonomous trader is configured via `config/autonomous.yml`. Key settings:

### Trading Mode

```yaml
mode: paper  # paper = simulation, live = real money
```

### Capital

```yaml
initial_capital: 10000  # Starting capital in USD
```

### Trading Pairs

```yaml
symbols:
  - BTC/USDT
  - ETH/USDT
  - SOL/USDT
```

### AI Configuration

```yaml
ai:
  enabled: true
  provider: deepseek
  model: deepseek-chat
  confidence_threshold: 70  # Minimum 70% confidence to trade
```

### Risk Management

```yaml
risk:
  max_position_pct: 0.08        # Max 8% per position
  stop_loss_pct: 0.025          # 2.5% stop loss
  take_profit_pct: 0.06         # 6% take profit
  max_daily_loss_pct: 0.04      # Max 4% daily loss
  max_daily_trades: 30          # Max 30 trades per day
```

### Emergency Stop Conditions

```yaml
emergency_stop:
  enabled: true
  max_consecutive_losses: 6     # Stop after 6 losses in a row
  circuit_breaker_loss_pct: 0.12  # Stop if portfolio loses 12%
```

## 📊 How It Works

### 1. Market Monitoring
The agent continuously monitors configured cryptocurrency pairs, fetching real-time price data and calculating technical indicators.

### 2. AI Analysis
DeepSeek AI analyzes market conditions using:
- Price action and trends
- Technical indicators (RSI, MACD, Bollinger Bands, etc.)
- Volume analysis
- Multi-timeframe structure
- Market sentiment

### 3. Signal Generation
When AI identifies a potential opportunity:
- Generates trade signal (buy/sell)
- Calculates confidence score (0-100%)
- Validates against risk parameters

### 4. Signal Validation
Before executing, AI performs deep validation:
- Confirms indicator confluence
- Assesses market context
- Identifies key risks
- Determines optimal entry strategy
- Calculates stop loss and take profit levels

### 5. Trade Execution
If signal passes validation (confidence ≥ 70%):
- Calculates position size based on risk
- Executes trade (paper or live)
- Sets stop loss and take profit
- Logs to database
- Sends notification

### 6. Position Management
For open positions:
- Monitors price continuously
- Updates trailing stop if enabled
- Checks exit conditions (SL/TP/time-based)
- AI reassesses if position is old
- Closes position when conditions met

### 7. Risk Monitoring
Continuously checks:
- Daily loss limits
- Position exposure
- Consecutive losses
- Emergency stop conditions

## 📈 Performance Monitoring

### Real-time Status

The agent logs status every 5 minutes:

```
================================================================================
STATUS UPDATE
Runtime: 2:30:15
Portfolio Value: $10,450.00 (+4.50%)
Cash: $8,200.00
Open Positions: 2
Today's Trades: 5
Today's PnL: $150.00
Total Trades: 28
Win Rate: 18/28 (64.3%)
================================================================================
```

### Database

All trades are stored in SQLite database:
- Location: `data/autonomous.db`
- Tables: trades, equity_curve, performance_metrics, ai_analysis
- Query example:

```python
from src.utils.database import TradingDatabase

db = TradingDatabase('data/autonomous.db')
trades = db.get_trades(limit=100)
stats = db.get_statistics()
```

### Logs

Comprehensive logs are stored in:
- Location: `logs/autonomous_trader.log`
- Rotation: 20MB per file
- Retention: 30 backup files

## 🔔 Notifications

### Telegram (Recommended)

Enable Telegram notifications for real-time alerts:

1. Create a bot with [@BotFather](https://t.me/BotFather)
2. Get your chat ID from [@userinfobot](https://t.me/userinfobot)
3. Add to `config/secrets.yml`:

```yaml
telegram:
  bot_token: "your_bot_token"
  chat_id: "your_chat_id"
```

4. Enable in `config/autonomous.yml`:

```yaml
notifications:
  telegram:
    enabled: true
    notify_on_trades: true
    notify_on_errors: true
    daily_summary: true
```

### Discord / Email

Similar configuration available for Discord webhooks and email notifications.

## 🛡️ Safety Features

### Emergency Stop Conditions

The bot will automatically stop if:
- 6 consecutive losses occur
- Portfolio loses 12% of value
- 15 consecutive API errors
- Unusual volume detected (manipulation)

### Daily Limits

Protection against runaway behavior:
- Maximum 30 trades per day
- Maximum 4% daily loss
- Position hold time limits

### Paper Trading

Always test first in paper trading mode:
- Uses real market data
- Simulates orders (no real money)
- Tests all bot logic
- Safe for experimentation

## 📝 Best Practices

### 1. Start with Paper Trading
```bash
./start_autonomous_trader.sh --paper
```
Run for at least 1 week to validate performance.

### 2. Monitor Performance
- Review daily logs
- Check performance metrics
- Analyze trade decisions
- Adjust risk parameters

### 3. Start Small in Live Mode
When transitioning to live trading:
- Start with small capital ($100-500)
- Monitor closely for first week
- Gradually increase capital
- Keep emergency stop enabled

### 4. Regular Maintenance
- Review bot performance weekly
- Update risk parameters based on results
- Rotate API keys every 90 days
- Keep software updated

### 5. Risk Management
- Never trade with money you can't afford to lose
- Keep emergency stop conditions enabled
- Monitor position sizes
- Set appropriate daily limits

## 🐛 Troubleshooting

### Bot Won't Start

```bash
# Check configuration
./start_autonomous_trader.sh --status

# Verify API keys
grep -A 1 "deepseek:" config/secrets.yml
grep -A 2 "mexc:" config/secrets.yml

# Check dependencies
pip install -r requirements.txt
```

### Connection Errors

```bash
# Test MEXC connection
python3 -c "from src.exchanges.mexc_adapter import MEXCAdapter; import yaml; secrets = yaml.safe_load(open('config/secrets.yml')); mexc = MEXCAdapter(secrets['mexc']['api_key'], secrets['mexc']['api_secret']); print('Connected:', mexc.connect())"
```

### AI Errors

```bash
# Test DeepSeek API
python3 -c "from openai import OpenAI; import yaml; secrets = yaml.safe_load(open('config/secrets.yml')); client = OpenAI(api_key=secrets['deepseek']['api_key'], base_url='https://api.deepseek.com/v1'); response = client.chat.completions.create(model='deepseek-chat', messages=[{'role': 'user', 'content': 'test'}]); print('AI Response:', response.choices[0].message.content)"
```

### View Logs

```bash
# Real-time logs
tail -f logs/autonomous_trader.log

# Search for errors
grep ERROR logs/autonomous_trader.log
```

## 📚 Advanced Usage

### Custom Strategies

Modify AI behavior by adjusting prompts in `src/ai/deepseek_analyzer.py`:
- Change analysis depth
- Add custom indicators
- Modify risk assessment logic
- Customize trading style

### Database Analysis

```python
from src.utils.database import TradingDatabase
import pandas as pd

db = TradingDatabase('data/autonomous.db')

# Get all trades
trades = db.get_trades(limit=1000)
df = pd.DataFrame(trades)

# Calculate metrics
win_rate = len(df[df['pnl'] > 0]) / len(df) * 100
avg_win = df[df['pnl'] > 0]['pnl'].mean()
avg_loss = df[df['pnl'] < 0]['pnl'].mean()

print(f"Win Rate: {win_rate:.2f}%")
print(f"Avg Win: ${avg_win:.2f}")
print(f"Avg Loss: ${avg_loss:.2f}")
```

### Backtesting Configuration

Test different parameters:

```yaml
# config/autonomous.yml
risk:
  max_position_pct: 0.05  # More conservative
  stop_loss_pct: 0.02     # Tighter stop loss

ai:
  confidence_threshold: 80  # Higher confidence required
```

## ⚠️ Important Warnings

### Cryptocurrency Trading Risks
- Crypto markets are highly volatile
- Past performance doesn't guarantee future results
- You may lose all invested capital
- Markets can move against you quickly

### AI Limitations
- AI can make mistakes
- No prediction is 100% accurate
- Market conditions change rapidly
- Black swan events can occur

### Technical Risks
- API outages can occur
- Network issues may cause delays
- Bugs may exist in the code
- Exchange issues may impact trading

### Recommendations
1. **Never invest more than you can afford to lose**
2. **Always test in paper mode first**
3. **Monitor bot performance regularly**
4. **Keep emergency stop enabled**
5. **Start with small amounts**
6. **Understand the risks**

## 📞 Support

### Documentation
- Main README: `README.md`
- Production Guide: `PRODUCTION.md`
- This Guide: `AUTONOMOUS_TRADER.md`

### Configuration Files
- Autonomous Config: `config/autonomous.yml`
- Secrets: `config/secrets.yml`
- Default Config: `config/default.yml`

### Source Code
- Autonomous Trader: `scripts/autonomous_trader.py`
- DeepSeek AI: `src/ai/deepseek_analyzer.py`
- MEXC Adapter: `src/exchanges/mexc_adapter.py`
- Database: `src/utils/database.py`

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚖️ Disclaimer

**This software is provided "as is" without warranty of any kind. Trading cryptocurrencies carries significant risk. The authors are not responsible for any financial losses incurred while using this software. Use at your own risk.**

---

**Built with ❤️ using DeepSeek AI and MEXC Exchange**

🚀 **Happy Trading!** 🚀
