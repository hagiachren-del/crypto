"""Database integration for trade history and persistence"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class TradingDatabase:
    """SQLite database for storing trading data"""

    def __init__(self, db_path: str = "data/trading.db"):
        """
        Initialize trading database

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        """Create database tables"""
        cursor = self.conn.cursor()

        # Trades table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                action TEXT NOT NULL,
                quantity REAL NOT NULL,
                price REAL NOT NULL,
                fees REAL DEFAULT 0,
                pnl REAL,
                portfolio_value REAL,
                strategy TEXT,
                signal_data TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Equity curve table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS equity_curve (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                equity REAL NOT NULL,
                cash REAL NOT NULL,
                positions INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Performance metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL UNIQUE,
                total_trades INTEGER DEFAULT 0,
                winning_trades INTEGER DEFAULT 0,
                losing_trades INTEGER DEFAULT 0,
                total_pnl REAL DEFAULT 0,
                win_rate REAL DEFAULT 0,
                profit_factor REAL DEFAULT 0,
                sharpe_ratio REAL DEFAULT 0,
                max_drawdown REAL DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Market data cache table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_data_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume REAL NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, timeframe, timestamp)
            )
        """)

        # AI analysis results table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                symbol TEXT NOT NULL,
                sentiment TEXT,
                confidence REAL,
                analysis_data TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_equity_timestamp ON equity_curve(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_market_symbol_time ON market_data_cache(symbol, timeframe, timestamp)")

        self.conn.commit()
        logger.info(f"Database initialized at {self.db_path}")

    def save_trade(self, trade_data: Dict[str, Any]) -> int:
        """
        Save trade to database

        Args:
            trade_data: Trade information

        Returns:
            Trade ID
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO trades
            (timestamp, symbol, side, action, quantity, price, fees, pnl,
             portfolio_value, strategy, signal_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trade_data.get('timestamp', datetime.now()),
            trade_data.get('symbol'),
            trade_data.get('side'),
            trade_data.get('action'),
            trade_data.get('quantity'),
            trade_data.get('price'),
            trade_data.get('fees', 0),
            trade_data.get('pnl'),
            trade_data.get('portfolio_value'),
            trade_data.get('strategy'),
            json.dumps(trade_data.get('signal_data', {}))
        ))

        self.conn.commit()
        trade_id = cursor.lastrowid
        logger.debug(f"Trade saved to database: ID {trade_id}")
        return trade_id

    def save_equity_point(self, timestamp: datetime, equity: float,
                         cash: float, positions: int):
        """Save equity curve point"""
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO equity_curve (timestamp, equity, cash, positions)
            VALUES (?, ?, ?, ?)
        """, (timestamp, equity, cash, positions))

        self.conn.commit()

    def save_daily_metrics(self, metrics: Dict[str, Any]):
        """Save daily performance metrics"""
        cursor = self.conn.cursor()

        date = datetime.now().date()

        cursor.execute("""
            INSERT OR REPLACE INTO performance_metrics
            (date, total_trades, winning_trades, losing_trades, total_pnl,
             win_rate, profit_factor, sharpe_ratio, max_drawdown)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            date,
            metrics.get('total_trades', 0),
            metrics.get('winning_trades', 0),
            metrics.get('losing_trades', 0),
            metrics.get('total_pnl', 0),
            metrics.get('win_rate', 0),
            metrics.get('profit_factor', 0),
            metrics.get('sharpe_ratio', 0),
            metrics.get('max_drawdown', 0)
        ))

        self.conn.commit()
        logger.info(f"Daily metrics saved for {date}")

    def save_ai_analysis(self, symbol: str, analysis: Dict[str, Any]):
        """Save AI analysis results"""
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO ai_analysis (timestamp, symbol, sentiment, confidence, analysis_data)
            VALUES (?, ?, ?, ?, ?)
        """, (
            datetime.now(),
            symbol,
            analysis.get('sentiment'),
            analysis.get('confidence'),
            json.dumps(analysis)
        ))

        self.conn.commit()

    def get_trades(self, symbol: Optional[str] = None,
                  start_date: Optional[datetime] = None,
                  end_date: Optional[datetime] = None,
                  limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get trades from database

        Args:
            symbol: Filter by symbol
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of trades

        Returns:
            List of trades
        """
        cursor = self.conn.cursor()

        query = "SELECT * FROM trades WHERE 1=1"
        params = []

        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)

        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)

        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        trades = []
        for row in rows:
            trade = dict(row)
            if trade.get('signal_data'):
                trade['signal_data'] = json.loads(trade['signal_data'])
            trades.append(trade)

        return trades

    def get_equity_curve(self, start_date: Optional[datetime] = None,
                        end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get equity curve data"""
        cursor = self.conn.cursor()

        query = "SELECT * FROM equity_curve WHERE 1=1"
        params = []

        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)

        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)

        query += " ORDER BY timestamp ASC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def get_daily_metrics(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get daily performance metrics"""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT * FROM performance_metrics
            ORDER BY date DESC
            LIMIT ?
        """, (days,))

        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_latest_ai_analysis(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get latest AI analysis for symbol"""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT * FROM ai_analysis
            WHERE symbol = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (symbol,))

        row = cursor.fetchone()
        if row:
            result = dict(row)
            if result.get('analysis_data'):
                result['analysis_data'] = json.loads(result['analysis_data'])
            return result

        return None

    def get_statistics(self) -> Dict[str, Any]:
        """Get overall trading statistics"""
        cursor = self.conn.cursor()

        # Total trades
        cursor.execute("SELECT COUNT(*) as count FROM trades")
        total_trades = cursor.fetchone()['count']

        # Win rate
        cursor.execute("""
            SELECT
                COUNT(CASE WHEN pnl > 0 THEN 1 END) as wins,
                COUNT(CASE WHEN pnl < 0 THEN 1 END) as losses,
                AVG(CASE WHEN pnl > 0 THEN pnl END) as avg_win,
                AVG(CASE WHEN pnl < 0 THEN pnl END) as avg_loss,
                SUM(pnl) as total_pnl
            FROM trades
            WHERE pnl IS NOT NULL
        """)
        stats = dict(cursor.fetchone())

        win_rate = 0
        if stats['wins'] and (stats['wins'] + stats['losses']) > 0:
            win_rate = (stats['wins'] / (stats['wins'] + stats['losses'])) * 100

        return {
            'total_trades': total_trades,
            'winning_trades': stats['wins'] or 0,
            'losing_trades': stats['losses'] or 0,
            'win_rate': win_rate,
            'avg_win': stats['avg_win'] or 0,
            'avg_loss': stats['avg_loss'] or 0,
            'total_pnl': stats['total_pnl'] or 0
        }

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
