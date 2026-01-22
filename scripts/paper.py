#!/usr/bin/env python3
"""
Paper Trading Script

Run strategies with real-time market data but simulated orders
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
    parser = argparse.ArgumentParser(description='Run paper trading')
    parser.add_argument('--config', type=str, default='config/default.yml',
                        help='Path to config file')
    parser.add_argument('--strategy', type=str, help='Strategy name')
    parser.add_argument('--symbols', type=str, nargs='+', help='Trading symbols')

    args = parser.parse_args()

    # Load configuration
    config = Config(args.config)

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
    testnet = config.get_secret('binance.testnet', True)

    exchange = BinanceAdapter(api_key, api_secret, testnet)

    # Initialize trading engine
    engine = TradingEngine(
        strategy=strategy,
        exchange=exchange,
        mode='paper',
        initial_capital=config.get('paper.initial_capital', 10000),
        risk_config=config.risk_params,
        symbols=symbols
    )

    # Start paper trading
    update_interval = config.get('paper.update_interval', 60)

    print("\n" + "=" * 60)
    print("PAPER TRADING MODE")
    print("=" * 60)
    print("\nThis is simulated trading with real market data.")
    print("No real orders will be placed.\n")
    print("Press Ctrl+C to stop\n")

    try:
        engine.start(interval=update_interval)
    except KeyboardInterrupt:
        print("\nStopping paper trading...")
        engine.stop()


if __name__ == '__main__':
    main()
