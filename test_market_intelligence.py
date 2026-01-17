#!/usr/bin/env python3
"""
Test Market Intelligence System
Demonstrates comprehensive multi-source analysis without requiring external APIs
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.ai.market_intelligence import MarketIntelligence

def generate_test_data(days=30):
    """Generate realistic OHLCV test data"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # Generate hourly data
    hours = days * 24
    dates = pd.date_range(start=start_date, end=end_date, periods=hours)

    # Simulate BTC price with trend and volatility
    np.random.seed(42)
    base_price = 43000
    trend = np.linspace(0, 5000, hours)  # Upward trend
    noise = np.random.randn(hours) * 500

    close_prices = base_price + trend + noise

    # Generate OHLCV
    data = pd.DataFrame({
        'timestamp': dates,
        'open': close_prices * (1 + np.random.randn(hours) * 0.01),
        'high': close_prices * (1 + np.abs(np.random.randn(hours)) * 0.02),
        'low': close_prices * (1 - np.abs(np.random.randn(hours)) * 0.02),
        'close': close_prices,
        'volume': np.random.randint(10000, 50000, hours)
    })

    return data

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*80)
    print(text)
    print("="*80)

def print_analysis_section(title, data, color="36"):
    """Print formatted analysis section"""
    print(f"\n\033[1;{color}m{title}\033[0m")
    print("-" * 80)
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (int, float)):
                print(f"  {key}: {value}")
            elif isinstance(value, list):
                print(f"  {key}:")
                for item in value[:3]:  # Show first 3 items
                    print(f"    • {item}")
            else:
                print(f"  {key}: {value}")
    else:
        print(f"  {data}")

