"""Professional backtesting engine with comprehensive metrics"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, List
from datetime import datetime
from src.core.portfolio import Portfolio
from src.core.risk import RiskManager
from src.strategies.base import Strategy
from src.exchanges.base import BaseExchange


class BacktestRunner:
    """
    Comprehensive backtesting engine

    Features:
    - Historical data simulation
    - Realistic fee modeling
    - Slippage simulation
    - Multiple performance metrics
    - Trade-by-trade analysis
    """

    def __init__(self, strategy: Strategy, exchange: BaseExchange,
                 initial_capital: float = 10000.0,
                 risk_config: Optional[Dict] = None,
                 fee_config: Optional[Dict] = None):
        """
        Initialize backtest runner

        Args:
            strategy: Trading strategy instance
            exchange: Exchange adapter for data
            initial_capital: Initial capital
            risk_config: Risk management configuration
            fee_config: Fee configuration
        """
        self.strategy = strategy
        self.exchange = exchange
        self.initial_capital = initial_capital

        # Initialize components
        self.portfolio = Portfolio(initial_capital)
        self.risk_manager = RiskManager(risk_config or {})

        # Fee configuration
        self.taker_fee = fee_config.get('taker', 0.001) if fee_config else 0.001
        self.maker_fee = fee_config.get('maker', 0.0006) if fee_config else 0.0006
        self.slippage_bps = fee_config.get('slippage_bps', 5) if fee_config else 5

        # Results
        self.results: Dict = {}
        self.trades: List[Dict] = []

    def run(self, symbol: str, start_date: datetime, end_date: datetime,
            timeframe: str = '1h') -> Dict:
        """
        Run backtest

        Args:
            symbol: Trading pair symbol
            start_date: Backtest start date
            end_date: Backtest end date
            timeframe: Candle timeframe

        Returns:
            Dictionary with backtest results
        """
        print(f"\n{'=' * 60}")
        print(f"Running Backtest: {self.strategy.get_name()}")
        print(f"Symbol: {symbol}")
        print(f"Period: {start_date.date()} to {end_date.date()}")
        print(f"Initial Capital: ${self.initial_capital:,.2f}")
        print(f"{'=' * 60}\n")

        # Fetch historical data
        print("Fetching historical data...")
        data = self.exchange.get_ohlcv(symbol, timeframe, start_date)

        # Filter by end date
        data = data[data.index <= end_date]

        if len(data) == 0:
            print("No data available for the specified period")
            return {}

        print(f"Data loaded: {len(data)} candles\n")

        # Reset portfolio and strategy
        self.portfolio.reset()
        self.strategy.reset()
        self.risk_manager.peak_equity = self.initial_capital

        # Run simulation
        print("Running simulation...")
        position_open = False
        position_side = None
        entry_price = 0.0
        highest_price = 0.0
        lowest_price = float('inf')

        for i in range(len(data)):
            current_data = data.iloc[:i + 1]
            current_candle = data.iloc[i]
            current_price = current_candle['close']
            timestamp = data.index[i]

            # Update price tracking for trailing stop
            if position_open:
                highest_price = max(highest_price, current_candle['high'])
                lowest_price = min(lowest_price, current_candle['low'])

                # Check trailing stop
                if self.risk_manager.trailing_stop:
                    self.risk_manager.update_trailing_stop(
                        symbol, current_price, position_side,
                        highest_price, lowest_price
                    )

                # Check exit conditions
                should_exit, exit_reason = self.risk_manager.should_close_position(
                    symbol, current_price, position_side, entry_price
                )

                if should_exit:
                    # Close position
                    fees = current_price * self.portfolio.get_position(symbol).quantity * self.taker_fee
                    slippage = self._calculate_slippage(current_price)
                    exit_price = current_price - slippage if position_side == 'long' else current_price + slippage

                    pnl = self.portfolio.close_position(symbol, exit_price, timestamp, fees)

                    if pnl is not None:
                        self.risk_manager.record_trade(pnl)
                        print(f"[{timestamp.strftime('%Y-%m-%d %H:%M')}] CLOSE - {exit_reason} - "
                              f"Price: ${exit_price:.2f}, PnL: ${pnl:.2f}")

                    position_open = False
                    position_side = None
                    highest_price = 0.0
                    lowest_price = float('inf')

            # Generate signal if no position
            if not position_open:
                signal = self.strategy.on_data(current_data)

                if signal in ['buy', 'sell']:
                    # Determine position side
                    position_side = 'long' if signal == 'buy' else 'short'

                    # Calculate position size
                    portfolio_value = self.portfolio.get_total_value({symbol: current_price})

                    can_open, reason = self.risk_manager.can_open_position(
                        symbol, 1.0, current_price, portfolio_value, len(self.portfolio.positions)
                    )

                    if can_open:
                        quantity = self.risk_manager.calculate_position_size(
                            portfolio_value, current_price
                        )

                        # Apply slippage
                        slippage = self._calculate_slippage(current_price)
                        entry_price = current_price + slippage if signal == 'buy' else current_price - slippage

                        # Calculate fees
                        fees = entry_price * quantity * self.taker_fee

                        # Open position
                        success = self.portfolio.open_position(
                            symbol, position_side, quantity, entry_price, timestamp, fees
                        )

                        if success:
                            # Set stop loss
                            self.risk_manager.set_stop_loss(symbol, entry_price, position_side)

                            position_open = True
                            highest_price = entry_price
                            lowest_price = entry_price

                            print(f"[{timestamp.strftime('%Y-%m-%d %H:%M')}] OPEN {position_side.upper()} - "
                                  f"Price: ${entry_price:.2f}, Qty: {quantity:.6f}")

            # Record equity
            self.portfolio.record_equity(timestamp, {symbol: current_price})
            self.risk_manager.update_peak_equity(
                self.portfolio.get_total_value({symbol: current_price})
            )

        # Close any remaining positions
        if position_open:
            final_price = data.iloc[-1]['close']
            final_timestamp = data.index[-1]
            fees = final_price * self.portfolio.get_position(symbol).quantity * self.taker_fee

            pnl = self.portfolio.close_position(symbol, final_price, final_timestamp, fees)
            if pnl is not None:
                self.risk_manager.record_trade(pnl)
                print(f"\n[{final_timestamp.strftime('%Y-%m-%d %H:%M')}] CLOSE (End of backtest) - "
                      f"Price: ${final_price:.2f}, PnL: ${pnl:.2f}")

        # Calculate results
        self.results = self._calculate_metrics(data, symbol)

        # Print results
        self._print_results()

        return self.results

    def _calculate_slippage(self, price: float) -> float:
        """Calculate slippage based on price and slippage basis points"""
        return price * (self.slippage_bps / 10000.0)

    def _calculate_metrics(self, data: pd.DataFrame, symbol: str) -> Dict:
        """Calculate comprehensive performance metrics"""
        equity_curve = self.portfolio.get_equity_curve_df()

        if len(equity_curve) < 2:
            return {}

        final_equity = equity_curve['equity'].iloc[-1]
        total_return = (final_equity / self.initial_capital - 1) * 100

        # Returns
        returns = equity_curve['equity'].pct_change().dropna()

        # Time-based metrics
        days = (equity_curve.index[-1] - equity_curve.index[0]).days
        years = days / 365.25

        # CAGR (Compound Annual Growth Rate)
        if years > 0:
            cagr = ((final_equity / self.initial_capital) ** (1 / years) - 1) * 100
        else:
            cagr = 0

        # Volatility (annualized)
        volatility = returns.std() * np.sqrt(252) * 100

        # Sharpe Ratio
        if returns.std() > 0:
            sharpe = (returns.mean() / returns.std()) * np.sqrt(252)
        else:
            sharpe = 0

        # Sortino Ratio (downside deviation)
        downside_returns = returns[returns < 0]
        if len(downside_returns) > 0 and downside_returns.std() > 0:
            sortino = (returns.mean() / downside_returns.std()) * np.sqrt(252)
        else:
            sortino = 0

        # Drawdown analysis
        cumulative = equity_curve['equity']
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max * 100
        max_drawdown = drawdown.min()

        # Trade statistics
        trades_df = self.portfolio.get_trades_df()
        closed_trades = trades_df[trades_df['type'] == 'close']

        if len(closed_trades) > 0:
            winning_trades = closed_trades[closed_trades['pnl'] > 0]
            losing_trades = closed_trades[closed_trades['pnl'] < 0]

            total_trades = len(closed_trades)
            win_rate = (len(winning_trades) / total_trades) * 100

            avg_win = winning_trades['pnl'].mean() if len(winning_trades) > 0 else 0
            avg_loss = losing_trades['pnl'].mean() if len(losing_trades) > 0 else 0

            largest_win = winning_trades['pnl'].max() if len(winning_trades) > 0 else 0
            largest_loss = losing_trades['pnl'].min() if len(losing_trades) > 0 else 0

            total_profit = winning_trades['pnl'].sum() if len(winning_trades) > 0 else 0
            total_loss = abs(losing_trades['pnl'].sum()) if len(losing_trades) > 0 else 0

            profit_factor = total_profit / total_loss if total_loss > 0 else 0

            # Expectancy
            expectancy = (win_rate / 100 * avg_win) - ((1 - win_rate / 100) * abs(avg_loss))
        else:
            total_trades = 0
            win_rate = 0
            avg_win = 0
            avg_loss = 0
            largest_win = 0
            largest_loss = 0
            profit_factor = 0
            expectancy = 0

        return {
            # Equity metrics
            'initial_capital': self.initial_capital,
            'final_equity': final_equity,
            'total_return_pct': total_return,
            'cagr_pct': cagr,

            # Risk metrics
            'volatility_pct': volatility,
            'sharpe_ratio': sharpe,
            'sortino_ratio': sortino,
            'max_drawdown_pct': max_drawdown,

            # Trade statistics
            'total_trades': total_trades,
            'win_rate_pct': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'largest_win': largest_win,
            'largest_loss': largest_loss,
            'profit_factor': profit_factor,
            'expectancy': expectancy,

            # Time
            'backtest_days': days,
            'backtest_years': years
        }

    def _print_results(self):
        """Print formatted backtest results"""
        if not self.results:
            return

        print(f"\n{'=' * 60}")
        print("BACKTEST RESULTS")
        print(f"{'=' * 60}\n")

        print("EQUITY METRICS:")
        print(f"  Initial Capital:      ${self.results['initial_capital']:,.2f}")
        print(f"  Final Equity:         ${self.results['final_equity']:,.2f}")
        print(f"  Total Return:         {self.results['total_return_pct']:.2f}%")
        print(f"  CAGR:                 {self.results['cagr_pct']:.2f}%")

        print("\nRISK METRICS:")
        print(f"  Volatility:           {self.results['volatility_pct']:.2f}%")
        print(f"  Sharpe Ratio:         {self.results['sharpe_ratio']:.2f}")
        print(f"  Sortino Ratio:        {self.results['sortino_ratio']:.2f}")
        print(f"  Max Drawdown:         {self.results['max_drawdown_pct']:.2f}%")

        print("\nTRADE STATISTICS:")
        print(f"  Total Trades:         {self.results['total_trades']}")
        print(f"  Win Rate:             {self.results['win_rate_pct']:.2f}%")
        print(f"  Avg Win:              ${self.results['avg_win']:.2f}")
        print(f"  Avg Loss:             ${self.results['avg_loss']:.2f}")
        print(f"  Largest Win:          ${self.results['largest_win']:.2f}")
        print(f"  Largest Loss:         ${self.results['largest_loss']:.2f}")
        print(f"  Profit Factor:        {self.results['profit_factor']:.2f}")
        print(f"  Expectancy:           ${self.results['expectancy']:.2f}")

        print(f"\n{'=' * 60}\n")

    def get_trades_df(self) -> pd.DataFrame:
        """Get trades as DataFrame"""
        return self.portfolio.get_trades_df()

    def get_equity_curve_df(self) -> pd.DataFrame:
        """Get equity curve as DataFrame"""
        return self.portfolio.get_equity_curve_df()
