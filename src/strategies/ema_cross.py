"""Exponential Moving Average Crossover Strategy"""

import pandas as pd
from .base import Strategy


class EMACrossStrategy(Strategy):
    """
    Exponential Moving Average Crossover Strategy

    Similar to SMA but uses EMA for more responsive signals
    """

    def __init__(self, params: dict):
        """
        Initialize EMA Cross strategy

        Args:
            params: Dictionary with 'fast' and 'slow' EMA periods
        """
        super().__init__(params)
        self.fast_period = params.get('fast', 12)
        self.slow_period = params.get('slow', 26)

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate trading signals based on EMA crossover"""
        close = data['close']

        # Calculate EMAs
        ema_fast = self.indicators.ema(close, self.fast_period)
        ema_slow = self.indicators.ema(close, self.slow_period)

        # Generate signals
        signals = pd.Series(0, index=data.index)

        # Buy when fast crosses above slow
        signals[(ema_fast > ema_slow) & (ema_fast.shift(1) <= ema_slow.shift(1))] = 1

        # Sell when fast crosses below slow
        signals[(ema_fast < ema_slow) & (ema_fast.shift(1) >= ema_slow.shift(1))] = -1

        return signals
