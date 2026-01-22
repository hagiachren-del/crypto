"""Simple Moving Average Crossover Strategy"""

import pandas as pd
from .base import Strategy


class SMACrossStrategy(Strategy):
    """
    Simple Moving Average Crossover Strategy

    Generates buy signal when fast SMA crosses above slow SMA
    Generates sell signal when fast SMA crosses below slow SMA
    """

    def __init__(self, params: dict):
        """
        Initialize SMA Cross strategy

        Args:
            params: Dictionary with 'fast' and 'slow' SMA periods
        """
        super().__init__(params)
        self.fast_period = params.get('fast', 20)
        self.slow_period = params.get('slow', 50)

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate trading signals based on SMA crossover"""
        close = data['close']

        # Calculate SMAs
        sma_fast = self.indicators.sma(close, self.fast_period)
        sma_slow = self.indicators.sma(close, self.slow_period)

        # Generate signals
        signals = pd.Series(0, index=data.index)

        # Buy when fast crosses above slow
        signals[(sma_fast > sma_slow) & (sma_fast.shift(1) <= sma_slow.shift(1))] = 1

        # Sell when fast crosses below slow
        signals[(sma_fast < sma_slow) & (sma_fast.shift(1) >= sma_slow.shift(1))] = -1

        return signals
