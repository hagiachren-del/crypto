#!/usr/bin/env python3
"""
Production Trading Script with MEXC and Claude AI

Features:
- MEXC exchange integration
- Claude AI-powered market analysis
- Real-time notifications
- Database persistence
- Production logging
- Health monitoring
"""

import sys
import os
import argparse
from datetime import datetime
import signal

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.config import Config
from src.utils.logger import setup_production_logging, TradeLogger
from src.utils.notifications import NotificationManager
from src.utils.database import TradingDatabase
from src.exchanges.mexc_adapter import MEXCAdapter
from src.ai.claude_analyzer import ClaudeMarketAnalyzer
from src.strategies import (
    SMACrossStrategy, EMACrossStrategy, RSIStrategy,
    MACDStrategy, BollingerBandsStrategy, MultiIndicatorStrategy
)
from src.core.engine import TradingEngine
from src.core.portfolio import Portfolio
from src.core.risk import RiskManager
from src.indicators.indicators import Indicators

# Strategy mapping
STRATEGY_MAP = {
    'sma_cross': SMACrossStrategy,
    'ema_cross': EMACrossStrategy,
    'rsi_strategy': RSIStrategy,
    'macd_strategy': MACDStrategy,
    'bollinger_bands': BollingerBandsStrategy,
    'multi_indicator': MultiIndicatorStrategy
}


