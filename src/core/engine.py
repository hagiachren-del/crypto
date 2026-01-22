"""Main trading engine for live and paper trading"""

import time
from typing import Dict, Optional
from datetime import datetime
import pandas as pd
from src.core.portfolio import Portfolio
from src.core.risk import RiskManager
from src.strategies.base import Strategy
from src.exchanges.base import BaseExchange


class TradingEngine:
    """
    Main trading engine for executing strategies in real-time

    Supports both paper trading and live trading modes
    """

    def __init__(self, strategy: Strategy, exchange: BaseExchange,
                 mode: str = 'paper',
                 initial_capital: float = 10000.0,
                 risk_config: Optional[Dict] = None,
                 symbols: Optional[list] = None):
        """
        Initialize trading engine

        Args:
            strategy: Trading strategy instance
            exchange: Exchange adapter
            mode: Trading mode ('paper' or 'live')
            initial_capital: Initial capital
            risk_config: Risk management configuration
            symbols: List of symbols to trade
        """
        self.strategy = strategy
        self.exchange = exchange
        self.mode = mode
        self.initial_capital = initial_capital
        self.symbols = symbols or ['BTC/USDT']

        # Initialize components
        self.portfolio = Portfolio(initial_capital)
        self.risk_manager = RiskManager(risk_config or {})

        # State
        self.running = False
        self.data_buffer: Dict[str, pd.DataFrame] = {}

        # Connect to exchange
        if not self.exchange.connect():
            raise ConnectionError("Failed to connect to exchange")

    def start(self, interval: int = 60):
        """
        Start trading engine

        Args:
            interval: Update interval in seconds
        """
        print(f"\n{'=' * 60}")
        print(f"Starting Trading Engine: {self.mode.upper()} mode")
        print(f"Strategy: {self.strategy.get_name()}")
        print(f"Symbols: {', '.join(self.symbols)}")
        print(f"Initial Capital: ${self.initial_capital:,.2f}")
        print(f"{'=' * 60}\n")

        self.running = True
        self.risk_manager.peak_equity = self.initial_capital

        try:
            while self.running:
                self._process_tick()
                time.sleep(interval)

        except KeyboardInterrupt:
            print("\nShutting down trading engine...")
            self.stop()

    def stop(self):
        """Stop trading engine"""
        self.running = False

        # Close all positions
        for symbol in list(self.portfolio.positions.keys()):
            self._close_position(symbol, "Engine shutdown")

        # Print final stats
        self._print_summary()

    def _process_tick(self):
        """Process single tick"""
        current_time = datetime.now()

        for symbol in self.symbols:
            try:
                # Fetch latest data
                ticker = self.exchange.get_ticker(symbol)
                current_price = ticker['last']

                # Update data buffer
                if symbol not in self.data_buffer:
                    # Fetch historical data for indicator calculation
                    data = self.exchange.get_ohlcv(symbol, '1h', limit=100)
                    self.data_buffer[symbol] = data
                else:
                    # Append new candle (simplified - in production would check timeframe)
                    # For now, just update the last row
                    pass

                # Check existing positions
                if self.portfolio.has_position(symbol):
                    position = self.portfolio.get_position(symbol)

                    # Check exit conditions
                    should_exit, reason = self.risk_manager.should_close_position(
                        symbol, current_price, position.side, position.entry_price
                    )

                    if should_exit:
                        self._close_position(symbol, reason)
                        continue

                # Generate signal if no position
                else:
                    data = self.data_buffer.get(symbol)
                    if data is not None and len(data) > 0:
                        signal = self.strategy.on_data(data)

                        if signal in ['buy', 'sell']:
                            self._open_position(symbol, signal, current_price, current_time)

                # Record equity
                prices = {sym: self.exchange.get_ticker(sym)['last'] for sym in self.symbols}
                self.portfolio.record_equity(current_time, prices)
                self.risk_manager.update_peak_equity(self.portfolio.get_total_value(prices))

            except Exception as e:
                print(f"Error processing {symbol}: {e}")

    def _open_position(self, symbol: str, signal: str, price: float, timestamp: datetime):
        """
        Open a new position

        Args:
            symbol: Trading pair symbol
            signal: Signal ('buy' or 'sell')
            price: Current price
            timestamp: Current timestamp
        """
        position_side = 'long' if signal == 'buy' else 'short'

        # Check risk limits
        portfolio_value = self.portfolio.get_total_value({symbol: price})
        can_open, reason = self.risk_manager.can_open_position(
            symbol, 1.0, price, portfolio_value, len(self.portfolio.positions)
        )

        if not can_open:
            print(f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] Cannot open position: {reason}")
            return

        # Calculate position size
        quantity = self.risk_manager.calculate_position_size(portfolio_value, price)

        # In paper mode, simulate order
        if self.mode == 'paper':
            fees = price * quantity * 0.001  # Assume 0.1% fee

            success = self.portfolio.open_position(
                symbol, position_side, quantity, price, timestamp, fees
            )

            if success:
                self.risk_manager.set_stop_loss(symbol, price, position_side)
                print(f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] OPENED {position_side.upper()} "
                      f"{symbol} - Price: ${price:.2f}, Qty: {quantity:.6f}")

        # In live mode, place actual order
        elif self.mode == 'live':
            try:
                order_side = 'buy' if signal == 'buy' else 'sell'
                order = self.exchange.create_order(
                    symbol=symbol,
                    order_type='market',
                    side=order_side,
                    amount=quantity
                )

                if order['status'] == 'filled' or order['status'] == 'closed':
                    actual_price = order['price']
                    fees = actual_price * quantity * 0.001

                    self.portfolio.open_position(
                        symbol, position_side, quantity, actual_price, timestamp, fees
                    )
                    self.risk_manager.set_stop_loss(symbol, actual_price, position_side)

                    print(f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] OPENED {position_side.upper()} "
                          f"{symbol} - Price: ${actual_price:.2f}, Qty: {quantity:.6f}, "
                          f"Order ID: {order['id']}")

            except Exception as e:
                print(f"Error placing order: {e}")

    def _close_position(self, symbol: str, reason: str):
        """
        Close an existing position

        Args:
            symbol: Trading pair symbol
            reason: Reason for closing
        """
        if not self.portfolio.has_position(symbol):
            return

        position = self.portfolio.get_position(symbol)
        timestamp = datetime.now()

        # In paper mode, simulate close
        if self.mode == 'paper':
            ticker = self.exchange.get_ticker(symbol)
            price = ticker['last']
            fees = price * position.quantity * 0.001

            pnl = self.portfolio.close_position(symbol, price, timestamp, fees)

            if pnl is not None:
                self.risk_manager.record_trade(pnl)
                print(f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] CLOSED {symbol} - "
                      f"{reason} - Price: ${price:.2f}, PnL: ${pnl:.2f}")

        # In live mode, place actual close order
        elif self.mode == 'live':
            try:
                order_side = 'sell' if position.side == 'long' else 'buy'
                order = self.exchange.create_order(
                    symbol=symbol,
                    order_type='market',
                    side=order_side,
                    amount=position.quantity
                )

                if order['status'] == 'filled' or order['status'] == 'closed':
                    price = order['price']
                    fees = price * position.quantity * 0.001

                    pnl = self.portfolio.close_position(symbol, price, timestamp, fees)

                    if pnl is not None:
                        self.risk_manager.record_trade(pnl)
                        print(f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] CLOSED {symbol} - "
                              f"{reason} - Price: ${price:.2f}, PnL: ${pnl:.2f}, "
                              f"Order ID: {order['id']}")

            except Exception as e:
                print(f"Error closing position: {e}")

    def _print_summary(self):
        """Print trading summary"""
        print(f"\n{'=' * 60}")
        print("TRADING SESSION SUMMARY")
        print(f"{'=' * 60}\n")

        metrics = self.portfolio.get_performance_metrics()

        if metrics:
            print(f"Initial Capital:      ${self.initial_capital:,.2f}")
            print(f"Final Equity:         ${metrics['final_equity']:,.2f}")
            print(f"Total Return:         {metrics['total_return_pct']:.2f}%")
            print(f"Total Trades:         {metrics['total_trades']}")
            print(f"Win Rate:             {metrics['win_rate_pct']:.2f}%")
            print(f"Sharpe Ratio:         {metrics['sharpe_ratio']:.2f}")
            print(f"Max Drawdown:         {metrics['max_drawdown_pct']:.2f}%")
        else:
            print("No trades executed")

        print(f"\n{'=' * 60}\n")

    def get_status(self) -> Dict:
        """
        Get current engine status

        Returns:
            Dictionary with status information
        """
        prices = {}
        for symbol in self.symbols:
            try:
                ticker = self.exchange.get_ticker(symbol)
                prices[symbol] = ticker['last']
            except:
                prices[symbol] = 0.0

        return {
            'running': self.running,
            'mode': self.mode,
            'portfolio_value': self.portfolio.get_total_value(prices),
            'cash': self.portfolio.cash,
            'open_positions': len(self.portfolio.positions),
            'total_trades': len([t for t in self.portfolio.trades if t['type'] == 'close']),
            'risk_metrics': self.risk_manager.get_risk_metrics()
        }
