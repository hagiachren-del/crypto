"""Base exchange adapter interface"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
import pandas as pd


class BaseExchange(ABC):
    """Abstract base class for exchange adapters"""

    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None,
                 testnet: bool = False):
        """
        Initialize exchange adapter

        Args:
            api_key: API key for authentication
            api_secret: API secret for authentication
            testnet: Whether to use testnet
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self._initialized = False

    @abstractmethod
    def connect(self) -> bool:
        """
        Connect to exchange

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Get current ticker data

        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USDT')

        Returns:
            Dictionary with ticker data
        """
        pass

    @abstractmethod
    def get_orderbook(self, symbol: str, limit: int = 20) -> Dict[str, List]:
        """
        Get order book

        Args:
            symbol: Trading pair symbol
            limit: Depth limit

        Returns:
            Dictionary with bids and asks
        """
        pass

    @abstractmethod
    def get_ohlcv(self, symbol: str, timeframe: str = '1h',
                  since: Optional[datetime] = None,
                  limit: Optional[int] = None) -> pd.DataFrame:
        """
        Get OHLCV (candlestick) data

        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe (e.g., '1m', '5m', '1h', '1d')
            since: Start time
            limit: Number of candles

        Returns:
            DataFrame with OHLCV data
        """
        pass

    @abstractmethod
    def get_balance(self) -> Dict[str, float]:
        """
        Get account balance

        Returns:
            Dictionary of currency balances
        """
        pass

    @abstractmethod
    def create_order(self, symbol: str, order_type: str, side: str,
                     amount: float, price: Optional[float] = None,
                     params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Create an order

        Args:
            symbol: Trading pair symbol
            order_type: Order type ('market', 'limit')
            side: Order side ('buy', 'sell')
            amount: Order amount
            price: Order price (for limit orders)
            params: Additional parameters

        Returns:
            Order information
        """
        pass

    @abstractmethod
    def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """
        Cancel an order

        Args:
            order_id: Order ID
            symbol: Trading pair symbol

        Returns:
            Cancellation result
        """
        pass

    @abstractmethod
    def get_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """
        Get order information

        Args:
            order_id: Order ID
            symbol: Trading pair symbol

        Returns:
            Order information
        """
        pass

    @abstractmethod
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get open orders

        Args:
            symbol: Trading pair symbol (optional, all if None)

        Returns:
            List of open orders
        """
        pass

    @abstractmethod
    def get_closed_orders(self, symbol: Optional[str] = None,
                          since: Optional[datetime] = None,
                          limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get closed orders

        Args:
            symbol: Trading pair symbol
            since: Start time
            limit: Maximum number of orders

        Returns:
            List of closed orders
        """
        pass

    @abstractmethod
    def get_trades(self, symbol: str, since: Optional[datetime] = None,
                   limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get trade history

        Args:
            symbol: Trading pair symbol
            since: Start time
            limit: Maximum number of trades

        Returns:
            List of trades
        """
        pass

    def get_markets(self) -> Dict[str, Dict]:
        """
        Get available markets

        Returns:
            Dictionary of market information
        """
        pass

    def get_fees(self, symbol: str) -> Dict[str, float]:
        """
        Get trading fees

        Args:
            symbol: Trading pair symbol

        Returns:
            Dictionary with maker and taker fees
        """
        pass
