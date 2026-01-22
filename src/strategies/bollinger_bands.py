"""Bollinger Bands Mean Reversion Strategy"""

import pandas as pd
from .base import Strategy


class BollingerBandsStrategy(Strategy):
    """
    Bollinger Bands Mean Reversion Strategy

    Buys when price touches lower band
    Sells when price touches upper band
    """

    def __init__(self, params: dict):
        """
        Initialize Bollinger Bands strategy

        Args:
            params: Dictionary with 'period' and 'std_dev'
        """
        super().__init__(params)
        self.period = params.get('period', 20)
        self.std_dev = params.get('std_dev', 2.0)

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate trading signals based on Bollinger Bands"""
        close = data['close']

        # Calculate Bollinger Bands
        upper, middle, lower = self.indicators.bollinger_bands(
            close, self.period, self.std_dev
        )

        # Generate signals
        signals = pd.Series(0, index=data.index)

        # Buy when price crosses below lower band
        signals[(close < lower) & (close.shift(1) >= lower.shift(1))] = 1

        # Sell when price crosses above upper band
        signals[(close > upper) & (close.shift(1) <= upper.shift(1))] = -1

        return signals
