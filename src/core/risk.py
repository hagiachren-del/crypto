"""Comprehensive risk management system"""

from typing import Dict, Optional
from datetime import datetime, timedelta
import numpy as np


class RiskManager:
    """Advanced risk management for trading"""

    def __init__(self, config: Dict):
        """
        Initialize risk manager

        Args:
            config: Risk configuration dictionary
        """
        # Position sizing
        self.max_position_pct = config.get('max_position_pct', 0.10)
        self.max_total_exposure_pct = config.get('max_total_exposure_pct', 0.50)

        # Stop loss / Take profit
        self.use_stop_loss = config.get('use_stop_loss', True)
        self.stop_loss_pct = config.get('stop_loss_pct', 0.02)
        self.use_take_profit = config.get('use_take_profit', False)
        self.take_profit_pct = config.get('take_profit_pct', 0.05)
        self.trailing_stop = config.get('trailing_stop', False)
        self.trailing_stop_pct = config.get('trailing_stop_pct', 0.03)

        # Daily limits
        self.max_daily_loss_pct = config.get('max_daily_loss_pct', 0.05)
        self.max_daily_trades = config.get('max_daily_trades', 50)

        # Leverage
        self.max_leverage = config.get('max_leverage', 1.0)

        # Risk metrics
        self.max_drawdown_pct = config.get('max_drawdown_pct', 0.20)
        self.risk_per_trade_pct = config.get('risk_per_trade_pct', 0.01)

        # Tracking
        self.daily_trades = 0
        self.daily_pnl = 0.0
        self.last_reset = datetime.now()
        self.peak_equity = 0.0
        self.stop_prices: Dict[str, float] = {}

    def reset_daily_counters(self):
        """Reset daily counters if new day"""
        now = datetime.now()
        if now.date() > self.last_reset.date():
            self.daily_trades = 0
            self.daily_pnl = 0.0
            self.last_reset = now

    def can_open_position(self, symbol: str, quantity: float, price: float,
                          portfolio_value: float, current_positions: int) -> tuple[bool, str]:
        """
        Check if position can be opened

        Args:
            symbol: Trading pair symbol
            quantity: Position size
            price: Entry price
            portfolio_value: Current portfolio value
            current_positions: Number of current positions

        Returns:
            Tuple of (can_open, reason)
        """
        self.reset_daily_counters()

        # Check daily trade limit
        if self.daily_trades >= self.max_daily_trades:
            return False, f"Daily trade limit reached ({self.max_daily_trades})"

        # Check position size
        position_value = quantity * price
        position_pct = position_value / portfolio_value

        if position_pct > self.max_position_pct:
            return False, f"Position size ({position_pct:.2%}) exceeds max ({self.max_position_pct:.2%})"

        # Check daily loss limit
        if self.daily_pnl < 0:
            daily_loss_pct = abs(self.daily_pnl / portfolio_value)
            if daily_loss_pct >= self.max_daily_loss_pct:
                return False, f"Daily loss limit reached ({daily_loss_pct:.2%})"

        return True, "OK"

    def calculate_position_size(self, portfolio_value: float, price: float,
                                 volatility: Optional[float] = None) -> float:
        """
        Calculate optimal position size

        Args:
            portfolio_value: Current portfolio value
            price: Entry price
            volatility: Asset volatility (optional, for Kelly criterion)

        Returns:
            Position size (quantity)
        """
        # Basic position sizing based on max position percentage
        max_position_value = portfolio_value * self.max_position_pct
        quantity = max_position_value / price

        # Adjust for risk per trade
        if self.use_stop_loss:
            risk_amount = portfolio_value * self.risk_per_trade_pct
            stop_distance = price * self.stop_loss_pct
            risk_based_quantity = risk_amount / stop_distance
            quantity = min(quantity, risk_based_quantity)

        # Adjust for volatility (if provided)
        if volatility is not None and volatility > 0:
            # Reduce position size in high volatility
            volatility_adjustment = 1.0 / (1.0 + volatility)
            quantity *= volatility_adjustment

        return quantity

    def set_stop_loss(self, symbol: str, entry_price: float, side: str) -> float:
        """
        Calculate and set stop loss price

        Args:
            symbol: Trading pair symbol
            entry_price: Entry price
            side: Position side ('long' or 'short')

        Returns:
            Stop loss price
        """
        if not self.use_stop_loss:
            return 0.0

        if side == 'long':
            stop_price = entry_price * (1 - self.stop_loss_pct)
        else:  # short
            stop_price = entry_price * (1 + self.stop_loss_pct)

        self.stop_prices[symbol] = stop_price
        return stop_price

    def set_take_profit(self, entry_price: float, side: str) -> float:
        """
        Calculate take profit price

        Args:
            entry_price: Entry price
            side: Position side ('long' or 'short')

        Returns:
            Take profit price
        """
        if not self.use_take_profit:
            return 0.0

        if side == 'long':
            return entry_price * (1 + self.take_profit_pct)
        else:  # short
            return entry_price * (1 - self.take_profit_pct)

    def update_trailing_stop(self, symbol: str, current_price: float,
                             side: str, highest_price: float = None,
                             lowest_price: float = None) -> Optional[float]:
        """
        Update trailing stop loss

        Args:
            symbol: Trading pair symbol
            current_price: Current market price
            side: Position side ('long' or 'short')
            highest_price: Highest price since entry (for long)
            lowest_price: Lowest price since entry (for short)

        Returns:
            New stop price or None
        """
        if not self.trailing_stop or symbol not in self.stop_prices:
            return None

        current_stop = self.stop_prices[symbol]

        if side == 'long' and highest_price:
            new_stop = highest_price * (1 - self.trailing_stop_pct)
            if new_stop > current_stop:
                self.stop_prices[symbol] = new_stop
                return new_stop

        elif side == 'short' and lowest_price:
            new_stop = lowest_price * (1 + self.trailing_stop_pct)
            if new_stop < current_stop:
                self.stop_prices[symbol] = new_stop
                return new_stop

        return None

    def should_close_position(self, symbol: str, current_price: float,
                              side: str, entry_price: float) -> tuple[bool, str]:
        """
        Check if position should be closed based on risk rules

        Args:
            symbol: Trading pair symbol
            current_price: Current market price
            side: Position side ('long' or 'short')
            entry_price: Entry price

        Returns:
            Tuple of (should_close, reason)
        """
        # Check stop loss
        if symbol in self.stop_prices:
            stop_price = self.stop_prices[symbol]

            if side == 'long' and current_price <= stop_price:
                return True, "Stop loss triggered"
            elif side == 'short' and current_price >= stop_price:
                return True, "Stop loss triggered"

        # Check take profit
        if self.use_take_profit:
            take_profit_price = self.set_take_profit(entry_price, side)

            if side == 'long' and current_price >= take_profit_price:
                return True, "Take profit triggered"
            elif side == 'short' and current_price <= take_profit_price:
                return True, "Take profit triggered"

        return False, ""

    def check_drawdown(self, current_equity: float, peak_equity: float) -> tuple[bool, float]:
        """
        Check if drawdown limit exceeded

        Args:
            current_equity: Current equity
            peak_equity: Peak equity

        Returns:
            Tuple of (limit_exceeded, drawdown_pct)
        """
        if peak_equity == 0:
            return False, 0.0

        drawdown_pct = (peak_equity - current_equity) / peak_equity

        if drawdown_pct >= self.max_drawdown_pct:
            return True, drawdown_pct

        return False, drawdown_pct

    def update_peak_equity(self, current_equity: float):
        """Update peak equity"""
        if current_equity > self.peak_equity:
            self.peak_equity = current_equity

    def record_trade(self, pnl: float):
        """
        Record trade for daily tracking

        Args:
            pnl: Trade PnL
        """
        self.reset_daily_counters()
        self.daily_trades += 1
        self.daily_pnl += pnl

    def get_risk_metrics(self) -> Dict:
        """
        Get current risk metrics

        Returns:
            Dictionary of risk metrics
        """
        return {
            'daily_trades': self.daily_trades,
            'daily_pnl': self.daily_pnl,
            'max_daily_trades': self.max_daily_trades,
            'max_daily_loss_pct': self.max_daily_loss_pct,
            'max_position_pct': self.max_position_pct,
            'stop_loss_pct': self.stop_loss_pct,
            'active_stops': len(self.stop_prices)
        }

    def calculate_risk_reward_ratio(self, entry_price: float, stop_price: float,
                                     target_price: float) -> float:
        """
        Calculate risk-reward ratio

        Args:
            entry_price: Entry price
            stop_price: Stop loss price
            target_price: Target price

        Returns:
            Risk-reward ratio
        """
        risk = abs(entry_price - stop_price)
        reward = abs(target_price - entry_price)

        if risk == 0:
            return 0.0

        return reward / risk

    def calculate_sharpe_ratio(self, returns: np.ndarray, risk_free_rate: float = 0.0) -> float:
        """
        Calculate Sharpe ratio

        Args:
            returns: Array of returns
            risk_free_rate: Risk-free rate

        Returns:
            Sharpe ratio
        """
        if len(returns) == 0 or np.std(returns) == 0:
            return 0.0

        excess_returns = returns - risk_free_rate
        return np.mean(excess_returns) / np.std(returns) * np.sqrt(252)

    def calculate_sortino_ratio(self, returns: np.ndarray, risk_free_rate: float = 0.0) -> float:
        """
        Calculate Sortino ratio (downside deviation)

        Args:
            returns: Array of returns
            risk_free_rate: Risk-free rate

        Returns:
            Sortino ratio
        """
        if len(returns) == 0:
            return 0.0

        excess_returns = returns - risk_free_rate
        downside_returns = returns[returns < 0]

        if len(downside_returns) == 0 or np.std(downside_returns) == 0:
            return 0.0

        return np.mean(excess_returns) / np.std(downside_returns) * np.sqrt(252)

    def calculate_var(self, returns: np.ndarray, confidence: float = 0.95) -> float:
        """
        Calculate Value at Risk (VaR)

        Args:
            returns: Array of returns
            confidence: Confidence level

        Returns:
            VaR value
        """
        if len(returns) == 0:
            return 0.0

        return np.percentile(returns, (1 - confidence) * 100)

    def calculate_cvar(self, returns: np.ndarray, confidence: float = 0.95) -> float:
        """
        Calculate Conditional Value at Risk (CVaR)

        Args:
            returns: Array of returns
            confidence: Confidence level

        Returns:
            CVaR value
        """
        if len(returns) == 0:
            return 0.0

        var = self.calculate_var(returns, confidence)
        return returns[returns <= var].mean()

    def __repr__(self) -> str:
        return (f"RiskManager(max_position={self.max_position_pct:.1%}, "
                f"stop_loss={self.stop_loss_pct:.1%}, "
                f"daily_trades={self.daily_trades}/{self.max_daily_trades})")
