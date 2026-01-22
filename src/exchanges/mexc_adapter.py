"""MEXC Exchange Adapter"""

import ccxt
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from .base import BaseExchange

logger = logging.getLogger(__name__)


class MEXCAdapter(BaseExchange):
    """MEXC Global exchange implementation"""

    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None,
                 testnet: bool = False):
        """
        Initialize MEXC adapter

        Args:
            api_key: MEXC API key
            api_secret: MEXC API secret
            testnet: Whether to use testnet (MEXC doesn't have official testnet)
        """
        super().__init__(api_key, api_secret, testnet)
        self.exchange = None
        self.logger = logging.getLogger(__name__)

    def connect(self) -> bool:
        """
        Connect to MEXC

        Returns:
            True if successful
        """
        try:
            self.logger.info("Connecting to MEXC exchange...")

            self.exchange = ccxt.mexc({
                'apiKey': self.api_key,
                'secret': self.api_secret,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot',  # spot or swap
                },
            })

            # Test connection
            self.exchange.load_markets()
            self._initialized = True

            self.logger.info(f"Successfully connected to MEXC - {len(self.exchange.markets)} markets available")
            return True

        except ccxt.AuthenticationError as e:
            self.logger.error(f"Authentication failed for MEXC: {e}")
            return False
        except ccxt.NetworkError as e:
            self.logger.error(f"Network error connecting to MEXC: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to connect to MEXC: {e}")
            return False

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get current ticker data"""
        if not self._initialized:
            if not self.connect():
                raise ConnectionError("Failed to connect to MEXC")

        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return {
                'symbol': symbol,
                'bid': ticker.get('bid'),
                'ask': ticker.get('ask'),
                'last': ticker.get('last'),
                'volume': ticker.get('baseVolume'),
                'timestamp': ticker.get('timestamp'),
                'high': ticker.get('high'),
                'low': ticker.get('low')
            }
        except ccxt.BadSymbol as e:
            self.logger.error(f"Invalid symbol {symbol}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error fetching ticker for {symbol}: {e}")
            raise

    def get_orderbook(self, symbol: str, limit: int = 20) -> Dict[str, List]:
        """Get order book"""
        if not self._initialized:
            if not self.connect():
                raise ConnectionError("Failed to connect to MEXC")

        try:
            orderbook = self.exchange.fetch_order_book(symbol, limit)
            return {
                'bids': orderbook['bids'],
                'asks': orderbook['asks'],
                'timestamp': orderbook.get('timestamp'),
                'nonce': orderbook.get('nonce')
            }
        except Exception as e:
            self.logger.error(f"Error fetching orderbook for {symbol}: {e}")
            raise

    def get_ohlcv(self, symbol: str, timeframe: str = '1h',
                  since: Optional[datetime] = None,
                  limit: Optional[int] = None) -> pd.DataFrame:
        """Get OHLCV data"""
        if not self._initialized:
            if not self.connect():
                raise ConnectionError("Failed to connect to MEXC")

        try:
            since_ms = None
            if since:
                since_ms = int(since.timestamp() * 1000)

            # Default limit
            if limit is None:
                limit = 500

            self.logger.debug(f"Fetching OHLCV data for {symbol}, timeframe={timeframe}, limit={limit}")

            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, since_ms, limit)

            if not ohlcv:
                self.logger.warning(f"No OHLCV data returned for {symbol}")
                return pd.DataFrame()

            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)

            self.logger.info(f"Fetched {len(df)} candles for {symbol}")
            return df

        except ccxt.BadSymbol as e:
            self.logger.error(f"Invalid symbol {symbol}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error fetching OHLCV for {symbol}: {e}")
            raise

    def get_balance(self) -> Dict[str, float]:
        """Get account balance"""
        if not self._initialized:
            if not self.connect():
                raise ConnectionError("Failed to connect to MEXC")

        try:
            balance = self.exchange.fetch_balance()
            # Return only non-zero free balances
            result = {}
            for currency, amounts in balance.get('free', {}).items():
                if amounts and float(amounts) > 0:
                    result[currency] = float(amounts)

            self.logger.info(f"Account balance retrieved: {len(result)} currencies")
            return result

        except ccxt.AuthenticationError as e:
            self.logger.error(f"Authentication error fetching balance: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error fetching balance: {e}")
            raise

    def create_order(self, symbol: str, order_type: str, side: str,
                     amount: float, price: Optional[float] = None,
                     params: Optional[Dict] = None) -> Dict[str, Any]:
        """Create an order"""
        if not self._initialized:
            if not self.connect():
                raise ConnectionError("Failed to connect to MEXC")

        if params is None:
            params = {}

        try:
            self.logger.info(f"Creating order: {side} {amount} {symbol} @ {price or 'market'}")

            order = self.exchange.create_order(
                symbol=symbol,
                type=order_type,
                side=side,
                amount=amount,
                price=price,
                params=params
            )

            self.logger.info(f"Order created successfully: {order.get('id')}")

            return {
                'id': order.get('id'),
                'symbol': order.get('symbol'),
                'type': order.get('type'),
                'side': order.get('side'),
                'price': order.get('price'),
                'amount': order.get('amount'),
                'filled': order.get('filled'),
                'remaining': order.get('remaining'),
                'status': order.get('status'),
                'timestamp': order.get('timestamp'),
                'fee': order.get('fee')
            }

        except ccxt.InsufficientFunds as e:
            self.logger.error(f"Insufficient funds for order: {e}")
            raise
        except ccxt.InvalidOrder as e:
            self.logger.error(f"Invalid order: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error creating order: {e}")
            raise

    def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """Cancel an order"""
        if not self._initialized:
            if not self.connect():
                raise ConnectionError("Failed to connect to MEXC")

        try:
            self.logger.info(f"Cancelling order {order_id} for {symbol}")
            result = self.exchange.cancel_order(order_id, symbol)
            self.logger.info(f"Order cancelled successfully: {order_id}")
            return result
        except ccxt.OrderNotFound as e:
            self.logger.error(f"Order not found: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error cancelling order: {e}")
            raise

    def get_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """Get order information"""
        if not self._initialized:
            if not self.connect():
                raise ConnectionError("Failed to connect to MEXC")

        try:
            order = self.exchange.fetch_order(order_id, symbol)
            return order
        except ccxt.OrderNotFound as e:
            self.logger.error(f"Order not found: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error fetching order: {e}")
            raise

    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get open orders"""
        if not self._initialized:
            if not self.connect():
                raise ConnectionError("Failed to connect to MEXC")

        try:
            orders = self.exchange.fetch_open_orders(symbol)
            self.logger.info(f"Retrieved {len(orders)} open orders")
            return orders
        except Exception as e:
            self.logger.error(f"Error fetching open orders: {e}")
            raise

    def get_closed_orders(self, symbol: Optional[str] = None,
                          since: Optional[datetime] = None,
                          limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get closed orders"""
        if not self._initialized:
            if not self.connect():
                raise ConnectionError("Failed to connect to MEXC")

        try:
            since_ms = None
            if since:
                since_ms = int(since.timestamp() * 1000)

            orders = self.exchange.fetch_closed_orders(symbol, since_ms, limit)
            self.logger.info(f"Retrieved {len(orders)} closed orders")
            return orders
        except Exception as e:
            self.logger.error(f"Error fetching closed orders: {e}")
            raise

    def get_trades(self, symbol: str, since: Optional[datetime] = None,
                   limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get trade history"""
        if not self._initialized:
            if not self.connect():
                raise ConnectionError("Failed to connect to MEXC")

        try:
            since_ms = None
            if since:
                since_ms = int(since.timestamp() * 1000)

            trades = self.exchange.fetch_my_trades(symbol, since_ms, limit)
            self.logger.info(f"Retrieved {len(trades)} trades for {symbol}")
            return trades
        except Exception as e:
            self.logger.error(f"Error fetching trades: {e}")
            raise

    def get_markets(self) -> Dict[str, Dict]:
        """Get available markets"""
        if not self._initialized:
            if not self.connect():
                raise ConnectionError("Failed to connect to MEXC")

        return self.exchange.markets

    def get_fees(self, symbol: str) -> Dict[str, float]:
        """Get trading fees"""
        if not self._initialized:
            if not self.connect():
                raise ConnectionError("Failed to connect to MEXC")

        try:
            market = self.exchange.market(symbol)
            return {
                'maker': market.get('maker', 0.0002),  # MEXC default: 0.02%
                'taker': market.get('taker', 0.0002)   # MEXC default: 0.02%
            }
        except Exception as e:
            self.logger.error(f"Error fetching fees for {symbol}: {e}")
            # Return default MEXC fees
            return {
                'maker': 0.0002,
                'taker': 0.0002
            }

    def check_connection(self) -> bool:
        """Check if connection is alive"""
        try:
            self.exchange.fetch_time()
            return True
        except:
            return False
