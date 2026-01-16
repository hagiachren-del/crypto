#!/usr/bin/env python3
"""
Backtesting Script

Run backtests with historical data to evaluate strategy performance
"""

import sys
import os
import argparse
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.config import Config
from src.exchanges.binance_adapter import BinanceAdapter
from src.strategies import (
    SMACrossStrategy, EMACrossStrategy, RSIStrategy,
    MACDStrategy, BollingerBandsStrategy, MultiIndicatorStrategy
)
from src.backtest.runner import BacktestRunner
from src.utils.analytics import TradingAnalytics


STRATEGY_MAP = {
    'sma_cross': SMACrossStrategy,
    'ema_cross': EMACrossStrategy,
    'rsi_strategy': RSIStrategy,
    'macd_strategy': MACDStrategy,
    'bollinger_bands': BollingerBandsStrategy,
    'multi_indicator': MultiIndicatorStrategy
}


def main():
    parser = argparse.ArgumentParser(description='Run backtest')
    parser.add_argument('--config', type=str, default='config/default.yml',
                        help='Path to config file')
    parser.add_argument('--start', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, help='End date (YYYY-MM-DD)')
    parser.add_argument('--symbol', type=str, help='Trading symbol (e.g., BTC/USDT)')
    parser.add_argument('--strategy', type=str, help='Strategy name')
    parser.add_argument('--report', action='store_true', help='Generate visual report')

    args = parser.parse_args()

    # Load configuration
    config = Config(args.config)

    # Get parameters
    symbol = args.symbol or config.symbols[0]
    strategy_name = args.strategy or config.strategy_name
    start_date = args.start or config.get('backtest.start_date', '2023-01-01')
    end_date = args.end or config.get('backtest.end_date', '2024-01-01')

    # Parse dates
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')

    # Initialize strategy
    if strategy_name not in STRATEGY_MAP:
        print(f"Error: Unknown strategy '{strategy_name}'")
        print(f"Available strategies: {', '.join(STRATEGY_MAP.keys())}")
        sys.exit(1)

    strategy_class = STRATEGY_MAP[strategy_name]
    strategy = strategy_class(config.strategy_params)

    # Initialize exchange (no API keys needed for backtesting)
    exchange = BinanceAdapter()
    exchange.connect()

    # Initialize backtest runner
    runner = BacktestRunner(
        strategy=strategy,
        exchange=exchange,
        initial_capital=config.get('backtest.initial_capital', 10000),
        risk_config=config.risk_params,
        fee_config={
            'taker': config.get('fees.taker', 0.001),
            'maker': config.get('fees.maker', 0.0006),
            'slippage_bps': config.get('slippage_bps', 5)
        }
    )

    # Run backtest
    results = runner.run(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        timeframe=config.get('backtest.timeframe', '1h')
    )

    # Generate report if requested
    if args.report and config.get('reporting.generate_plots', True):
        analytics = TradingAnalytics()
        equity_df = runner.get_equity_curve_df()
        trades_df = runner.get_trades_df()

        analytics.generate_report(
            equity_df=equity_df,
            trades_df=trades_df,
            metrics=results,
            output_dir=config.get('reporting.output_dir', 'reports')
        )


if __name__ == '__main__':
    main()
