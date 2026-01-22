"""Binance exchange adapter"""

import ccxt
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime
from .base import BaseExchange


class BinanceAdapter(BaseExchange):
    """Binance exchange implementation"""

    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None,
                 testnet: bool = False):
        """
        Initialize Binance adapter

        Args:
            api_key: Binance API key
            api_secret: Binance API secret
            testnet: Whether to use testnet
        """
        super().__init__(api_key, api_secret, testnet)
        self.exchange = None

    def connect(self) -> bool:
        """
        Connect to Binance

        Returns:
            True if successful
        """
        try:
            if self.testnet:
                self.exchange = ccxt.binance({
                    'apiKey': self.api_key,
                    'secret': self.api_secret,
                    'enableRateLimit': True,
                    'options': {'defaultType': 'future'},
                    'urls': {
                        'api': {
                            'public': 'https://testnet.binancefuture.com/fapi/v1',
                            'private': 'https://testnet.binancefuture.com/fapi/v1',
                        }
                    }
                })
            else:
                self.exchange = ccxt.binance({
                    'apiKey': self.api_key,
                    'secret': self.api_secret,
                    'enableRateLimit': True,
                })

            # Test connection
            self.exchange.load_markets()
            self._initialized = True
            return True

        except Exception as e:
            print(f"Failed to connect to Binance: {e}")
            return False

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get current ticker data"""
        if not self._initialized:
            self.connect()

        ticker = self.exchange.fetch_ticker(symbol)
        return {
            'symbol': symbol,
            'bid': ticker['bid'],
            'ask': ticker['ask'],
            'last': ticker['last'],
            'volume': ticker['baseVolume'],
            'timestamp': ticker['timestamp']
        }

    def get_orderbook(self, symbol: str, limit: int = 20) -> Dict[str, List]:
        """Get order book"""
        if not self._initialized:
            self.connect()

        orderbook = self.exchange.fetch_order_book(symbol, limit)
        return {
            'bids': orderbook['bids'],
            'asks': orderbook['asks'],
            'timestamp': orderbook['timestamp']
        }

    def get_ohlcv(self, symbol: str, timeframe: str = '1h',
                  since: Optional[datetime] = None,
                  limit: Optional[int] = None) -> pd.DataFrame:
        """Get OHLCV data"""
        if not self._initialized:
            self.connect()

        since_ms = None
        if since:
            since_ms = int(since.timestamp() * 1000)

        ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, since_ms, limit)

        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)

        return df

    def get_balance(self) -> Dict[str, float]:
        """Get account balance"""
        if not self._initialized:
            self.connect()

        balance = self.exchange.fetch_balance()
        return {k: v['free'] for k, v in balance['total'].items() if v['free'] > 0}

    def create_order(self, symbol: str, order_type: str, side: str,
                     amount: float, price: Optional[float] = None,
                     params: Optional[Dict] = None) -> Dict[str, Any]:
        """Create an order"""
        if not self._initialized:
            self.connect()

        if params is None:
            params = {}

        order = self.exchange.create_order(
            symbol=symbol,
            type=order_type,
            side=side,
            amount=amount,
            price=price,
            params=params
        )

        return {
            'id': order['id'],
            'symbol': order['symbol'],
            'type': order['type'],
            'side': order['side'],
            'price': order['price'],
            'amount': order['amount'],
            'status': order['status'],
            'timestamp': order['timestamp']
        }

    def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """Cancel an order"""
        if not self._initialized:
            self.connect()

        result = self.exchange.cancel_order(order_id, symbol)
        return result

    def get_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """Get order information"""
        if not self._initialized:
            self.connect()

        order = self.exchange.fetch_order(order_id, symbol)
        return order

    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get open orders"""
        if not self._initialized:
            self.connect()

        orders = self.exchange.fetch_open_orders(symbol)
        return orders

    def get_closed_orders(self, symbol: Optional[str] = None,
                          since: Optional[datetime] = None,
                          limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get closed orders"""
        if not self._initialized:
            self.connect()

        since_ms = None
        if since:
            since_ms = int(since.timestamp() * 1000)

        orders = self.exchange.fetch_closed_orders(symbol, since_ms, limit)
        return orders

    def get_trades(self, symbol: str, since: Optional[datetime] = None,
                   limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get trade history"""
        if not self._initialized:
            self.connect()

        since_ms = None
        if since:
            since_ms = int(since.timestamp() * 1000)

        trades = self.exchange.fetch_my_trades(symbol, since_ms, limit)
        return trades

    def get_markets(self) -> Dict[str, Dict]:
        """Get available markets"""
        if not self._initialized:
            self.connect()

        return self.exchange.markets

    def get_fees(self, symbol: str) -> Dict[str, float]:
        """Get trading fees"""
        if not self._initialized:
            self.connect()

        market = self.exchange.market(symbol)
        return {
            'maker': market['maker'],
            'taker': market['taker']
        }
