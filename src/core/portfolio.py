"""Portfolio management system"""

from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd
import numpy as np


class Position:
    """Represents a trading position"""

    def __init__(self, symbol: str, side: str, quantity: float, entry_price: float,
                 timestamp: datetime):
        """
        Initialize position

        Args:
            symbol: Trading pair symbol
            side: Position side ('long' or 'short')
            quantity: Position size
            entry_price: Entry price
            timestamp: Entry timestamp
        """
        self.symbol = symbol
        self.side = side
        self.quantity = quantity
        self.entry_price = entry_price
        self.timestamp = timestamp
        self.realized_pnl = 0.0
        self.fees = 0.0

    def get_unrealized_pnl(self, current_price: float) -> float:
        """
        Calculate unrealized PnL

        Args:
            current_price: Current market price

        Returns:
            Unrealized PnL
        """
        if self.side == 'long':
            return (current_price - self.entry_price) * self.quantity
        else:  # short
            return (self.entry_price - current_price) * self.quantity

    def get_pnl_percentage(self, current_price: float) -> float:
        """
        Calculate PnL percentage

        Args:
            current_price: Current market price

        Returns:
            PnL percentage
        """
        pnl = self.get_unrealized_pnl(current_price)
        return (pnl / (self.entry_price * self.quantity)) * 100

    def __repr__(self) -> str:
        return (f"Position(symbol={self.symbol}, side={self.side}, "
                f"qty={self.quantity}, entry={self.entry_price})")


