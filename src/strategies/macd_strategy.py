"""MACD Trading Strategy"""

import pandas as pd
from .base import Strategy


class MACDStrategy(Strategy):
    """
    MACD Strategy

    Buys when MACD line crosses above signal line
    Sells when MACD line crosses below signal line
    """

    def __init__(self, params: dict):
        """
        Initialize MACD strategy

        Args:
            params: Dictionary with 'fast', 'slow', and 'signal' periods
        """
        super().__init__(params)
        self.fast_period = params.get('fast', 12)
        self.slow_period = params.get('slow', 26)
        self.signal_period = params.get('signal', 9)

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate trading signals based on MACD"""
        close = data['close']

        # Calculate MACD
        macd_line, signal_line, histogram = self.indicators.macd(
            close, self.fast_period, self.slow_period, self.signal_period
        )

        # Generate signals
        signals = pd.Series(0, index=data.index)

        # Buy when MACD crosses above signal
        signals[(macd_line > signal_line) & (macd_line.shift(1) <= signal_line.shift(1))] = 1

        # Sell when MACD crosses below signal
        signals[(macd_line < signal_line) & (macd_line.shift(1) >= signal_line.shift(1))] = -1

        return signals
