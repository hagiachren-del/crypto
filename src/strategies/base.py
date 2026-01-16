"""Base strategy class"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
import pandas as pd
from src.indicators import Indicators


class Strategy(ABC):
    """Abstract base class for trading strategies"""

    def __init__(self, params: Dict[str, Any]):
        """
        Initialize strategy

        Args:
            params: Strategy parameters
        """
        self.params = params
        self.indicators = Indicators()
        self.data: Optional[pd.DataFrame] = None
        self.position = None  # 'long', 'short', or None
        self.entry_price = 0.0

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals

        Args:
            data: OHLCV DataFrame with columns [open, high, low, close, volume]

        Returns:
            Series with signals: 1 (buy), -1 (sell), 0 (hold)
        """
        pass

    def on_data(self, data: pd.DataFrame) -> Optional[str]:
        """
        Process new data and generate signal

        Args:
            data: OHLCV DataFrame

        Returns:
            Signal: 'buy', 'sell', or None
        """
        self.data = data
        signals = self.generate_signals(data)

        if len(signals) == 0:
            return None

        last_signal = signals.iloc[-1]

        if last_signal == 1:
            return 'buy'
        elif last_signal == -1:
            return 'sell'
        else:
            return None

    def on_candle(self, candle: Dict) -> Optional[str]:
        """
        Process single candle (for real-time trading)

        Args:
            candle: Dictionary with OHLCV data

        Returns:
            Signal: 'buy', 'sell', or None
        """
        # Convert candle to DataFrame row
        df_row = pd.DataFrame([candle])

        if self.data is None:
            self.data = df_row
        else:
            self.data = pd.concat([self.data, df_row], ignore_index=True)

        return self.on_data(self.data)

    def get_position_size(self, capital: float, price: float) -> float:
        """
        Calculate position size

        Args:
            capital: Available capital
            price: Current price

        Returns:
            Position size
        """
        # Default: use all available capital
        return capital / price

    def should_exit(self, current_price: float) -> bool:
        """
        Check if position should be exited

        Args:
            current_price: Current market price

        Returns:
            True if should exit
        """
        # Default: no exit logic
        return False

    def reset(self):
        """Reset strategy state"""
        self.data = None
        self.position = None
        self.entry_price = 0.0

    def get_name(self) -> str:
        """Get strategy name"""
        return self.__class__.__name__

    def __repr__(self) -> str:
        return f"{self.get_name()}(params={self.params})"