class Portfolio:
    """Multi-asset portfolio manager"""

    def __init__(self, initial_capital: float = 10000.0):
        """
        Initialize portfolio

        Args:
            initial_capital: Initial capital in base currency
        """
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}
        self.closed_positions: List[Position] = []
        self.trades: List[Dict] = []
        self.equity_curve: List[Dict] = []

    def open_position(self, symbol: str, side: str, quantity: float, price: float,
                      timestamp: datetime, fees: float = 0.0) -> bool:
        """
        Open a new position

        Args:
            symbol: Trading pair symbol
            side: Position side ('long' or 'short')
            quantity: Position size
            price: Entry price
            timestamp: Entry timestamp
            fees: Trading fees

        Returns:
            True if position opened successfully
        """
        cost = quantity * price + fees

        if cost > self.cash:
            return False

        position = Position(symbol, side, quantity, price, timestamp)
        position.fees += fees

        self.positions[symbol] = position
        self.cash -= cost

        # Record trade
        self.trades.append({
            'timestamp': timestamp,
            'symbol': symbol,
            'side': side,
            'type': 'open',
            'quantity': quantity,
            'price': price,
            'fees': fees,
            'cash': self.cash
        })

        return True

    def close_position(self, symbol: str, price: float, timestamp: datetime,
                       fees: float = 0.0) -> Optional[float]:
        """
        Close an existing position

        Args:
            symbol: Trading pair symbol
            price: Exit price
            timestamp: Exit timestamp
            fees: Trading fees

        Returns:
            Realized PnL or None if no position exists
        """
        if symbol not in self.positions:
            return None

        position = self.positions[symbol]

        # Calculate PnL
        if position.side == 'long':
            proceeds = position.quantity * price - fees
            cost = position.quantity * position.entry_price
            pnl = proceeds - cost
        else:  # short
            cost = position.quantity * price + fees
            proceeds = position.quantity * position.entry_price
            pnl = proceeds - cost

        position.realized_pnl = pnl - position.fees
        self.cash += position.quantity * price - fees

        # Record trade
        self.trades.append({
            'timestamp': timestamp,
            'symbol': symbol,
            'side': 'close',
            'type': 'close',
            'quantity': position.quantity,
            'price': price,
            'fees': fees,
            'pnl': position.realized_pnl,
            'cash': self.cash
        })

        # Move to closed positions
        self.closed_positions.append(position)
        del self.positions[symbol]

        return position.realized_pnl

    def update_position(self, symbol: str, quantity: float, price: float,
                        timestamp: datetime, fees: float = 0.0) -> bool:
        """
        Update existing position (add or reduce)

        Args:
            symbol: Trading pair symbol
            quantity: Quantity to add (positive) or reduce (negative)
            price: Current price
            timestamp: Timestamp
            fees: Trading fees

        Returns:
            True if successful
        """
        if symbol not in self.positions:
            return False

        position = self.positions[symbol]

        if quantity > 0:
            # Add to position
            cost = quantity * price + fees
            if cost > self.cash:
                return False

            total_quantity = position.quantity + quantity
            position.entry_price = ((position.entry_price * position.quantity) +
                                    (price * quantity)) / total_quantity
            position.quantity = total_quantity
            position.fees += fees
            self.cash -= cost

        elif quantity < 0:
            # Reduce position
            quantity = abs(quantity)
            if quantity > position.quantity:
                return False

            # Partial close
            pnl_ratio = quantity / position.quantity
            realized_pnl = position.get_unrealized_pnl(price) * pnl_ratio

            position.realized_pnl += realized_pnl - (fees * pnl_ratio)
            position.quantity -= quantity
            self.cash += quantity * price - fees

            if position.quantity == 0:
                self.closed_positions.append(position)
                del self.positions[symbol]

        return True

    def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for symbol"""
        return self.positions.get(symbol)

    def has_position(self, symbol: str) -> bool:
        """Check if position exists"""
        return symbol in self.positions

    def get_total_value(self, prices: Dict[str, float]) -> float:
        """
        Get total portfolio value

        Args:
            prices: Dictionary of current prices

        Returns:
            Total portfolio value
        """
        value = self.cash

        for symbol, position in self.positions.items():
            if symbol in prices:
                value += position.quantity * prices[symbol]

        return value

    def get_equity_curve_df(self) -> pd.DataFrame:
        """
        Get equity curve as DataFrame

        Returns:
            DataFrame with equity curve
        """
        if not self.equity_curve:
            return pd.DataFrame()

        df = pd.DataFrame(self.equity_curve)
        if 'timestamp' in df.columns:
            df.set_index('timestamp', inplace=True)

        return df

    def get_trades_df(self) -> pd.DataFrame:
        """
        Get trades as DataFrame

        Returns:
            DataFrame with all trades
        """
        if not self.trades:
            return pd.DataFrame()

        df = pd.DataFrame(self.trades)
        if 'timestamp' in df.columns:
            df.set_index('timestamp', inplace=True)

        return df

    def get_performance_metrics(self) -> Dict:
        """
        Calculate portfolio performance metrics

        Returns:
            Dictionary with performance metrics
        """
        if not self.equity_curve:
            return {}

        df = self.get_equity_curve_df()

        if len(df) < 2:
            return {}

        returns = df['equity'].pct_change().dropna()

        # Calculate metrics
        total_return = (df['equity'].iloc[-1] / self.initial_capital - 1) * 100
        total_trades = len([t for t in self.trades if t['type'] == 'close'])

        if total_trades > 0:
            winning_trades = len([t for t in self.trades if t.get('pnl', 0) > 0])
            losing_trades = len([t for t in self.trades if t.get('pnl', 0) < 0])
            win_rate = (winning_trades / total_trades) * 100

            profits = [t['pnl'] for t in self.trades if t.get('pnl', 0) > 0]
            losses = [t['pnl'] for t in self.trades if t.get('pnl', 0) < 0]

            avg_win = np.mean(profits) if profits else 0
            avg_loss = abs(np.mean(losses)) if losses else 0
            profit_factor = sum(profits) / abs(sum(losses)) if losses else 0
        else:
            win_rate = 0
            avg_win = 0
            avg_loss = 0
            profit_factor = 0

        # Sharpe ratio (annualized)
        if len(returns) > 0 and returns.std() > 0:
            sharpe = (returns.mean() / returns.std()) * np.sqrt(252)
        else:
            sharpe = 0

        # Max drawdown
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min() * 100

        return {
            'total_return_pct': total_return,
            'sharpe_ratio': sharpe,
            'max_drawdown_pct': max_drawdown,
            'total_trades': total_trades,
            'win_rate_pct': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'final_equity': df['equity'].iloc[-1]
        }

    def record_equity(self, timestamp: datetime, prices: Dict[str, float]):
        """
        Record equity at timestamp

        Args:
            timestamp: Current timestamp
            prices: Dictionary of current prices
        """
        equity = self.get_total_value(prices)
        self.equity_curve.append({
            'timestamp': timestamp,
            'equity': equity,
            'cash': self.cash,
            'positions': len(self.positions)
        })

    def reset(self):
        """Reset portfolio to initial state"""
        self.cash = self.initial_capital
        self.positions = {}
        self.closed_positions = []
        self.trades = []
        self.equity_curve = []

    def __repr__(self) -> str:
        return (f"Portfolio(cash={self.cash:.2f}, positions={len(self.positions)}, "
                f"closed={len(self.closed_positions)})")
