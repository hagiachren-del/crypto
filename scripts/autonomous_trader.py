#!/usr/bin/env python3
"""
Autonomous AI Trading Agent - Production-Ready Cryptocurrency Trading Bot

This autonomous agent uses DeepSeek AI to make intelligent trading decisions 24/7.
It features:
- Continuous market monitoring and analysis
- AI-driven entry and exit decisions
- Advanced risk management
- Real-time notifications
- Database logging
- Emergency stop mechanisms
- Portfolio optimization

Author: AI Crypto Trader
Version: 1.0.0
"""

import sys
import os
import time
import signal
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import traceback

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import yaml
from src.ai.deepseek_analyzer import DeepSeekMarketAnalyzer
from src.ai.market_intelligence import MarketIntelligence
from src.exchanges.mexc_adapter import MEXCAdapter
from src.indicators.indicators import Indicators
from src.utils.database import TradingDatabase
from src.utils.logger import setup_production_logging
from src.utils.notifications import NotificationManager

logger = logging.getLogger(__name__)


class AutonomousTrader:
    """
    Fully autonomous AI-powered cryptocurrency trading agent

    This agent operates independently, making trading decisions based on:
    - Real-time market data analysis
    - DeepSeek AI intelligence
    - Technical indicators
    - Risk management rules
    - Portfolio optimization
    """

    def __init__(self, config_path: str = "config/autonomous.yml"):
        """
        Initialize autonomous trader

        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.running = False
        self.should_stop = False

        # Initialize components
        self.logger = self._setup_logging()
        self.db = TradingDatabase(self.config.get('database', {}).get('path', 'data/autonomous.db'))
        self.notifier = NotificationManager(self.config.get('notifications', {}))

        # Load API keys from secrets
        secrets = self._load_secrets()

        # Initialize AI analyzer
        ai_config = self.config.get('ai', {})
        deepseek_api_key = secrets.get('deepseek', {}).get('api_key')
        if not deepseek_api_key:
            raise ValueError("DeepSeek API key not found in config/secrets.yml")

        self.ai = DeepSeekMarketAnalyzer(
            api_key=deepseek_api_key,
            model=ai_config.get('model', 'deepseek-chat')
        )

        # Initialize market intelligence system
        self.market_intelligence = MarketIntelligence(self.config.get('intelligence', {}))
        self.logger.info("✅ Market Intelligence System initialized")
        self.logger.info("   - Technical analysis (charts, indicators)")
        self.logger.info("   - News sentiment analysis")
        self.logger.info("   - Social media sentiment (Twitter, Reddit)")
        self.logger.info("   - Market-wide sentiment (Fear & Greed)")
        self.logger.info("   - On-chain metrics")
        self.logger.info("   - Order flow analysis")

        # Initialize exchange
        mexc_config = secrets.get('mexc', {})
        self.exchange = MEXCAdapter(
            api_key=mexc_config.get('api_key'),
            api_secret=mexc_config.get('api_secret')
        )

        # Trading state
        self.symbols = self.config.get('symbols', ['BTC/USDT'])
        self.initial_capital = self.config.get('initial_capital', 10000.0)
        self.cash = self.initial_capital
        self.positions: Dict[str, Dict] = {}
        self.data_buffer: Dict[str, pd.DataFrame] = {}

        # Risk management
        self.risk_config = self.config.get('risk', {})
        self.max_position_size = self.initial_capital * self.risk_config.get('max_position_pct', 0.05)
        self.max_daily_trades = self.risk_config.get('max_daily_trades', 20)
        self.max_daily_loss = self.initial_capital * self.risk_config.get('max_daily_loss_pct', 0.03)

        # Statistics
        self.stats = {
            'trades_today': 0,
            'daily_pnl': 0.0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'consecutive_losses': 0,
            'api_errors': 0,
            'last_trade_time': None,
            'start_time': datetime.now()
        }

        # Emergency stop conditions
        self.emergency_stop_config = self.config.get('emergency_stop', {})

        self.logger.info("=" * 80)
        self.logger.info("AUTONOMOUS AI TRADER INITIALIZED")
        self.logger.info("=" * 80)
        self.logger.info(f"AI Model: DeepSeek ({ai_config.get('model', 'deepseek-chat')})")
        self.logger.info(f"Exchange: MEXC")
        self.logger.info(f"Symbols: {', '.join(self.symbols)}")
        self.logger.info(f"Initial Capital: ${self.initial_capital:,.2f}")
        self.logger.info(f"Mode: {self.config.get('mode', 'paper').upper()}")
        self.logger.info("=" * 80)

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def _load_secrets(self) -> Dict:
        """Load secrets from secrets.yml"""
        secrets_path = 'config/secrets.yml'
        if not os.path.exists(secrets_path):
            raise FileNotFoundError(f"Secrets file not found: {secrets_path}")

        with open(secrets_path, 'r') as f:
            return yaml.safe_load(f)

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        log_config = self.config.get('logging', {})
        return setup_production_logging(
            app_name='autonomous_trader',
            log_level=log_config.get('level', 'INFO')
        )

    def start(self):
        """Start autonomous trading"""
        try:
            # Connect to exchange
            if not self.exchange.connect():
                raise ConnectionError("Failed to connect to MEXC exchange")

            self.logger.info("Connected to MEXC exchange successfully")

            # Send startup notification
            self.notifier.send_startup_notification(
                mode=self.config.get('mode', 'paper'),
                symbols=self.symbols,
                capital=self.initial_capital
            )

            # Register signal handlers for graceful shutdown
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)

            self.running = True
            self.logger.info("Starting autonomous trading loop...")

            # Main trading loop
            self._trading_loop()

        except Exception as e:
            self.logger.error(f"Fatal error in autonomous trader: {e}")
            self.logger.error(traceback.format_exc())
            self.notifier.send_error_notification(str(e))
            raise

    def _trading_loop(self):
        """Main trading loop"""
        update_interval = self.config.get('update_interval', 60)
        analysis_interval = self.config.get('analysis_interval', 300)  # Deep analysis every 5 min
        last_analysis_time = {}

        while self.running and not self.should_stop:
            try:
                cycle_start = time.time()

                # Check emergency stop conditions
                if self._check_emergency_stop():
                    self.logger.critical("EMERGENCY STOP TRIGGERED!")
                    self.notifier.send_alert("EMERGENCY STOP TRIGGERED", "critical")
                    break

                # Reset daily stats if new day
                self._reset_daily_stats_if_needed()

                # Process each symbol
                for symbol in self.symbols:
                    try:
                        # Fetch latest market data
                        self._update_market_data(symbol)

                        # Check if we need deep AI analysis
                        should_analyze = (
                            symbol not in last_analysis_time or
                            (datetime.now() - last_analysis_time[symbol]).seconds >= analysis_interval
                        )

                        # Process trading logic
                        self._process_symbol(symbol, deep_analysis=should_analyze)

                        if should_analyze:
                            last_analysis_time[symbol] = datetime.now()

                    except Exception as e:
                        self.logger.error(f"Error processing {symbol}: {e}")
                        self.stats['api_errors'] += 1

                # Update portfolio metrics
                self._update_portfolio_metrics()

                # Log status periodically
                if int(time.time()) % 300 == 0:  # Every 5 minutes
                    self._log_status()

                # Sleep for remaining interval
                elapsed = time.time() - cycle_start
                sleep_time = max(0, update_interval - elapsed)
                time.sleep(sleep_time)

            except KeyboardInterrupt:
                self.logger.info("Keyboard interrupt received, shutting down...")
                break
            except Exception as e:
                self.logger.error(f"Error in trading loop: {e}")
                self.logger.error(traceback.format_exc())
                time.sleep(60)  # Wait before retrying

        # Shutdown
        self._shutdown()

    def _process_symbol(self, symbol: str, deep_analysis: bool = False):
        """
        Process trading logic for a symbol

        Args:
            symbol: Trading pair symbol
            deep_analysis: Whether to perform deep AI analysis
        """
        data = self.data_buffer.get(symbol)
        if data is None or len(data) < 50:
            return

        current_price = data['close'].iloc[-1]

        # Check if we have an open position
        if symbol in self.positions:
            self._manage_open_position(symbol, current_price, data)
        else:
            # Look for new trading opportunities
            if deep_analysis:
                self._analyze_entry_opportunity(symbol, current_price, data)

    def _manage_open_position(self, symbol: str, current_price: float, data: pd.DataFrame):
        """
        Manage an open position

        Args:
            symbol: Trading pair
            current_price: Current market price
            data: OHLCV data
        """
        position = self.positions[symbol]
        entry_price = position['entry_price']
        side = position['side']

        # Calculate current PnL
        if side == 'long':
            pnl_pct = ((current_price - entry_price) / entry_price) * 100
        else:
            pnl_pct = ((entry_price - current_price) / entry_price) * 100

        position['current_price'] = current_price
        position['pnl_pct'] = pnl_pct
        position['pnl'] = position['size'] * (pnl_pct / 100)

        # Check exit conditions
        should_exit, reason = self._check_exit_conditions(symbol, position, data)

        if should_exit:
            self._close_position(symbol, current_price, reason)
        else:
            # Update trailing stop if enabled
            if self.risk_config.get('trailing_stop', False):
                self._update_trailing_stop(symbol, current_price)

    def _check_exit_conditions(self, symbol: str, position: Dict, data: pd.DataFrame) -> tuple:
        """
        Check if position should be exited

        Args:
            symbol: Trading pair
            position: Position information
            data: Market data

        Returns:
            (should_exit, reason)
        """
        current_price = position['current_price']
        pnl_pct = position['pnl_pct']

        # Stop loss
        if self.risk_config.get('use_stop_loss', True):
            stop_loss_pct = self.risk_config.get('stop_loss_pct', 0.02) * 100
            if pnl_pct <= -stop_loss_pct:
                return True, f"Stop loss hit ({pnl_pct:.2f}%)"

        # Take profit
        if self.risk_config.get('use_take_profit', True):
            take_profit_pct = self.risk_config.get('take_profit_pct', 0.04) * 100
            if pnl_pct >= take_profit_pct:
                return True, f"Take profit hit ({pnl_pct:.2f}%)"

        # Trailing stop
        if 'trailing_stop_price' in position:
            if position['side'] == 'long':
                if current_price <= position['trailing_stop_price']:
                    return True, f"Trailing stop hit (${position['trailing_stop_price']:.2f})"
            else:
                if current_price >= position['trailing_stop_price']:
                    return True, f"Trailing stop hit (${position['trailing_stop_price']:.2f})"

        # Time-based exit (if position is old)
        hold_time = datetime.now() - position['entry_time']
        max_hold_hours = self.config.get('max_position_hold_hours', 48)
        if hold_time.total_seconds() / 3600 > max_hold_hours:
            # Ask AI if we should continue holding
            indicators = self._calculate_indicators(data)
            validation = self.ai.validate_trade_signal(
                symbol=symbol,
                signal='sell' if position['side'] == 'long' else 'buy',
                data=data,
                indicators=indicators,
                reasoning=f"Position held for {hold_time.total_seconds() / 3600:.1f} hours"
            )

            if validation.get('confidence', 0) > 70:
                return True, f"AI recommends exit after {hold_time.total_seconds() / 3600:.1f}h hold"

        return False, ""

    def _analyze_entry_opportunity(self, symbol: str, current_price: float, data: pd.DataFrame):
        """
        Analyze potential entry opportunity using comprehensive intelligence + AI

        Args:
            symbol: Trading pair
            current_price: Current price
            data: Market data
        """
        # Check if we can open new position
        if not self._can_open_position():
            return

        # Calculate technical indicators
        indicators = self._calculate_indicators(data)

        # Get COMPREHENSIVE MARKET INTELLIGENCE (multi-source analysis)
        try:
            self.logger.info(f"📊 Running comprehensive market analysis for {symbol}...")

            # Get comprehensive analysis from all sources
            comprehensive_analysis = self.market_intelligence.get_comprehensive_analysis(
                symbol=symbol,
                data=data
            )

            overall_score = comprehensive_analysis['overall_score']
            recommendation = comprehensive_analysis['recommendation']

            self.logger.info(f"🎯 Market Intelligence Score: {overall_score}/100 - {recommendation}")
            self.logger.info(f"   Technical: {comprehensive_analysis['technical']['score']}/100 "
                           f"({comprehensive_analysis['technical']['trend']})")
            self.logger.info(f"   News Sentiment: {comprehensive_analysis['news_sentiment']['score']}/100")
            self.logger.info(f"   Social Sentiment: {comprehensive_analysis['social_sentiment']['score']}/100")
            self.logger.info(f"   Market Sentiment: {comprehensive_analysis['market_sentiment']['fear_greed_index']} "
                           f"({comprehensive_analysis['market_sentiment']['sentiment']})")

            # Only proceed if comprehensive analysis is favorable
            if overall_score < 45:
                self.logger.info(f"❌ Market intelligence score too low: {overall_score}/100")
                return

            # Now get DeepSeek AI analysis with comprehensive context
            self.logger.info(f"🤖 Requesting DeepSeek AI analysis with market intelligence context...")

            # Prepare comprehensive summary for AI
            intelligence_summary = self.market_intelligence.get_analysis_summary(comprehensive_analysis)

            # Enhanced AI analysis with comprehensive market context
            analysis = self.ai.analyze_market_data(
                symbol=symbol,
                data=data,
                indicators=indicators,
                multi_timeframe=True,
                additional_context=intelligence_summary  # Pass comprehensive intelligence to AI
            )

            self.logger.info(f"🧠 AI Analysis: Sentiment={analysis.get('sentiment')}, "
                            f"Confidence={analysis.get('confidence')}%")

            # Save both analyses to database
            self.db.save_ai_analysis(symbol, {
                **analysis,
                'comprehensive_intelligence': comprehensive_analysis,
                'intelligence_score': overall_score,
                'recommendation': recommendation
            })

            # Check if AI agrees with comprehensive analysis
            signals = analysis.get('signals', {})
            ai_confidence = analysis.get('confidence', 0)
            min_confidence = self.config.get('ai', {}).get('confidence_threshold', 70)

            # Require both high AI confidence AND favorable market intelligence
            if ai_confidence < min_confidence:
                self.logger.info(f"⚠️  AI confidence too low: {ai_confidence}% < {min_confidence}%")
                return

            if overall_score < 55 and recommendation not in ['BUY', 'STRONG_BUY']:
                self.logger.info(f"⚠️  Market intelligence doesn't support entry: {recommendation}")
                return

            # Determine signal (AI must agree with market intelligence)
            signal = None
            if signals.get('buy_signal') and analysis.get('sentiment') == 'bullish':
                if recommendation in ['BUY', 'STRONG_BUY', 'WEAK_BUY']:
                    signal = 'buy'
                    self.logger.info(f"✅ BUY signal confirmed by both AI and market intelligence!")
                else:
                    self.logger.info(f"⚠️  AI suggests buy but market intelligence says {recommendation}")
            elif signals.get('sell_signal') and analysis.get('sentiment') == 'bearish':
                if recommendation in ['SELL', 'STRONG_SELL', 'WEAK_SELL']:
                    signal = 'sell'
                    self.logger.info(f"✅ SELL signal confirmed by both AI and market intelligence!")
                else:
                    self.logger.info(f"⚠️  AI suggests sell but market intelligence says {recommendation}")

            if signal:
                # Validate the signal with detailed analysis
                self._validate_and_execute_signal(symbol, signal, current_price, data, indicators, analysis)
            else:
                self.logger.info(f"⏸️  No clear signal - AI and market intelligence not aligned")

        except Exception as e:
            self.logger.error(f"Error in comprehensive analysis for {symbol}: {e}")
            self.logger.error(traceback.format_exc())

    def _validate_and_execute_signal(self, symbol: str, signal: str, current_price: float,
                                    data: pd.DataFrame, indicators: Dict, analysis: Dict):
        """
        Validate signal with AI and execute if approved

        Args:
            symbol: Trading pair
            signal: Trade signal (buy/sell)
            current_price: Current price
            data: Market data
            indicators: Technical indicators
            analysis: Initial AI analysis
        """
        try:
            # Get detailed validation from AI
            validation = self.ai.validate_trade_signal(
                symbol=symbol,
                signal=signal,
                data=data,
                indicators=indicators,
                reasoning=analysis.get('outlook', 'AI market analysis')
            )

            validation_status = validation.get('validation_status', 'rejected')
            confidence = validation.get('confidence', 0)

            self.logger.info(f"Signal validation for {symbol} {signal.upper()}: "
                           f"Status={validation_status}, Confidence={confidence}%")

            # Check if signal is approved
            if validation_status == 'approved' and confidence >= 70:
                # Execute the trade
                self._execute_entry(symbol, signal, current_price, validation)
            elif validation_status == 'conditional' and confidence >= 60:
                self.logger.info(f"Conditional approval for {symbol} - monitoring for better entry")
                # Could implement conditional entry logic here
            else:
                self.logger.info(f"Signal rejected for {symbol}: {validation.get('overall_assessment', 'N/A')}")

        except Exception as e:
            self.logger.error(f"Error validating signal for {symbol}: {e}")

    def _execute_entry(self, symbol: str, signal: str, current_price: float, validation: Dict):
        """
        Execute entry trade

        Args:
            symbol: Trading pair
            signal: Trade signal
            current_price: Current price
            validation: AI validation results
        """
        try:
            # Calculate position size
            risk_mgmt = validation.get('risk_management', {})
            position_size_rec = risk_mgmt.get('position_size_recommendation', 'medium')

            # Adjust position size based on AI recommendation
            size_multiplier = {
                'small': 0.5,
                'medium': 1.0,
                'large': 1.5
            }.get(position_size_rec, 1.0)

            position_size = self.max_position_size * size_multiplier

            # Ensure we have enough cash
            if position_size > self.cash:
                position_size = self.cash * 0.95  # Use 95% of available cash

            if position_size < 10:  # Minimum $10 position
                self.logger.warning(f"Position size too small for {symbol}: ${position_size:.2f}")
                return

            quantity = position_size / current_price

            # Execute trade based on mode
            mode = self.config.get('mode', 'paper')

            if mode == 'paper':
                # Paper trading
                self._execute_paper_entry(symbol, signal, quantity, current_price, validation)
            elif mode == 'live':
                # Live trading
                self._execute_live_entry(symbol, signal, quantity, current_price, validation)

        except Exception as e:
            self.logger.error(f"Error executing entry for {symbol}: {e}")
            self.notifier.send_error_notification(f"Entry execution error: {e}")

    def _execute_paper_entry(self, symbol: str, signal: str, quantity: float,
                            price: float, validation: Dict):
        """Execute paper trade entry"""
        side = 'long' if signal == 'buy' else 'short'
        position_value = quantity * price
        fees = position_value * 0.0002  # MEXC fee

        # Create position
        self.positions[symbol] = {
            'symbol': symbol,
            'side': side,
            'entry_price': price,
            'current_price': price,
            'quantity': quantity,
            'size': position_value,
            'fees': fees,
            'entry_time': datetime.now(),
            'pnl': 0,
            'pnl_pct': 0,
            'validation': validation
        }

        self.cash -= (position_value + fees)
        self.stats['trades_today'] += 1
        self.stats['total_trades'] += 1
        self.stats['last_trade_time'] = datetime.now()

        # Log trade
        self.logger.info(f"✅ OPENED {side.upper()} {symbol} | "
                        f"Price: ${price:.2f} | Qty: {quantity:.6f} | "
                        f"Size: ${position_value:.2f} | Mode: PAPER")

        # Save to database
        self.db.save_trade({
            'timestamp': datetime.now(),
            'symbol': symbol,
            'side': side,
            'action': 'open',
            'quantity': quantity,
            'price': price,
            'fees': fees,
            'portfolio_value': self._get_portfolio_value(),
            'strategy': 'DeepSeek AI',
            'signal_data': validation
        })

        # Send notification
        self.notifier.send_trade_notification(
            symbol=symbol,
            action='OPEN',
            side=side,
            price=price,
            quantity=quantity,
            mode='PAPER'
        )

    def _execute_live_entry(self, symbol: str, signal: str, quantity: float,
                           price: float, validation: Dict):
        """Execute live trade entry"""
        try:
            order_side = 'buy' if signal == 'buy' else 'sell'

            self.logger.info(f"Placing LIVE order: {order_side.upper()} {quantity:.6f} {symbol}")

            order = self.exchange.create_order(
                symbol=symbol,
                order_type='market',
                side=order_side,
                amount=quantity
            )

            if order and order.get('status') in ['filled', 'closed']:
                actual_price = order.get('price', price)
                actual_quantity = order.get('filled', quantity)
                fees = order.get('fee', {}).get('cost', 0)

                side = 'long' if signal == 'buy' else 'short'
                position_value = actual_quantity * actual_price

                # Create position
                self.positions[symbol] = {
                    'symbol': symbol,
                    'side': side,
                    'entry_price': actual_price,
                    'current_price': actual_price,
                    'quantity': actual_quantity,
                    'size': position_value,
                    'fees': fees,
                    'entry_time': datetime.now(),
                    'pnl': 0,
                    'pnl_pct': 0,
                    'order_id': order.get('id'),
                    'validation': validation
                }

                self.cash -= (position_value + fees)
                self.stats['trades_today'] += 1
                self.stats['total_trades'] += 1
                self.stats['last_trade_time'] = datetime.now()

                # Log trade
                self.logger.info(f"✅ OPENED {side.upper()} {symbol} | "
                                f"Price: ${actual_price:.2f} | Qty: {actual_quantity:.6f} | "
                                f"Size: ${position_value:.2f} | Order: {order.get('id')} | Mode: LIVE")

                # Save to database
                self.db.save_trade({
                    'timestamp': datetime.now(),
                    'symbol': symbol,
                    'side': side,
                    'action': 'open',
                    'quantity': actual_quantity,
                    'price': actual_price,
                    'fees': fees,
                    'portfolio_value': self._get_portfolio_value(),
                    'strategy': 'DeepSeek AI',
                    'signal_data': validation
                })

                # Send notification
                self.notifier.send_trade_notification(
                    symbol=symbol,
                    action='OPEN',
                    side=side,
                    price=actual_price,
                    quantity=actual_quantity,
                    mode='LIVE'
                )

            else:
                self.logger.error(f"Order not filled: {order}")

        except Exception as e:
            self.logger.error(f"Error placing live order: {e}")
            self.notifier.send_error_notification(f"Live order error: {e}")

    def _close_position(self, symbol: str, price: float, reason: str):
        """
        Close an open position

        Args:
            symbol: Trading pair
            price: Close price
            reason: Reason for closing
        """
        if symbol not in self.positions:
            return

        position = self.positions[symbol]
        mode = self.config.get('mode', 'paper')

        if mode == 'paper':
            self._close_paper_position(symbol, price, reason)
        elif mode == 'live':
            self._close_live_position(symbol, price, reason)

    def _close_paper_position(self, symbol: str, price: float, reason: str):
        """Close paper position"""
        position = self.positions[symbol]
        side = position['side']
        quantity = position['quantity']
        entry_price = position['entry_price']

        # Calculate PnL
        if side == 'long':
            pnl = quantity * (price - entry_price)
        else:
            pnl = quantity * (entry_price - price)

        fees = price * quantity * 0.0002
        pnl -= fees + position['fees']

        # Update cash
        close_value = quantity * price
        self.cash += close_value - fees

        # Update stats
        self.stats['daily_pnl'] += pnl
        if pnl > 0:
            self.stats['winning_trades'] += 1
            self.stats['consecutive_losses'] = 0
        else:
            self.stats['losing_trades'] += 1
            self.stats['consecutive_losses'] += 1

        # Calculate hold time
        hold_time = datetime.now() - position['entry_time']
        hold_hours = hold_time.total_seconds() / 3600

        # Log trade
        pnl_pct = (pnl / position['size']) * 100
        self.logger.info(f"❌ CLOSED {side.upper()} {symbol} | "
                        f"Entry: ${entry_price:.2f} | Exit: ${price:.2f} | "
                        f"PnL: ${pnl:.2f} ({pnl_pct:+.2f}%) | "
                        f"Hold: {hold_hours:.1f}h | Reason: {reason} | Mode: PAPER")

        # Save to database
        self.db.save_trade({
            'timestamp': datetime.now(),
            'symbol': symbol,
            'side': side,
            'action': 'close',
            'quantity': quantity,
            'price': price,
            'fees': fees,
            'pnl': pnl,
            'portfolio_value': self._get_portfolio_value(),
            'strategy': 'DeepSeek AI',
            'signal_data': {'reason': reason, 'hold_hours': hold_hours}
        })

        # Send notification
        self.notifier.send_trade_notification(
            symbol=symbol,
            action='CLOSE',
            side=side,
            price=price,
            quantity=quantity,
            pnl=pnl,
            pnl_pct=pnl_pct,
            mode='PAPER'
        )

        # Remove position
        del self.positions[symbol]

    def _close_live_position(self, symbol: str, price: float, reason: str):
        """Close live position"""
        try:
            position = self.positions[symbol]
            side = position['side']
            quantity = position['quantity']

            order_side = 'sell' if side == 'long' else 'buy'

            self.logger.info(f"Placing LIVE close order: {order_side.upper()} {quantity:.6f} {symbol}")

            order = self.exchange.create_order(
                symbol=symbol,
                order_type='market',
                side=order_side,
                amount=quantity
            )

            if order and order.get('status') in ['filled', 'closed']:
                actual_price = order.get('price', price)
                fees = order.get('fee', {}).get('cost', 0)
                entry_price = position['entry_price']

                # Calculate PnL
                if side == 'long':
                    pnl = quantity * (actual_price - entry_price)
                else:
                    pnl = quantity * (entry_price - actual_price)

                pnl -= fees + position['fees']

                # Update cash
                close_value = quantity * actual_price
                self.cash += close_value - fees

                # Update stats
                self.stats['daily_pnl'] += pnl
                if pnl > 0:
                    self.stats['winning_trades'] += 1
                    self.stats['consecutive_losses'] = 0
                else:
                    self.stats['losing_trades'] += 1
                    self.stats['consecutive_losses'] += 1

                # Calculate hold time
                hold_time = datetime.now() - position['entry_time']
                hold_hours = hold_time.total_seconds() / 3600

                # Log trade
                pnl_pct = (pnl / position['size']) * 100
                self.logger.info(f"❌ CLOSED {side.upper()} {symbol} | "
                                f"Entry: ${entry_price:.2f} | Exit: ${actual_price:.2f} | "
                                f"PnL: ${pnl:.2f} ({pnl_pct:+.2f}%) | "
                                f"Hold: {hold_hours:.1f}h | Order: {order.get('id')} | "
                                f"Reason: {reason} | Mode: LIVE")

                # Save to database
                self.db.save_trade({
                    'timestamp': datetime.now(),
                    'symbol': symbol,
                    'side': side,
                    'action': 'close',
                    'quantity': quantity,
                    'price': actual_price,
                    'fees': fees,
                    'pnl': pnl,
                    'portfolio_value': self._get_portfolio_value(),
                    'strategy': 'DeepSeek AI',
                    'signal_data': {'reason': reason, 'hold_hours': hold_hours}
                })

                # Send notification
                self.notifier.send_trade_notification(
                    symbol=symbol,
                    action='CLOSE',
                    side=side,
                    price=actual_price,
                    quantity=quantity,
                    pnl=pnl,
                    pnl_pct=pnl_pct,
                    mode='LIVE'
                )

                # Remove position
                del self.positions[symbol]

        except Exception as e:
            self.logger.error(f"Error closing live position: {e}")
            self.notifier.send_error_notification(f"Close position error: {e}")

    def _update_trailing_stop(self, symbol: str, current_price: float):
        """Update trailing stop for position"""
        if symbol not in self.positions:
            return

        position = self.positions[symbol]
        trailing_pct = self.risk_config.get('trailing_stop_pct', 0.015)

        if position['side'] == 'long':
            # Update trailing stop if price moved up
            new_stop = current_price * (1 - trailing_pct)
            if 'trailing_stop_price' not in position:
                position['trailing_stop_price'] = new_stop
            elif new_stop > position['trailing_stop_price']:
                position['trailing_stop_price'] = new_stop
                self.logger.debug(f"Updated trailing stop for {symbol}: ${new_stop:.2f}")
        else:
            # Short position
            new_stop = current_price * (1 + trailing_pct)
            if 'trailing_stop_price' not in position:
                position['trailing_stop_price'] = new_stop
            elif new_stop < position['trailing_stop_price']:
                position['trailing_stop_price'] = new_stop
                self.logger.debug(f"Updated trailing stop for {symbol}: ${new_stop:.2f}")

    def _calculate_indicators(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate technical indicators"""
        indicators = {}

        # Trend indicators
        indicators['SMA_20'] = Indicators.sma(data['close'], 20).iloc[-1]
        indicators['SMA_50'] = Indicators.sma(data['close'], 50).iloc[-1] if len(data) >= 50 else None
        indicators['EMA_12'] = Indicators.ema(data['close'], 12).iloc[-1]
        indicators['EMA_26'] = Indicators.ema(data['close'], 26).iloc[-1]

        # RSI
        indicators['RSI'] = Indicators.rsi(data['close'], 14).iloc[-1]

        # MACD
        macd_line, signal_line, histogram = Indicators.macd(data['close'])
        indicators['MACD'] = macd_line.iloc[-1]
        indicators['MACD_Signal'] = signal_line.iloc[-1]
        indicators['MACD_Histogram'] = histogram.iloc[-1]

        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = Indicators.bollinger_bands(data['close'], 20, 2.0)
        indicators['BB_Upper'] = bb_upper.iloc[-1]
        indicators['BB_Middle'] = bb_middle.iloc[-1]
        indicators['BB_Lower'] = bb_lower.iloc[-1]

        # Volume
        indicators['Volume'] = data['volume'].iloc[-1]
        indicators['Volume_SMA'] = data['volume'].rolling(20).mean().iloc[-1]

        return indicators

    def _update_market_data(self, symbol: str):
        """Update market data for symbol"""
        try:
            # Fetch OHLCV data
            data = self.exchange.get_ohlcv(symbol, '1h', limit=200)

            if data is not None and len(data) > 0:
                self.data_buffer[symbol] = data
            else:
                self.logger.warning(f"No data received for {symbol}")

        except Exception as e:
            self.logger.error(f"Error updating market data for {symbol}: {e}")
            self.stats['api_errors'] += 1

    def _can_open_position(self) -> bool:
        """Check if we can open a new position"""
        # Check daily trade limit
        if self.stats['trades_today'] >= self.max_daily_trades:
            return False

        # Check daily loss limit
        if self.stats['daily_pnl'] <= -self.max_daily_loss:
            self.logger.warning("Daily loss limit reached")
            return False

        # Check consecutive losses
        max_consecutive = self.emergency_stop_config.get('max_consecutive_losses', 5)
        if self.stats['consecutive_losses'] >= max_consecutive:
            self.logger.warning(f"Max consecutive losses reached: {self.stats['consecutive_losses']}")
            return False

        # Check cash available
        if self.cash < self.max_position_size:
            self.logger.debug(f"Insufficient cash: ${self.cash:.2f} < ${self.max_position_size:.2f}")
            return False

        return True

    def _check_emergency_stop(self) -> bool:
        """Check if emergency stop conditions are met"""
        if not self.emergency_stop_config.get('enabled', True):
            return False

        # Check consecutive losses
        max_consecutive = self.emergency_stop_config.get('max_consecutive_losses', 5)
        if self.stats['consecutive_losses'] >= max_consecutive:
            self.logger.critical(f"Emergency stop: {self.stats['consecutive_losses']} consecutive losses")
            return True

        # Check circuit breaker loss
        portfolio_value = self._get_portfolio_value()
        loss_pct = ((self.initial_capital - portfolio_value) / self.initial_capital) * 100
        max_loss_pct = self.emergency_stop_config.get('circuit_breaker_loss_pct', 0.10) * 100

        if loss_pct >= max_loss_pct:
            self.logger.critical(f"Emergency stop: Portfolio loss {loss_pct:.2f}% >= {max_loss_pct:.2f}%")
            return True

        # Check API errors
        max_errors = self.emergency_stop_config.get('api_error_threshold', 10)
        if self.stats['api_errors'] >= max_errors:
            self.logger.critical(f"Emergency stop: {self.stats['api_errors']} API errors")
            return True

        return False

    def _get_portfolio_value(self) -> float:
        """Calculate total portfolio value"""
        total = self.cash

        for symbol, position in self.positions.items():
            total += position.get('current_price', position['entry_price']) * position['quantity']

        return total

    def _update_portfolio_metrics(self):
        """Update portfolio metrics in database"""
        portfolio_value = self._get_portfolio_value()

        self.db.save_equity_point(
            timestamp=datetime.now(),
            equity=portfolio_value,
            cash=self.cash,
            positions=len(self.positions)
        )

    def _reset_daily_stats_if_needed(self):
        """Reset daily statistics if new day"""
        now = datetime.now()

        if self.stats.get('last_reset_date') != now.date():
            # Save yesterday's metrics
            if self.stats['trades_today'] > 0:
                self.db.save_daily_metrics({
                    'total_trades': self.stats['trades_today'],
                    'winning_trades': self.stats.get('daily_wins', 0),
                    'losing_trades': self.stats.get('daily_losses', 0),
                    'total_pnl': self.stats['daily_pnl']
                })

            # Reset daily stats
            self.stats['trades_today'] = 0
            self.stats['daily_pnl'] = 0.0
            self.stats['daily_wins'] = 0
            self.stats['daily_losses'] = 0
            self.stats['last_reset_date'] = now.date()
            self.stats['api_errors'] = 0

            self.logger.info(f"Daily stats reset for {now.date()}")

    def _log_status(self):
        """Log current status"""
        portfolio_value = self._get_portfolio_value()
        pnl = portfolio_value - self.initial_capital
        pnl_pct = (pnl / self.initial_capital) * 100

        runtime = datetime.now() - self.stats['start_time']

        self.logger.info("=" * 80)
        self.logger.info("STATUS UPDATE")
        self.logger.info(f"Runtime: {runtime}")
        self.logger.info(f"Portfolio Value: ${portfolio_value:,.2f} ({pnl_pct:+.2f}%)")
        self.logger.info(f"Cash: ${self.cash:,.2f}")
        self.logger.info(f"Open Positions: {len(self.positions)}")
        self.logger.info(f"Today's Trades: {self.stats['trades_today']}")
        self.logger.info(f"Today's PnL: ${self.stats['daily_pnl']:,.2f}")
        self.logger.info(f"Total Trades: {self.stats['total_trades']}")
        self.logger.info(f"Win Rate: {self.stats['winning_trades']}/{self.stats['winning_trades'] + self.stats['losing_trades']}")
        self.logger.info("=" * 80)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.should_stop = True

    def _shutdown(self):
        """Shutdown trader gracefully"""
        self.logger.info("Shutting down autonomous trader...")

        # Close all open positions
        for symbol in list(self.positions.keys()):
            try:
                data = self.data_buffer.get(symbol)
                if data is not None:
                    current_price = data['close'].iloc[-1]
                    self._close_position(symbol, current_price, "Shutdown")
            except Exception as e:
                self.logger.error(f"Error closing position {symbol} during shutdown: {e}")

        # Final metrics
        portfolio_value = self._get_portfolio_value()
        total_return = ((portfolio_value - self.initial_capital) / self.initial_capital) * 100

        self.logger.info("=" * 80)
        self.logger.info("FINAL STATISTICS")
        self.logger.info("=" * 80)
        self.logger.info(f"Initial Capital: ${self.initial_capital:,.2f}")
        self.logger.info(f"Final Portfolio Value: ${portfolio_value:,.2f}")
        self.logger.info(f"Total Return: {total_return:+.2f}%")
        self.logger.info(f"Total Trades: {self.stats['total_trades']}")
        self.logger.info(f"Winning Trades: {self.stats['winning_trades']}")
        self.logger.info(f"Losing Trades: {self.stats['losing_trades']}")
        if (self.stats['winning_trades'] + self.stats['losing_trades']) > 0:
            win_rate = (self.stats['winning_trades'] / (self.stats['winning_trades'] + self.stats['losing_trades'])) * 100
            self.logger.info(f"Win Rate: {win_rate:.2f}%")
        self.logger.info("=" * 80)

        # Send shutdown notification
        self.notifier.send_shutdown_notification(
            final_value=portfolio_value,
            total_return=total_return,
            total_trades=self.stats['total_trades']
        )

        # Close database
        self.db.close()

        self.logger.info("Autonomous trader shut down successfully")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Autonomous AI Cryptocurrency Trader")
    parser.add_argument('--config', type=str, default='config/autonomous.yml',
                       help='Path to configuration file')
    parser.add_argument('--mode', type=str, choices=['paper', 'live'],
                       help='Trading mode (overrides config)')

    args = parser.parse_args()

    try:
        trader = AutonomousTrader(config_path=args.config)

        # Override mode if specified
        if args.mode:
            trader.config['mode'] = args.mode
            trader.logger.info(f"Mode overridden to: {args.mode.upper()}")

        trader.start()

    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
