#!/usr/bin/env python3
"""
Live Trading Script

Run strategies with real money - USE WITH EXTREME CAUTION
"""

import sys
import os
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.config import Config
from src.exchanges.binance_adapter import BinanceAdapter
from src.strategies import (
    SMACrossStrategy, EMACrossStrategy, RSIStrategy,
    MACDStrategy, BollingerBandsStrategy, MultiIndicatorStrategy
)
from src.core.engine import TradingEngine


STRATEGY_MAP = {
    'sma_cross': SMACrossStrategy,
    'ema_cross': EMACrossStrategy,
    'rsi_strategy': RSIStrategy,
    'macd_strategy': MACDStrategy,
    'bollinger_bands': BollingerBandsStrategy,
    'multi_indicator': MultiIndicatorStrategy
}


def main():
    parser = argparse.ArgumentParser(description='Run live trading')
    parser.add_argument('--config', type=str, default='config/default.yml',
                        help='Path to config file')
    parser.add_argument('--strategy', type=str, help='Strategy name')
    parser.add_argument('--symbols', type=str, nargs='+', help='Trading symbols')
    parser.add_argument('--confirm', action='store_true',
                        help='Skip confirmation prompt (USE WITH CAUTION)')

    args = parser.parse_args()

    # Load configuration
    config = Config(args.config)

    # Safety check
    if not args.confirm:
        print("\n" + "=" * 60)
        print("WARNING: LIVE TRADING MODE")
        print("=" * 60)
        print("\nThis will place REAL orders with REAL money!")
        print("You can lose money quickly if the strategy is not profitable.")
        print("\nRecommendations:")
        print("  1. Test thoroughly with backtesting first")
        print("  2. Run in paper trading mode to verify")
        print("  3. Start with small amounts")
        print("  4. Use stop losses and risk limits")
        print("  5. Monitor constantly\n")

        confirmation = input("Type 'I UNDERSTAND THE RISKS' to continue: ")

        if confirmation != "I UNDERSTAND THE RISKS":
            print("\nLive trading cancelled.")
            sys.exit(0)

    # Get parameters
    strategy_name = args.strategy or config.strategy_name
    symbols = args.symbols or config.symbols

    # Initialize strategy
    if strategy_name not in STRATEGY_MAP:
        print(f"Error: Unknown strategy '{strategy_name}'")
        print(f"Available strategies: {', '.join(STRATEGY_MAP.keys())}")
        sys.exit(1)

    strategy_class = STRATEGY_MAP[strategy_name]
    strategy = strategy_class(config.strategy_params)

    # Initialize exchange
    api_key = config.get_secret('binance.api_key')
    api_secret = config.get_secret('binance.api_secret')

    if not api_key or not api_secret:
        print("Error: API credentials not found in secrets.yml")
        sys.exit(1)

    # For live trading, testnet should be False
    exchange = BinanceAdapter(api_key, api_secret, testnet=False)

    # Get initial balance
    try:
        balance = exchange.get_balance()
        print(f"\nCurrent balance: {balance}")
    except Exception as e:
        print(f"Error getting balance: {e}")
        print("Please check your API credentials")
        sys.exit(1)

    # Initialize trading engine
    engine = TradingEngine(
        strategy=strategy,
        exchange=exchange,
        mode='live',
        risk_config=config.risk_params,
        symbols=symbols
    )

    # Start live trading
    update_interval = config.get('live.update_interval', 60)

    print("\n" + "=" * 60)
    print("LIVE TRADING STARTED")
    print("=" * 60)
    print("\nPress Ctrl+C to stop\n")

    try:
        engine.start(interval=update_interval)
    except KeyboardInterrupt:
        print("\nStopping live trading...")
        engine.stop()


if __name__ == '__main__':
    main()
