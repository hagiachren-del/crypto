# 🏭 Production Deployment Guide

Complete guide for deploying the crypto trading platform in production with MEXC exchange and Claude AI integration.

---

## 🎯 Production Features

### Exchange Integration
- ✅ **MEXC Global** - Primary exchange with full API support
- ✅ **Binance** - Alternative exchange (optional)
- ✅ **Extensible architecture** - Easy to add more exchanges

### AI-Powered Analysis
- ✅ **Claude AI (Anthropic)** - Advanced market analysis
  - Real-time market sentiment analysis
  - Trade signal validation
  - Risk assessment
  - Automated daily reports
  - Pattern recognition
- ✅ **Confidence-based trading** - Only execute high-confidence AI signals

### Production Infrastructure
- ✅ **Professional logging** - Multi-level logging with rotation
- ✅ **Database persistence** - SQLite for trade history
- ✅ **Real-time notifications** - Telegram, Email, Discord
- ✅ **Health monitoring** - System health checks
- ✅ **Error handling** - Automatic retry with exponential backoff
- ✅ **Emergency stop** - Circuit breakers for safety

---

## 📋 Prerequisites

### 1. Exchange Account (MEXC)
1. Create account at [MEXC.com](https://www.mexc.com/)
2. Complete KYC verification
3. Enable 2FA security
4. Generate API keys:
   - Go to: Account → API Management
   - Create new API key
   - **Enable**: Read + Trade permissions
   - **Disable**: Withdrawal permissions (security)
   - Whitelist your IP (recommended)

### 2. Claude AI API Key
1. Sign up at [Anthropic Console](https://console.anthropic.com/)
2. Add credits to your account
3. Generate API key
4. Store securely

### 3. Telegram Bot (Optional)
1. Message [@BotFather](https://t.me/botfather)
2. Create new bot with `/newbot`
3. Save the bot token
4. Get your chat ID from [@userinfobot](https://t.me/userinfobot)

---

## 🚀 Quick Start

### 1. Installation

```bash
# Clone repository
git clone https://github.com/yourusername/crypto.git
cd crypto

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install production dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy configuration files
cp config/production.yml config/local.yml
cp config/secrets.example.yml config/secrets.yml

# Edit secrets.yml with your credentials
nano config/secrets.yml
```

Add your credentials to `config/secrets.yml`:

```yaml
# MEXC Exchange
mexc:
  api_key: "your_mexc_api_key_here"
  api_secret: "your_mexc_api_secret_here"

# Claude AI
claude:
  api_key: "sk-ant-api03-xxxxx"

# Telegram (optional)
telegram:
  bot_token: "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
  chat_id: "123456789"
```

### 3. Test Configuration

```bash
# Test exchange connection
python -c "
from src.exchanges.mexc_adapter import MEXCAdapter
exchange = MEXCAdapter('YOUR_KEY', 'YOUR_SECRET')
print('✅ Connection successful!' if exchange.connect() else '❌ Connection failed')
"

# Test Claude AI
python -c "
from src.ai.claude_analyzer import ClaudeMarketAnalyzer
ai = ClaudeMarketAnalyzer('YOUR_ANTHROPIC_KEY')
print('✅ Claude AI ready!')
"
```

### 4. Start Trading

```bash
# Start in paper trading mode (recommended first)
python scripts/trade_production.py --config config/local.yml

# Or explicitly set mode
python scripts/trade_production.py --config config/local.yml --mode paper

# When ready for live trading (BE CAREFUL!)
python scripts/trade_production.py --config config/local.yml --mode live
```

---

## ⚙️ Configuration Guide

### Trading Parameters

Edit `config/local.yml`:

```yaml
# Exchange
exchange: mexc

# Symbols to trade
symbols:
  - BTC/USDT
  - ETH/USDT
  - SOL/USDT

# Strategy
strategy:
  name: multi_indicator  # Recommended for AI validation
  params:
    threshold: 2  # Require 2+ indicator confirmations

# AI Configuration
ai:
  enabled: true
  confidence_threshold: 60  # Only trade on 60%+ confidence

# Risk Management (START CONSERVATIVE!)
risk:
  max_position_pct: 0.05      # 5% max per position
  stop_loss_pct: 0.02         # 2% stop loss
  max_daily_loss_pct: 0.03    # 3% max daily loss
  max_daily_trades: 20        # Limit trades per day
```

### Notification Settings

```yaml
notifications:
  telegram:
    enabled: true
    notify_on_trades: true
    notify_on_errors: true
    daily_report: true
    daily_report_time: "20:00"  # 8 PM daily report
```

---

## 🤖 AI-Powered Trading Features

### 1. Market Sentiment Analysis

Claude AI analyzes market data and provides:
- Overall sentiment (bullish/bearish/neutral)
- Confidence level (0-100%)
- Key market insights
- Risk factors to consider

### 2. Trade Signal Validation

Before executing any trade:
1. Strategy generates signal
2. AI validates signal and provides confidence score
3. Only executes if confidence > threshold (default: 60%)
4. AI suggests entry strategy and stop loss levels

### 3. Portfolio Risk Assessment

Regular AI-powered risk analysis:
- Overall risk level evaluation
- Specific concerns and warnings
- Recommended actions
- Position sizing suggestions

### 4. Daily Market Reports

Automated daily reports via Telegram/Email:
- Market summary
- Trading performance
- AI outlook for next day
- Recommendations

---

## 📊 Monitoring & Logs

### Log Files

Logs are stored in `logs/` directory:

```
logs/
├── crypto_trader_prod.log          # Main log (rotated at 10MB)
├── crypto_trader_prod_errors.log   # Errors only
├── crypto_trader_prod_structured.json  # JSON logs for analysis
├── trades.jsonl                    # Trade history
├── signals.jsonl                   # Trading signals
└── trading_errors.jsonl            # Trading errors
```

### Database

Trade data persisted in SQLite:
- `data/production.db` - All trades, equity curve, performance metrics

Query your data:

```bash
sqlite3 data/production.db
```

```sql
-- View recent trades
SELECT * FROM trades ORDER BY timestamp DESC LIMIT 10;

-- Performance metrics
SELECT * FROM performance_metrics ORDER BY date DESC;

-- AI analysis history
SELECT * FROM ai_analysis ORDER BY timestamp DESC LIMIT 5;
```

---

## 🔒 Security Best Practices

### 1. API Key Security

✅ **DO:**
- Use separate API keys for trading (never withdrawal)
- Enable IP whitelisting on exchange
- Rotate keys every 90 days
- Store keys in `secrets.yml` (not in code)
- Use environment variables in production

❌ **DON'T:**
- Commit `secrets.yml` to git
- Share API keys
- Enable withdrawal permissions
- Use same keys across services

### 2. Risk Management

Start with these conservative settings:

```yaml
risk:
  max_position_pct: 0.03        # Only 3% per trade
  max_total_exposure_pct: 0.20  # Max 20% in positions
  use_stop_loss: true
  stop_loss_pct: 0.02           # 2% stop loss
  max_daily_loss_pct: 0.03      # Stop if lose 3% in a day
```

### 3. Testing Progression

**NEVER skip these steps:**

1. **Backtesting** (1-2 weeks)
   - Test strategy on historical data
   - Analyze performance metrics
   - Optimize parameters

2. **Paper Trading** (2-4 weeks minimum)
   - Real market data, simulated orders
   - Verify AI integration works
   - Monitor for at least 2 weeks
   - Ensure positive results

3. **Live Trading** (start tiny!)
   - Start with $100-500 maximum
   - Use tightest risk limits
   - Monitor constantly for first week
   - Gradually increase if profitable

---

## 📈 Performance Optimization

### 1. Strategy Selection

For AI-enhanced trading:
```yaml
strategy:
  name: multi_indicator  # Best with AI validation
  params:
    threshold: 2  # Require multiple confirmations
```

### 2. AI Settings

Balance cost vs. accuracy:
```yaml
ai:
  confidence_threshold: 70  # Higher = fewer but better trades
  features:
    market_analysis: true
    signal_validation: true    # Essential
    risk_assessment: true
    daily_reports: false       # Optional, costs API calls
```

### 3. Update Frequency

```yaml
paper:
  update_interval: 60   # 1 minute (real-time-ish)

live:
  update_interval: 30   # 30 seconds (more responsive)
```

---

## 🚨 Emergency Procedures

### Stop Trading Immediately

```bash
# Send SIGTERM to graceful shutdown
kill -TERM <PID>

# Or Ctrl+C in terminal
```

Bot will:
1. Stop accepting new signals
2. Close all open positions
3. Save state to database
4. Send shutdown notification

### Emergency Circuit Breakers

Auto-stop triggers (configured in `production.yml`):

```yaml
emergency_stop:
  max_consecutive_losses: 5         # Stop after 5 losses in a row
  circuit_breaker_loss_pct: 0.10    # Stop if lose 10% of portfolio
  api_error_threshold: 10           # Stop after 10 API errors
```

### Manual Position Close

```python
# Emergency position close script
from src.exchanges.mexc_adapter import MEXCAdapter

exchange = MEXCAdapter(api_key, api_secret)
exchange.connect()

# Get all open orders
orders = exchange.get_open_orders()

# Cancel all
for order in orders:
    exchange.cancel_order(order['id'], order['symbol'])
```

---

## 📞 Support & Troubleshooting

### Common Issues

**1. "Failed to connect to MEXC"**
- Check API key/secret are correct
- Verify IP is whitelisted
- Check exchange status page

**2. "Claude AI authentication failed"**
- Verify Anthropic API key
- Check account has credits
- Ensure key is set in secrets.yml or environment

**3. "Telegram notifications not working"**
- Verify bot token is correct
- Check chat_id is correct
- Message bot first to start conversation

**4. "Database locked error"**
- Only run one bot instance
- Check no other process using DB
- Restart if needed

### Getting Help

1. Check logs in `logs/` directory
2. Review `logs/crypto_trader_prod_errors.log`
3. Check database for trade history
4. Open GitHub issue with logs

---

## 📚 Additional Resources

### MEXC Documentation
- [MEXC API Docs](https://mexcdevelop.github.io/apidocs/spot_v3_en/)
- [Trading Fees](https://www.mexc.com/fee)
- [API Management](https://www.mexc.com/user/openapi)

### Claude AI Documentation
- [Anthropic API Docs](https://docs.anthropic.com/)
- [API Keys](https://console.anthropic.com/settings/keys)
- [Pricing](https://www.anthropic.com/api)

### Trading Resources
- [Technical Indicators Guide](https://www.investopedia.com/technical-analysis-4689657)
- [Risk Management Basics](https://www.investopedia.com/articles/trading/09/risk-management.asp)
- [Crypto Trading Strategies](https://academy.binance.com/en/articles/a-complete-guide-to-cryptocurrency-trading-for-beginners)

---

## ⚖️ Legal Disclaimer

**IMPORTANT:**

- This software is for educational purposes
- Cryptocurrency trading carries significant risk
- You can lose all your capital
- Authors are not responsible for financial losses
- Not financial advice
- Use at your own risk
- Consult financial advisor before trading
- Comply with local regulations
- Past performance ≠ future results

**By using this software, you agree:**
- You understand crypto trading risks
- You accept full responsibility for losses
- You will comply with all applicable laws
- You will use appropriate risk management
- You will start with funds you can afford to lose

---

## 🎯 Production Checklist

Before going live, ensure:

- [ ] Tested strategy in backtest (positive results)
- [ ] Paper traded for minimum 2 weeks (profitable)
- [ ] MEXC API keys configured correctly
- [ ] Claude AI working (tested market analysis)
- [ ] Telegram notifications working
- [ ] Database saving trades correctly
- [ ] Risk limits are conservative
- [ ] Emergency stop conditions configured
- [ ] Using small capital ($100-500 max)
- [ ] Monitoring setup (can check logs anytime)
- [ ] Backup plan ready
- [ ] Understand how to emergency stop
- [ ] Read and accept all risks

**DO NOT skip these steps. Your money depends on it.**

---

## 🏆 Success Tips

1. **Start Small** - $100-500 maximum initially
2. **Be Patient** - Don't increase capital quickly
3. **Monitor Daily** - Check logs and performance
4. **Trust the AI** - It's trained on vast data
5. **Respect Risk Limits** - They protect you
6. **Keep Learning** - Study your trades
7. **Stay Humble** - Markets are unpredictable
8. **Take Breaks** - Don't trade emotionally
9. **Diversify** - Don't rely on one bot
10. **Have Fun** - But trade responsibly!

---

**Ready to trade? Start with paper mode and good luck! 🚀**
