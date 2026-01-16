#!/usr/bin/env python3
"""
Interactive Paper Trading Demo with Claude AI Simulation

This demo shows how the platform works with AI-powered trading
without requiring real API keys. Perfect for learning!
"""

import sys
import os
import time
import random
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.strategies.multi_indicator import MultiIndicatorStrategy
from src.core.portfolio import Portfolio
from src.core.risk import RiskManager
from src.indicators.indicators import Indicators


class AIAnalysisSimulator:
    """Simulates Claude AI analysis for demo purposes"""

    def __init__(self):
        self.sentiments = ['bullish', 'bearish', 'neutral']

    def analyze_market(self, symbol: str, data: pd.DataFrame, indicators: dict) -> dict:
        """Simulate AI market analysis"""
        current_price = data['close'].iloc[-1]
        prev_price = data['close'].iloc[-24] if len(data) >= 24 else data['close'].iloc[0]
        price_change = ((current_price - prev_price) / prev_price) * 100

        # Determine sentiment based on indicators
        rsi = indicators.get('rsi', 50)
        macd_signal = indicators.get('macd_signal', 'neutral')

        if rsi < 35 and price_change < -2:
            sentiment = 'bullish'
            confidence = random.randint(65, 85)
            reasoning = "Oversold conditions with strong reversal potential"
        elif rsi > 65 and price_change > 2:
            sentiment = 'bearish'
            confidence = random.randint(60, 80)
            reasoning = "Overbought conditions, potential correction ahead"
        else:
            sentiment = 'neutral'
            confidence = random.randint(40, 60)
            reasoning = "Mixed signals, market consolidating"

        return {
            'sentiment': sentiment,
            'confidence': confidence,
            'reasoning': reasoning,
            'key_points': [
                f"Current price: ${current_price:.2f}",
                f"24h change: {price_change:+.2f}%",
                f"RSI: {rsi:.1f}",
                f"Trend: {macd_signal}"
            ],
            'risks': [
                "Market volatility remains elevated",
                "External market factors could impact price"
            ]
        }

    def validate_signal(self, symbol: str, signal: str, analysis: dict) -> dict:
        """Simulate AI signal validation"""
        base_confidence = analysis['confidence']

        # Adjust confidence based on signal alignment
        if (signal == 'buy' and analysis['sentiment'] == 'bullish') or \
           (signal == 'sell' and analysis['sentiment'] == 'bearish'):
            validation_confidence = min(base_confidence + 10, 95)
            approved = validation_confidence >= 60
        else:
            validation_confidence = max(base_confidence - 15, 30)
            approved = False

        return {
            'approved': approved,
            'confidence': validation_confidence,
            'recommendation': 'Execute trade' if approved else 'Skip trade - low confidence',
            'entry_strategy': 'Market order with immediate execution' if approved else 'Wait for better setup',
            'stop_loss_suggestion': '2% below entry' if signal == 'buy' else '2% above entry'
        }


def generate_realistic_market_data(start_date, days=7, initial_price=43000):
    """Generate realistic-looking crypto market data"""
    print(f"📊 Generating {days} days of realistic market data...")

    hours = days * 24
    timestamps = pd.date_range(start=start_date, periods=hours, freq='h')

    # Create realistic price movement with trends
    trends = []
    segment_length = hours // 4

    # Uptrend
    trends.append(np.linspace(0, 0.08, segment_length))
    # Consolidation
    trends.append(np.linspace(0.08, 0.10, segment_length) + np.random.normal(0, 0.01, segment_length))
    # Correction
    trends.append(np.linspace(0.10, 0.03, segment_length))
    # Recovery
    remaining = hours - (3 * segment_length)
    trends.append(np.linspace(0.03, 0.12, remaining))

    trend = np.concatenate(trends)

    # Add realistic noise
    noise = np.random.normal(0, 0.008, hours)
    returns = np.diff(trend, prepend=0) + noise

    # Generate prices
    price = initial_price * np.exp(np.cumsum(returns))

    # Create OHLCV data
    data = pd.DataFrame(index=timestamps)
    data['close'] = price
    data['open'] = data['close'].shift(1).fillna(initial_price)

    # Realistic high/low
    volatility = 0.015
    data['high'] = data[['open', 'close']].max(axis=1) * (1 + np.random.uniform(0, volatility, hours))
    data['low'] = data[['open', 'close']].min(axis=1) * (1 - np.random.uniform(0, volatility, hours))
    data['volume'] = np.random.uniform(800, 1500, hours)

    print(f"✅ Market data ready: {len(data)} candles")
    print(f"   Starting price: ${data['close'].iloc[0]:.2f}")
    print(f"   Current price: ${data['close'].iloc[-1]:.2f}")
    print(f"   Total change: {((data['close'].iloc[-1] / data['close'].iloc[0] - 1) * 100):+.2f}%\n")

    return data


def print_header(text):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")


