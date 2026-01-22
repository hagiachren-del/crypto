"""Multi-Indicator Strategy combining multiple technical signals"""

import pandas as pd
import numpy as np
from .base import Strategy


class MultiIndicatorStrategy(Strategy):
    """
    Advanced Multi-Indicator Strategy

    Combines RSI, MACD, and Bollinger Bands for stronger signals
    Requires multiple confirmations before generating signals
    """

    def __init__(self, params: dict):
        """
        Initialize Multi-Indicator strategy

        Args:
            params: Dictionary with various indicator parameters
        """
        super().__init__(params)

        # RSI params
        self.rsi_period = params.get('rsi_period', 14)
        self.rsi_oversold = params.get('rsi_oversold', 30)
        self.rsi_overbought = params.get('rsi_overbought', 70)

        # MACD params
        self.macd_fast = params.get('macd_fast', 12)
        self.macd_slow = params.get('macd_slow', 26)
        self.macd_signal = params.get('macd_signal', 9)

        # Bollinger Bands params
        self.bb_period = params.get('bb_period', 20)
        self.bb_std = params.get('bb_std', 2.0)

        # Signal threshold (how many indicators must agree)
        self.threshold = params.get('threshold', 2)

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate trading signals based on multiple indicators"""
        close = data['close']

        # Calculate all indicators
        rsi = self.indicators.rsi(close, self.rsi_period)
        macd_line, signal_line, _ = self.indicators.macd(
            close, self.macd_fast, self.macd_slow, self.macd_signal
        )
        upper, middle, lower = self.indicators.bollinger_bands(
            close, self.bb_period, self.bb_std
        )

        # Individual indicator signals
        rsi_signal = pd.Series(0, index=data.index)
        rsi_signal[rsi < self.rsi_oversold] = 1
        rsi_signal[rsi > self.rsi_overbought] = -1

        macd_signal = pd.Series(0, index=data.index)
        macd_signal[macd_line > signal_line] = 1
        macd_signal[macd_line < signal_line] = -1

        bb_signal = pd.Series(0, index=data.index)
        bb_signal[close < lower] = 1
        bb_signal[close > upper] = -1

        # Combine signals - require multiple confirmations
        buy_score = (rsi_signal == 1).astype(int) + \
                    (macd_signal == 1).astype(int) + \
                    (bb_signal == 1).astype(int)

        sell_score = (rsi_signal == -1).astype(int) + \
                     (macd_signal == -1).astype(int) + \
                     (bb_signal == -1).astype(int)

        # Generate final signals
        signals = pd.Series(0, index=data.index)
        signals[buy_score >= self.threshold] = 1
        signals[sell_score >= self.threshold] = -1

        return signals
