"""Trading strategies"""

from .base import Strategy
from .sma_cross import SMACrossStrategy
from .ema_cross import EMACrossStrategy
from .rsi_strategy import RSIStrategy
from .macd_strategy import MACDStrategy
from .bollinger_bands import BollingerBandsStrategy
from .multi_indicator import MultiIndicatorStrategy

__all__ = [
    'Strategy',
    'SMACrossStrategy',
    'EMACrossStrategy',
    'RSIStrategy',
    'MACDStrategy',
    'BollingerBandsStrategy',
    'MultiIndicatorStrategy'
]