def print_ai_analysis(analysis):
    """Print AI analysis in a nice format"""
    print("🤖 CLAUDE AI MARKET ANALYSIS")
    print("-" * 70)
    print(f"Sentiment:  {analysis['sentiment'].upper()} (Confidence: {analysis['confidence']}%)")
    print(f"Analysis:   {analysis['reasoning']}\n")

    print("Key Points:")
    for point in analysis['key_points']:
        print(f"  • {point}")

    print("\nRisk Factors:")
    for risk in analysis['risks']:
        print(f"  ⚠️  {risk}")
    print("-" * 70)


def print_trade_validation(symbol, signal, validation):
    """Print trade validation result"""
    print("\n🔍 AI SIGNAL VALIDATION")
    print("-" * 70)
    print(f"Symbol:        {symbol}")
    print(f"Signal:        {signal.upper()}")
    print(f"AI Confidence: {validation['confidence']}%")

    if validation['approved']:
        print(f"Decision:      ✅ APPROVED - {validation['recommendation']}")
        print(f"Entry:         {validation['entry_strategy']}")
        print(f"Stop Loss:     {validation['stop_loss_suggestion']}")
    else:
        print(f"Decision:      ❌ REJECTED - {validation['recommendation']}")
    print("-" * 70)


def run_paper_trading_demo():
    """Run interactive paper trading demo"""
    print_header("🚀 PAPER TRADING DEMO WITH CLAUDE AI")

    print("Welcome to the AI-Powered Crypto Trading Platform!")
    print("This demo shows how Claude AI analyzes markets and validates trades.\n")

    print("Demo features:")
    print("  ✓ Realistic market data simulation")
    print("  ✓ AI market analysis with confidence scoring")
    print("  ✓ Trade signal validation")
    print("  ✓ Risk-managed portfolio")
    print("  ✓ Performance tracking\n")

    # Auto-start in automated environments
    print("Starting demo...\n")

    # Initialize components
    print_header("INITIALIZING TRADING SYSTEM")

    print("📦 Loading components...")
    strategy = MultiIndicatorStrategy({
        'rsi_period': 14,
        'rsi_oversold': 30,
        'rsi_overbought': 70,
        'macd_fast': 12,
        'macd_slow': 26,
        'macd_signal': 9,
        'bb_period': 20,
        'bb_std': 2.0,
        'threshold': 2
    })
    print("   ✅ Multi-Indicator Strategy loaded")

    portfolio = Portfolio(10000)
    print(f"   ✅ Portfolio initialized: ${portfolio.initial_capital:,.2f}")

    risk_manager = RiskManager({
        'max_position_pct': 0.10,
        'use_stop_loss': True,
        'stop_loss_pct': 0.02,
        'max_daily_loss_pct': 0.05,
        'max_daily_trades': 20
    })
    print("   ✅ Risk management configured")

    ai_analyzer = AIAnalysisSimulator()
    print("   ✅ Claude AI simulator ready")

    indicators_calc = Indicators()
    print("   ✅ Technical indicators ready\n")

    # Generate market data
    symbol = "BTC/USDT"
    start_date = datetime.now() - timedelta(days=7)
    market_data = generate_realistic_market_data(start_date, days=7, initial_price=43000)

    # Run simulation
    print_header("STARTING PAPER TRADING SIMULATION")

    print(f"Symbol: {symbol}")
    print(f"Strategy: Multi-Indicator (RSI + MACD + Bollinger Bands)")
    print(f"AI: Claude AI validation with 60% confidence threshold")
    print(f"Period: 7 days ({len(market_data)} hours)\n")

    print("Beginning trading simulation...\n")
    time.sleep(1)

    position_open = False
    trades_executed = 0
    trades_rejected = 0

    # Simulate trading hour by hour
    for i in range(50, len(market_data), 12):  # Sample every 12 hours
        current_data = market_data.iloc[:i+1]
        current_price = current_data['close'].iloc[-1]
        timestamp = current_data.index[-1]

        # Calculate indicators
        close = current_data['close']
        high = current_data['high']
        low = current_data['low']

        rsi = indicators_calc.rsi(close, 14).iloc[-1]
        macd_line, signal_line, _ = indicators_calc.macd(close)
        macd_signal_val = "bullish" if macd_line.iloc[-1] > signal_line.iloc[-1] else "bearish"

        indicators_dict = {
            'rsi': rsi,
            'macd_signal': macd_signal_val
        }

        print(f"\n\n{'='*70}")
        print(f"📅 {timestamp.strftime('%Y-%m-%d %H:%M')} | Price: ${current_price:.2f}")
        print(f"{'='*70}")

        # Check for exit
        if position_open:
            should_exit, reason = risk_manager.should_close_position(
                symbol, current_price, 'long', entry_price
            )

            if should_exit:
                fees = current_price * portfolio.get_position(symbol).quantity * 0.001
                pnl = portfolio.close_position(symbol, current_price, timestamp, fees)

                print(f"\n🔴 POSITION CLOSED")
                print(f"   Reason: {reason}")
                print(f"   Exit Price: ${current_price:.2f}")
                print(f"   PnL: ${pnl:.2f} ({(pnl / (entry_price * portfolio.get_position(symbol).quantity) * 100 if pnl else 0):.2f}%)")

                risk_manager.record_trade(pnl)
                position_open = False
                time.sleep(2)
                continue

        # Generate signal
        if not position_open:
            signal = strategy.on_data(current_data)

            if signal in ['buy', 'sell']:
                # AI Analysis
                print("\n🔍 Signal detected! Requesting AI analysis...")
                time.sleep(1)

                ai_analysis = ai_analyzer.analyze_market(symbol, current_data, indicators_dict)
                print_ai_analysis(ai_analysis)
                time.sleep(1)

                # AI Validation
                validation = ai_analyzer.validate_signal(symbol, signal, ai_analysis)
                print_trade_validation(symbol, signal, validation)
                time.sleep(1)

                if validation['approved']:
                    # Execute trade
                    portfolio_value = portfolio.get_total_value({symbol: current_price})
                    quantity = risk_manager.calculate_position_size(portfolio_value, current_price)
                    entry_price = current_price
                    fees = entry_price * quantity * 0.001

                    success = portfolio.open_position(symbol, 'long', quantity, entry_price, timestamp, fees)

                    if success:
                        risk_manager.set_stop_loss(symbol, entry_price, 'long')
                        position_open = True
                        trades_executed += 1

                        print(f"\n✅ TRADE EXECUTED")
                        print(f"   Position: LONG {symbol}")
                        print(f"   Entry: ${entry_price:.2f}")
                        print(f"   Quantity: {quantity:.6f} BTC")
                        print(f"   Value: ${entry_price * quantity:.2f}")
                        print(f"   Stop Loss: ${risk_manager.stop_prices[symbol]:.2f}")
                        print(f"   Risk: 2% (${entry_price * quantity * 0.02:.2f})")
                else:
                    trades_rejected += 1
                    print("\n⏭️  Trade skipped - AI confidence below threshold")

                time.sleep(2)

        # Record equity
        portfolio.record_equity(timestamp, {symbol: current_price})

    # Final results
    print_header("PAPER TRADING RESULTS")

    metrics = portfolio.get_performance_metrics()

    if metrics:
        print("📊 PERFORMANCE SUMMARY")
        print("-" * 70)
        print(f"Initial Capital:    ${portfolio.initial_capital:,.2f}")
        print(f"Final Equity:       ${metrics['final_equity']:,.2f}")
        print(f"Total Return:       {metrics['total_return_pct']:+.2f}%")
        print(f"Profit/Loss:        ${metrics['final_equity'] - portfolio.initial_capital:+,.2f}\n")

        print("📈 TRADING STATISTICS")
        print("-" * 70)
        print(f"Total Signals:      {trades_executed + trades_rejected}")
        print(f"AI Approved:        {trades_executed} ✅")
        print(f"AI Rejected:        {trades_rejected} ❌")
        print(f"Approval Rate:      {(trades_executed / (trades_executed + trades_rejected) * 100) if (trades_executed + trades_rejected) > 0 else 0:.1f}%\n")

        print(f"Executed Trades:    {metrics['total_trades']}")
        print(f"Win Rate:           {metrics['win_rate_pct']:.1f}%")
        print(f"Average Win:        ${metrics['avg_win']:.2f}")
        print(f"Average Loss:       ${metrics['avg_loss']:.2f}")
        print(f"Profit Factor:      {metrics['profit_factor']:.2f}\n")

        print("⚡ RISK METRICS")
        print("-" * 70)
        print(f"Sharpe Ratio:       {metrics['sharpe_ratio']:.2f}")
        print(f"Max Drawdown:       {metrics['max_drawdown_pct']:.2f}%")
        print("-" * 70)

    print("\n✨ DEMO COMPLETE!")
    print("\nThis demo showed how Claude AI:")
    print("  ✓ Analyzes market conditions in real-time")
    print("  ✓ Provides confidence scores for each signal")
    print("  ✓ Validates trades before execution")
    print("  ✓ Helps avoid low-confidence trades")
    print("  ✓ Improves overall trading performance")

    print("\n📚 NEXT STEPS:")
    print("  1. Get MEXC API keys: https://www.mexc.com/user/openapi")
    print("  2. Get Claude AI key: https://console.anthropic.com/")
    print("  3. Set up config/secrets.yml with your keys")
    print("  4. Run: python scripts/trade_production.py --mode paper")
    print("  5. Monitor for 2+ weeks before considering live trading")

    print("\n" + "="*70)
    print("  Happy Trading! 🚀")
    print("="*70 + "\n")


if __name__ == '__main__':
    try:
        run_paper_trading_demo()
    except KeyboardInterrupt:
        print("\n\n⏸️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