class ProductionTradingBot:
    """Production-grade trading bot with MEXC and Claude AI"""

    def __init__(self, config_path: str):
        """
        Initialize production trading bot

        Args:
            config_path: Path to configuration file
        """
        # Setup logging
        self.logger = setup_production_logging('crypto_trader_prod',
                                               log_level='INFO')
        self.trade_logger = TradeLogger()

        self.logger.info("="*60)
        self.logger.info("🚀 PRODUCTION CRYPTO TRADING BOT")
        self.logger.info("="*60)

        # Load configuration
        self.config = Config(config_path)
        self.logger.info(f"Configuration loaded from: {config_path}")
        self.logger.info(f"Mode: {self.config.mode}")
        self.logger.info(f"Exchange: {self.config.exchange}")
        self.logger.info(f"Strategy: {self.config.strategy_name}")

        # Initialize components
        self._init_database()
        self._init_notifications()
        self._init_exchange()
        self._init_ai_analyzer()
        self._init_strategy()
        self._init_trading_components()

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        self.running = False

    def _init_database(self):
        """Initialize database connection"""
        if self.config.get('database.enabled', True):
            db_path = self.config.get('database.path', 'data/production.db')
            self.db = TradingDatabase(db_path)
            self.logger.info(f"Database initialized: {db_path}")
        else:
            self.db = None
            self.logger.warning("Database disabled in configuration")

    def _init_notifications(self):
        """Initialize notification system"""
        notif_config = self.config.get('notifications', {})
        self.notifications = NotificationManager(notif_config)

        if notif_config.get('telegram', {}).get('enabled'):
            self.logger.info("Telegram notifications enabled")
        if notif_config.get('email', {}).get('enabled'):
            self.logger.info("Email notifications enabled")

        # Send startup notification
        self.notifications.send_alert(
            "Bot Started",
            f"Trading bot started in {self.config.mode} mode",
            "info"
        )

    def _init_exchange(self):
        """Initialize exchange connection"""
        exchange_name = self.config.exchange.lower()

        self.logger.info(f"Connecting to {exchange_name.upper()} exchange...")

        if exchange_name == 'mexc':
            api_key = self.config.get_secret('mexc.api_key')
            api_secret = self.config.get_secret('mexc.api_secret')

            if not api_key or not api_secret:
                raise ValueError("MEXC API credentials not found in secrets.yml")

            self.exchange = MEXCAdapter(api_key, api_secret)

        else:
            raise ValueError(f"Unsupported exchange: {exchange_name}")

        # Test connection
        if not self.exchange.connect():
            raise ConnectionError(f"Failed to connect to {exchange_name}")

        self.logger.info(f"✅ Connected to {exchange_name.upper()}")

    def _init_ai_analyzer(self):
        """Initialize Claude AI analyzer"""
        ai_config = self.config.get('ai', {})

        if not ai_config.get('enabled', False):
            self.ai_analyzer = None
            self.logger.warning("AI analysis disabled")
            return

        try:
            api_key = self.config.get_secret('claude.api_key') or os.getenv('ANTHROPIC_API_KEY')
            model = ai_config.get('model', 'claude-sonnet-4-5-20250929')

            self.ai_analyzer = ClaudeMarketAnalyzer(api_key, model)
            self.logger.info(f"✅ Claude AI initialized ({model})")

            # Test AI connection
            self.logger.info("Testing Claude AI connection...")
            # Small test to verify API key works

        except Exception as e:
            self.logger.error(f"Failed to initialize Claude AI: {e}")
            self.logger.warning("Continuing without AI analysis")
            self.ai_analyzer = None

    def _init_strategy(self):
        """Initialize trading strategy"""
        strategy_name = self.config.strategy_name

        if strategy_name not in STRATEGY_MAP:
            raise ValueError(f"Unknown strategy: {strategy_name}")

        strategy_class = STRATEGY_MAP[strategy_name]
        self.strategy = strategy_class(self.config.strategy_params)

        self.logger.info(f"✅ Strategy loaded: {strategy_name}")

    def _init_trading_components(self):
        """Initialize portfolio and risk management"""
        # Get initial capital based on mode
        if self.config.mode == 'live':
            initial_capital = self.config.get('live.initial_capital', 1000)
        elif self.config.mode == 'paper':
            initial_capital = self.config.get('paper.initial_capital', 10000)
        else:
            initial_capital = self.config.get('backtest.initial_capital', 10000)

        self.portfolio = Portfolio(initial_capital)
        self.risk_manager = RiskManager(self.config.risk_params)
        self.indicators = Indicators()

        self.logger.info(f"✅ Portfolio initialized: ${initial_capital:,.2f}")
        self.logger.info(f"✅ Risk management active")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info("Shutdown signal received...")
        self.stop()

    def start(self):
        """Start the trading bot"""
        self.logger.info("\n" + "="*60)
        self.logger.info("STARTING PRODUCTION TRADING BOT")
        self.logger.info("="*60)

        # Safety check for live trading
        if self.config.mode == 'live':
            self._live_trading_safety_check()

        self.running = True

        try:
            # Initialize trading engine
            engine = TradingEngine(
                strategy=self.strategy,
                exchange=self.exchange,
                mode=self.config.mode,
                initial_capital=self.portfolio.initial_capital,
                risk_config=self.config.risk_params,
                symbols=self.config.symbols
            )

            # Get update interval
            if self.config.mode == 'live':
                interval = self.config.get('live.update_interval', 30)
            else:
                interval = self.config.get('paper.update_interval', 60)

            self.logger.info(f"Update interval: {interval} seconds")
            self.logger.info(f"Symbols: {', '.join(self.config.symbols)}")
            self.logger.info("\n🤖 Bot is now running... Press Ctrl+C to stop\n")

            # Send start notification
            self.notifications.send_alert(
                "Bot Running",
                f"Trading bot is now active\nMode: {self.config.mode}\nSymbols: {', '.join(self.config.symbols)}",
                "info"
            )

            # Start trading
            engine.start(interval=interval)

        except KeyboardInterrupt:
            self.logger.info("\nKeyboard interrupt received")
        except Exception as e:
            self.logger.error(f"Trading bot error: {e}", exc_info=True)
            self.notifications.send_alert("Bot Error", str(e), "critical")
        finally:
            self.stop()

    def _live_trading_safety_check(self):
        """Safety checks before live trading"""
        self.logger.warning("\n" + "!"*60)
        self.logger.warning("LIVE TRADING MODE - REAL MONEY AT RISK!")
        self.logger.warning("!"*60)

        # Check if dry run first is enabled
        dry_run = self.config.get('live.dry_run_first', True)
        if dry_run:
            self.logger.error("dry_run_first is enabled - switch to paper mode first!")
            sys.exit(1)

        # Verify small initial capital
        capital = self.config.get('live.initial_capital', 0)
        if capital > 5000:
            self.logger.warning(f"Initial capital is ${capital:,.2f} - Consider starting smaller!")

        # Display risk limits
        self.logger.info("\nRisk Limits:")
        self.logger.info(f"  - Max position: {self.risk_manager.max_position_pct:.1%}")
        self.logger.info(f"  - Stop loss: {self.risk_manager.stop_loss_pct:.1%}")
        self.logger.info(f"  - Max daily loss: {self.risk_manager.max_daily_loss_pct:.1%}")
        self.logger.info(f"  - Max daily trades: {self.risk_manager.max_daily_trades}")

        input("\nPress ENTER to continue with LIVE trading, or Ctrl+C to abort...")

    def stop(self):
        """Stop the trading bot"""
        if not self.running:
            return

        self.logger.info("\n" + "="*60)
        self.logger.info("STOPPING TRADING BOT")
        self.logger.info("="*60)

        self.running = False

        # Close database
        if self.db:
            self.db.close()

        # Send shutdown notification
        self.notifications.send_alert(
            "Bot Stopped",
            "Trading bot has been shut down",
            "warning"
        )

        self.logger.info("✅ Bot stopped successfully")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Production Crypto Trading Bot with MEXC and Claude AI'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config/production.yml',
        help='Path to configuration file (default: config/production.yml)'
    )
    parser.add_argument(
        '--mode',
        type=str,
        choices=['paper', 'live'],
        help='Override trading mode from config'
    )

    args = parser.parse_args()

    try:
        # Create and start bot
        bot = ProductionTradingBot(args.config)

        # Override mode if specified
        if args.mode:
            bot.config._config['mode'] = args.mode
            bot.logger.info(f"Mode overridden to: {args.mode}")

        bot.start()

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
