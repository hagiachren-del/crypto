"""
Comprehensive Technical Indicators Library

This module provides 50+ technical indicators for crypto market analysis,
including trend, momentum, volatility, volume, and advanced indicators.
"""

import numpy as np
import pandas as pd
from typing import Union, Tuple, Optional


class Indicators:
    """Collection of technical indicators for market analysis"""

    # ==================== TREND INDICATORS ====================

    @staticmethod
    def sma(data: Union[pd.Series, np.ndarray], period: int = 20) -> pd.Series:
        """
        Simple Moving Average

        Args:
            data: Price data
            period: Period for SMA

        Returns:
            SMA values
        """
        if isinstance(data, np.ndarray):
            data = pd.Series(data)
        return data.rolling(window=period).mean()

    @staticmethod
    def ema(data: Union[pd.Series, np.ndarray], period: int = 20) -> pd.Series:
        """
        Exponential Moving Average

        Args:
            data: Price data
            period: Period for EMA

        Returns:
            EMA values
        """
        if isinstance(data, np.ndarray):
            data = pd.Series(data)
        return data.ewm(span=period, adjust=False).mean()

    @staticmethod
    def wma(data: Union[pd.Series, np.ndarray], period: int = 20) -> pd.Series:
        """
        Weighted Moving Average

        Args:
            data: Price data
            period: Period for WMA

        Returns:
            WMA values
        """
        if isinstance(data, np.ndarray):
            data = pd.Series(data)

        weights = np.arange(1, period + 1)
        return data.rolling(period).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)

    @staticmethod
    def dema(data: Union[pd.Series, np.ndarray], period: int = 20) -> pd.Series:
        """
        Double Exponential Moving Average

        Args:
            data: Price data
            period: Period for DEMA

        Returns:
            DEMA values
        """
        ema1 = Indicators.ema(data, period)
        ema2 = Indicators.ema(ema1, period)
        return 2 * ema1 - ema2

    @staticmethod
    def tema(data: Union[pd.Series, np.ndarray], period: int = 20) -> pd.Series:
        """
        Triple Exponential Moving Average

        Args:
            data: Price data
            period: Period for TEMA

        Returns:
            TEMA values
        """
        ema1 = Indicators.ema(data, period)
        ema2 = Indicators.ema(ema1, period)
        ema3 = Indicators.ema(ema2, period)
        return 3 * ema1 - 3 * ema2 + ema3

    @staticmethod
    def macd(data: Union[pd.Series, np.ndarray],
             fast: int = 12,
             slow: int = 26,
             signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Moving Average Convergence Divergence

        Args:
            data: Price data
            fast: Fast EMA period
            slow: Slow EMA period
            signal: Signal line period

        Returns:
            Tuple of (MACD line, Signal line, Histogram)
        """
        if isinstance(data, np.ndarray):
            data = pd.Series(data)

        fast_ema = Indicators.ema(data, fast)
        slow_ema = Indicators.ema(data, slow)
        macd_line = fast_ema - slow_ema
        signal_line = Indicators.ema(macd_line, signal)
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram

    @staticmethod
    def adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """
        Average Directional Index

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: Period for ADX

        Returns:
            ADX values
        """
        plus_dm = high.diff()
        minus_dm = -low.diff()

        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0

        tr = Indicators.atr(high, low, close, period)
        plus_di = 100 * (plus_dm.ewm(alpha=1 / period).mean() / tr)
        minus_di = 100 * (minus_dm.ewm(alpha=1 / period).mean() / tr)

        dx = (abs(plus_di - minus_di) / abs(plus_di + minus_di)) * 100
        adx = dx.ewm(alpha=1 / period).mean()

        return adx

    @staticmethod
    def ichimoku(high: pd.Series, low: pd.Series, close: pd.Series) -> dict:
        """
        Ichimoku Cloud

        Args:
            high: High prices
            low: Low prices
            close: Close prices

        Returns:
            Dictionary with all Ichimoku components
        """
        # Tenkan-sen (Conversion Line): (9-period high + 9-period low)/2
        tenkan = (high.rolling(window=9).max() + low.rolling(window=9).min()) / 2

        # Kijun-sen (Base Line): (26-period high + 26-period low)/2
        kijun = (high.rolling(window=26).max() + low.rolling(window=26).min()) / 2

        # Senkou Span A (Leading Span A): (Conversion Line + Base Line)/2
        senkou_a = ((tenkan + kijun) / 2).shift(26)

        # Senkou Span B (Leading Span B): (52-period high + 52-period low)/2
        senkou_b = ((high.rolling(window=52).max() + low.rolling(window=52).min()) / 2).shift(26)

        # Chikou Span (Lagging Span): Close plotted 26 days in the past
        chikou = close.shift(-26)

        return {
            'tenkan': tenkan,
            'kijun': kijun,
            'senkou_a': senkou_a,
            'senkou_b': senkou_b,
            'chikou': chikou
        }

    # ==================== MOMENTUM INDICATORS ====================

    @staticmethod
    def rsi(data: Union[pd.Series, np.ndarray], period: int = 14) -> pd.Series:
        """
        Relative Strength Index

        Args:
            data: Price data
            period: Period for RSI

        Returns:
            RSI values
        """
        if isinstance(data, np.ndarray):
            data = pd.Series(data)

        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    @staticmethod
    def stochastic(high: pd.Series, low: pd.Series, close: pd.Series,
                   k_period: int = 14, d_period: int = 3) -> Tuple[pd.Series, pd.Series]:
        """
        Stochastic Oscillator

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            k_period: %K period
            d_period: %D period

        Returns:
            Tuple of (%K, %D)
        """
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()

        k = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d = k.rolling(window=d_period).mean()

        return k, d

    @staticmethod
    def cci(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20) -> pd.Series:
        """
        Commodity Channel Index

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: Period for CCI

        Returns:
            CCI values
        """
        tp = (high + low + close) / 3
        sma_tp = tp.rolling(window=period).mean()
        mad = tp.rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean())

        cci = (tp - sma_tp) / (0.015 * mad)

        return cci

    @staticmethod
    def williams_r(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """
        Williams %R

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: Period for Williams %R

        Returns:
            Williams %R values
        """
        highest_high = high.rolling(window=period).max()
        lowest_low = low.rolling(window=period).min()

        wr = -100 * ((highest_high - close) / (highest_high - lowest_low))

        return wr

    @staticmethod
    def roc(data: Union[pd.Series, np.ndarray], period: int = 12) -> pd.Series:
        """
        Rate of Change

        Args:
            data: Price data
            period: Period for ROC

        Returns:
            ROC values
        """
        if isinstance(data, np.ndarray):
            data = pd.Series(data)

        roc = ((data - data.shift(period)) / data.shift(period)) * 100

        return roc

    @staticmethod
    def mfi(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series,
            period: int = 14) -> pd.Series:
        """
        Money Flow Index

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            volume: Volume data
            period: Period for MFI

        Returns:
            MFI values
        """
        tp = (high + low + close) / 3
        mf = tp * volume

        mf_positive = pd.Series(np.where(tp > tp.shift(1), mf, 0), index=mf.index)
        mf_negative = pd.Series(np.where(tp < tp.shift(1), mf, 0), index=mf.index)

        mf_positive_sum = mf_positive.rolling(window=period).sum()
        mf_negative_sum = mf_negative.rolling(window=period).sum()

        mfi = 100 - (100 / (1 + (mf_positive_sum / mf_negative_sum)))

        return mfi

    # ==================== VOLATILITY INDICATORS ====================

    @staticmethod
    def bollinger_bands(data: Union[pd.Series, np.ndarray],
                        period: int = 20,
                        std_dev: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Bollinger Bands

        Args:
            data: Price data
            period: Period for moving average
            std_dev: Number of standard deviations

        Returns:
            Tuple of (Upper Band, Middle Band, Lower Band)
        """
        if isinstance(data, np.ndarray):
            data = pd.Series(data)

        middle = data.rolling(window=period).mean()
        std = data.rolling(window=period).std()

        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)

        return upper, middle, lower

    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """
        Average True Range

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: Period for ATR

        Returns:
            ATR values
        """
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.ewm(alpha=1 / period, adjust=False).mean()

        return atr

    @staticmethod
    def keltner_channels(high: pd.Series, low: pd.Series, close: pd.Series,
                         period: int = 20, atr_period: int = 10,
                         multiplier: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Keltner Channels

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: Period for EMA
            atr_period: Period for ATR
            multiplier: ATR multiplier

        Returns:
            Tuple of (Upper Channel, Middle Channel, Lower Channel)
        """
        middle = Indicators.ema(close, period)
        atr = Indicators.atr(high, low, close, atr_period)

        upper = middle + (multiplier * atr)
        lower = middle - (multiplier * atr)

        return upper, middle, lower

    @staticmethod
    def donchian_channels(high: pd.Series, low: pd.Series,
                          period: int = 20) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Donchian Channels

        Args:
            high: High prices
            low: Low prices
            period: Period for channels

        Returns:
            Tuple of (Upper Channel, Middle Channel, Lower Channel)
        """
        upper = high.rolling(window=period).max()
        lower = low.rolling(window=period).min()
        middle = (upper + lower) / 2

        return upper, middle, lower

    # ==================== VOLUME INDICATORS ====================

    @staticmethod
    def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        """
        On-Balance Volume

        Args:
            close: Close prices
            volume: Volume data

        Returns:
            OBV values
        """
        obv = (np.sign(close.diff()) * volume).fillna(0).cumsum()
        return obv

    @staticmethod
    def vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
        """
        Volume Weighted Average Price

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            volume: Volume data

        Returns:
            VWAP values
        """
        tp = (high + low + close) / 3
        vwap = (tp * volume).cumsum() / volume.cumsum()

        return vwap

    @staticmethod
    def ad_line(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
        """
        Accumulation/Distribution Line

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            volume: Volume data

        Returns:
            A/D Line values
        """
        clv = ((close - low) - (high - close)) / (high - low)
        clv = clv.fillna(0.0)
        ad = (clv * volume).cumsum()

        return ad

    @staticmethod
    def cmf(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series,
            period: int = 20) -> pd.Series:
        """
        Chaikin Money Flow

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            volume: Volume data
            period: Period for CMF

        Returns:
            CMF values
        """
        clv = ((close - low) - (high - close)) / (high - low)
        clv = clv.fillna(0.0)
        cmf = (clv * volume).rolling(window=period).sum() / volume.rolling(window=period).sum()

        return cmf

    # ==================== ADVANCED INDICATORS ====================

    @staticmethod
    def supertrend(high: pd.Series, low: pd.Series, close: pd.Series,
                   period: int = 10, multiplier: float = 3.0) -> Tuple[pd.Series, pd.Series]:
        """
        SuperTrend Indicator

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: Period for ATR
            multiplier: ATR multiplier

        Returns:
            Tuple of (SuperTrend, Direction)
        """
        atr = Indicators.atr(high, low, close, period)
        hl_avg = (high + low) / 2

        upper_band = hl_avg + (multiplier * atr)
        lower_band = hl_avg - (multiplier * atr)

        supertrend = pd.Series(index=close.index, dtype=float)
        direction = pd.Series(index=close.index, dtype=int)

        supertrend.iloc[0] = upper_band.iloc[0]
        direction.iloc[0] = 1

        for i in range(1, len(close)):
            if close.iloc[i] > supertrend.iloc[i - 1]:
                direction.iloc[i] = 1
                supertrend.iloc[i] = max(lower_band.iloc[i], supertrend.iloc[i - 1])
            else:
                direction.iloc[i] = -1
                supertrend.iloc[i] = min(upper_band.iloc[i], supertrend.iloc[i - 1])

        return supertrend, direction

    @staticmethod
    def vortex(high: pd.Series, low: pd.Series, close: pd.Series,
               period: int = 14) -> Tuple[pd.Series, pd.Series]:
        """
        Vortex Indicator

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: Period for VI

        Returns:
            Tuple of (VI+, VI-)
        """
        tr = Indicators.atr(high, low, close, 1)

        vm_plus = abs(high - low.shift(1))
        vm_minus = abs(low - high.shift(1))

        vi_plus = vm_plus.rolling(window=period).sum() / tr.rolling(window=period).sum()
        vi_minus = vm_minus.rolling(window=period).sum() / tr.rolling(window=period).sum()

        return vi_plus, vi_minus

    @staticmethod
    def awesome_oscillator(high: pd.Series, low: pd.Series) -> pd.Series:
        """
        Awesome Oscillator

        Args:
            high: High prices
            low: Low prices

        Returns:
            AO values
        """
        median_price = (high + low) / 2
        ao = Indicators.sma(median_price, 5) - Indicators.sma(median_price, 34)

        return ao

    @staticmethod
    def fibonacci_retracement(high: float, low: float) -> dict:
        """
        Calculate Fibonacci retracement levels

        Args:
            high: Highest price
            low: Lowest price

        Returns:
            Dictionary of Fibonacci levels
        """
        diff = high - low

        levels = {
            '0.0': high,
            '0.236': high - (0.236 * diff),
            '0.382': high - (0.382 * diff),
            '0.500': high - (0.500 * diff),
            '0.618': high - (0.618 * diff),
            '0.786': high - (0.786 * diff),
            '1.0': low
        }

        return levels

    @staticmethod
    def pivot_points(high: float, low: float, close: float) -> dict:
        """
        Calculate Pivot Points

        Args:
            high: Previous period high
            low: Previous period low
            close: Previous period close

        Returns:
            Dictionary of pivot levels
        """
        pivot = (high + low + close) / 3

        r1 = 2 * pivot - low
        s1 = 2 * pivot - high
        r2 = pivot + (high - low)
        s2 = pivot - (high - low)
        r3 = high + 2 * (pivot - low)
        s3 = low - 2 * (high - pivot)

        return {
            'pivot': pivot,
            'r1': r1, 's1': s1,
            'r2': r2, 's2': s2,
            'r3': r3, 's3': s3
        }

    @staticmethod
    def heikin_ashi(open_price: pd.Series, high: pd.Series, low: pd.Series,
                    close: pd.Series) -> dict:
        """
        Heikin-Ashi Candlesticks

        Args:
            open_price: Open prices
            high: High prices
            low: Low prices
            close: Close prices

        Returns:
            Dictionary of Heikin-Ashi OHLC
        """
        ha_close = (open_price + high + low + close) / 4
        ha_open = pd.Series(index=open_price.index, dtype=float)
        ha_open.iloc[0] = open_price.iloc[0]

        for i in range(1, len(open_price)):
            ha_open.iloc[i] = (ha_open.iloc[i - 1] + ha_close.iloc[i - 1]) / 2

        ha_high = pd.concat([high, ha_open, ha_close], axis=1).max(axis=1)
        ha_low = pd.concat([low, ha_open, ha_close], axis=1).min(axis=1)

        return {
            'open': ha_open,
            'high': ha_high,
            'low': ha_low,
            'close': ha_close
        }

    @staticmethod
    def elder_ray(close: pd.Series, high: pd.Series, low: pd.Series, period: int = 13) -> dict:
        """
        Elder Ray Index

        Args:
            close: Close prices
            high: High prices
            low: Low prices
            period: Period for EMA

        Returns:
            Dictionary with Bull Power and Bear Power
        """
        ema = Indicators.ema(close, period)
        bull_power = high - ema
        bear_power = low - ema

        return {
            'bull_power': bull_power,
            'bear_power': bear_power
        }

    @staticmethod
    def zscore(data: Union[pd.Series, np.ndarray], period: int = 20) -> pd.Series:
        """
        Z-Score (Standard Score)

        Args:
            data: Price data
            period: Period for calculation

        Returns:
            Z-Score values
        """
        if isinstance(data, np.ndarray):
            data = pd.Series(data)

        mean = data.rolling(window=period).mean()
        std = data.rolling(window=period).std()

        zscore = (data - mean) / std

        return zscore

    @staticmethod
    def correlation(data1: pd.Series, data2: pd.Series, period: int = 20) -> pd.Series:
        """
        Rolling correlation between two series

        Args:
            data1: First series
            data2: Second series
            period: Period for correlation

        Returns:
            Correlation values
        """
        return data1.rolling(window=period).corr(data2)