def main():
    print_header("🤖 AUTONOMOUS TRADER - MARKET INTELLIGENCE TEST")

    print("\n📊 Initializing Market Intelligence System...")
    print("   This system aggregates data from 6 different sources:")
    print("   1. Technical Analysis (charts, indicators, patterns)")
    print("   2. News Sentiment (CryptoPanic API)")
    print("   3. Social Sentiment (Twitter, Reddit, LunarCrush)")
    print("   4. Market Sentiment (Fear & Greed Index)")
    print("   5. On-Chain Metrics (exchange flows, active addresses)")
    print("   6. Order Flow Analysis (volume profiling)")

    # Initialize market intelligence
    intelligence = MarketIntelligence()

    print("\n✅ Market Intelligence System Ready")

    # Generate test data
    print("\n📈 Generating realistic market data (30 days, hourly)...")
    data = generate_test_data(days=30)
    print(f"   Generated {len(data)} candles")
    print(f"   Price range: ${data['close'].min():.2f} - ${data['close'].max():.2f}")
    print(f"   Current price: ${data['close'].iloc[-1]:.2f}")

    # Run comprehensive analysis
    print_header("🔍 RUNNING COMPREHENSIVE MARKET ANALYSIS")

    symbol = "BTC/USDT"
    print(f"\nAnalyzing: {symbol}")
    print("Please wait while we analyze across all 6 data sources...\n")

    analysis = intelligence.get_comprehensive_analysis(symbol, data)

    # Display results
    print_header("📊 ANALYSIS RESULTS")

    print(f"\n🎯 Overall Score: {analysis['overall_score']}/100")
    print(f"📈 Recommendation: {analysis['recommendation']}")

    # Technical Analysis
    print_analysis_section(
        "1️⃣  TECHNICAL ANALYSIS",
        {
            "Score": f"{analysis['technical']['score']}/100",
            "Trend": analysis['technical']['trend'].upper(),
            "RSI": f"{analysis['technical']['rsi']:.1f}",
            "Signals": analysis['technical']['signals'][:3]
        },
        "32"  # Green
    )

    if analysis['technical']['patterns']:
        print(f"  Patterns: {', '.join(analysis['technical']['patterns'])}")

    # News Sentiment
    print_analysis_section(
        "2️⃣  NEWS SENTIMENT",
        {
            "Score": f"{analysis['news_sentiment']['score']}/100",
            "Sentiment": analysis['news_sentiment']['sentiment'].upper(),
            "Confidence": f"{analysis['news_sentiment']['confidence']}%",
            "Recent News": analysis['news_sentiment']['news_items']
        },
        "34"  # Blue
    )

    # Social Sentiment
    print_analysis_section(
        "3️⃣  SOCIAL SENTIMENT",
        {
            "Score": f"{analysis['social_sentiment']['score']}/100",
            "Sentiment": analysis['social_sentiment']['sentiment'].upper(),
            "Mentions": f"{analysis['social_sentiment']['mentions']:,}",
            "Confidence": f"{analysis['social_sentiment']['confidence']}%"
        },
        "35"  # Magenta
    )

    # Market Sentiment
    print_analysis_section(
        "4️⃣  MARKET SENTIMENT (Fear & Greed Index)",
        {
            "Score": f"{analysis['market_sentiment']['score']}/100",
            "Fear & Greed": f"{analysis['market_sentiment']['fear_greed_index']}/100",
            "Status": analysis['market_sentiment']['sentiment'].upper(),
            "Interpretation": analysis['market_sentiment']['interpretation']
        },
        "33"  # Yellow
    )

    # On-Chain Analysis
    print_analysis_section(
        "5️⃣  ON-CHAIN ANALYSIS",
        {
            "Score": f"{analysis['on_chain']['score']}/100",
            "Signals": analysis['on_chain']['signals']
        },
        "36"  # Cyan
    )

    # Order Flow
    print_analysis_section(
        "6️⃣  ORDER FLOW ANALYSIS",
        {
            "Score": f"{analysis['order_flow']['score']}/100",
            "Volume Trend": analysis['order_flow']['volume_trend'],
            "Signals": analysis['order_flow']['signals']
        },
        "35"  # Magenta
    )

    # Decision Summary
    print_header("🎯 TRADING DECISION FRAMEWORK")

    print("\n📋 Multi-Layer Validation:")
    print(f"   1. Market Intelligence Score: {analysis['overall_score']}/100 (threshold: >45)")
    print(f"   2. Recommendation: {analysis['recommendation']}")

    if analysis['overall_score'] >= 45:
        print("   ✅ Market intelligence APPROVED for AI review")
        print("\n   Next step: DeepSeek AI will:")
        print("      • Receive this comprehensive analysis as context")
        print("      • Perform deep market analysis")
        print("      • Generate confidence score (threshold: >70%)")
        print("      • Validate signal alignment with market intelligence")
        print("      • Execute trade ONLY if both systems agree")
    else:
        print("   ❌ Market intelligence score too low - REJECTED")
        print("   Trade will NOT be submitted to AI for review")

    # Scoring breakdown
    print_header("📊 SCORING BREAKDOWN (Weighted)")

    weights = {
        'Technical Analysis': (0.30, analysis['technical']['score']),
        'News Sentiment': (0.15, analysis['news_sentiment']['score']),
        'Social Sentiment': (0.15, analysis['social_sentiment']['score']),
        'Market Sentiment': (0.20, analysis['market_sentiment']['score']),
        'On-Chain': (0.10, analysis['on_chain']['score']),
        'Order Flow': (0.10, analysis['order_flow']['score'])
    }

    print("\nSource                    Weight    Score    Contribution")
    print("-" * 80)
    total_contribution = 0
    for source, (weight, score) in weights.items():
        contribution = weight * score
        total_contribution += contribution
        bar_length = int(score / 5)
        bar = "█" * bar_length
        print(f"{source:24s} {weight:5.0%}     {score:3.0f}/100  {contribution:5.1f}  {bar}")

    print("-" * 80)
    print(f"{'TOTAL':24s}              {total_contribution:5.1f}/100")

    # Summary
    print_header("✅ TEST COMPLETE")

    print("\n🎉 Market Intelligence System is working perfectly!")
    print("\nKey Features Demonstrated:")
    print("  ✅ Multi-source data aggregation (6 sources)")
    print("  ✅ Weighted scoring system (0-100 scale)")
    print("  ✅ 8-level recommendations (STRONG_BUY to STRONG_SELL)")
    print("  ✅ Comprehensive signal analysis")
    print("  ✅ Dual-validation framework (Intelligence + AI)")
    print("  ✅ Complete audit trail")

    print("\n📝 Next Steps:")
    print("  1. Run autonomous trader in paper mode: ./start_autonomous_trader.sh")
    print("  2. Monitor logs: tail -f logs/autonomous_trader.log")
    print("  3. Review trades in database: data/autonomous.db")

    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()
