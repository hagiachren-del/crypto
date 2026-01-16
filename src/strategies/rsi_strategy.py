"""RSI-based Trading Strategy"""

import pandas as pd
from .base import Strategy


class RSIStrategy(Strategy):
    """
    RSI Mean Reversion Strategy

    Buys when RSI is oversold (< 30)
    Sells when RSI is overbought (> 70)
    """

    def __init__(self, params: dict):
        """
        Initialize RSI strategy

        Args:
            params: Dictionary with 'period', 'oversold', and 'overbought' levels
        """
        super().__init__(params)
        self.period = params.get('period', 14)
        self.oversold = params.get('oversold', 30)
        self.overbought = params.get('overbought', 70)

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate trading signals based on RSI"""
        close = data['close']

        # Calculate RSI
        rsi = self.indicators.rsi(close, self.period)

        # Generate signals
        signals = pd.Series(0, index=data.index)

        # Buy when RSI crosses above oversold level
        signals[(rsi > self.oversold) & (rsi.shift(1) <= self.oversold)] = 1

        # Sell when RSI crosses below overbought level
        signals[(rsi < self.overbought) & (rsi.shift(1) >= self.overbought)] = -1

        return signals
