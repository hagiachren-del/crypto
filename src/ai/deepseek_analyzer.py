"""DeepSeek AI Market Analyzer - Advanced AI-powered crypto market analysis

This analyzer uses DeepSeek AI for intelligent market analysis with advanced
multi-timeframe analysis, pattern recognition, and risk assessment.
"""

import os
from typing import Dict, List, Optional, Any
import pandas as pd
import json
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)


class DeepSeekMarketAnalyzer:
    """
    AI-powered market analyzer using DeepSeek API

    Features:
    - Advanced multi-timeframe analysis
    - Pattern recognition and trend analysis
    - Intelligent trade signal validation
    - Comprehensive risk assessment
    - Market sentiment analysis
    - Volume profile analysis
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "deepseek-chat"):
        """
        Initialize DeepSeek analyzer

        Args:
            api_key: DeepSeek API key
            model: DeepSeek model to use (deepseek-chat or deepseek-coder)
        """
        self.api_key = api_key or os.getenv('DEEPSEEK_API_KEY')
        if not self.api_key:
            raise ValueError("DeepSeek API key required. Set DEEPSEEK_API_KEY environment variable.")

        # DeepSeek uses OpenAI-compatible API
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com/v1"
        )
        self.model = model
        self.logger = logging.getLogger(__name__)

        self.logger.info(f"DeepSeek AI Analyzer initialized with model: {model}")

    def analyze_market_data(self, symbol: str, data: pd.DataFrame,
                           indicators: Dict[str, Any],
                           multi_timeframe: bool = True) -> Dict[str, Any]:
        """
        Perform comprehensive market analysis using DeepSeek AI

        Args:
            symbol: Trading symbol
            data: OHLCV DataFrame
            indicators: Dictionary of calculated indicators
            multi_timeframe: Enable multi-timeframe analysis

        Returns:
            Comprehensive analysis with sentiment, signals, and reasoning
        """
        try:
            # Prepare comprehensive market summary
            market_summary = self._prepare_advanced_market_summary(
                symbol, data, indicators, multi_timeframe
            )

            # Create advanced analysis prompt
            prompt = self._create_advanced_analysis_prompt(market_summary)

            self.logger.info(f"Requesting DeepSeek AI analysis for {symbol}...")

            # Get AI analysis
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "system",
                    "content": self._get_system_prompt()
                }, {
                    "role": "user",
                    "content": prompt
                }],
                max_tokens=2500,
                temperature=0.7,
                top_p=0.95
            )

            # Parse response
            analysis_text = response.choices[0].message.content
            analysis = self._parse_analysis(analysis_text)

            self.logger.info(f"DeepSeek AI analysis complete for {symbol} - Confidence: {analysis.get('confidence', 0)}%")
            return analysis

        except Exception as e:
            self.logger.error(f"Error in DeepSeek analysis: {e}")
            return {
                'success': False,
                'error': str(e),
                'sentiment': 'neutral',
                'confidence': 0
            }

    def validate_trade_signal(self, symbol: str, signal: str,
                             data: pd.DataFrame, indicators: Dict[str, Any],
                             reasoning: str) -> Dict[str, Any]:
        """
        Validate trade signal with advanced AI analysis

        Args:
            symbol: Trading symbol
            signal: Trade signal (buy/sell)
            data: Market data
            indicators: Technical indicators
            reasoning: Strategy reasoning

        Returns:
            Validation result with confidence, risk assessment, and strategy
        """
        try:
            # Calculate advanced metrics
            volatility = data['close'].pct_change().std() * 100
            volume_trend = "Increasing" if data['volume'].iloc[-3:].mean() > data['volume'].iloc[-10:-3].mean() else "Decreasing"
            price_trend = "Bullish" if data['close'].iloc[-1] > data['close'].iloc[-20:].mean() else "Bearish"

            # Get recent price action
            recent_candles = []
            for i in range(-5, 0):
                candle = data.iloc[i]
                candle_type = "Bullish" if candle['close'] > candle['open'] else "Bearish"
                body_size = abs(candle['close'] - candle['open'])
                wick_size = candle['high'] - candle['low']
                recent_candles.append(f"{candle_type} (Body: ${body_size:.2f}, Range: ${wick_size:.2f})")

            prompt = f"""
You are an expert cryptocurrency trader and technical analyst. Validate this trade signal with rigorous analysis.

TRADE SIGNAL:
- Symbol: {symbol}
- Signal: {signal.upper()}
- Strategy Reasoning: {reasoning}

CURRENT MARKET CONDITIONS:
- Current Price: ${data['close'].iloc[-1]:.2f}
- 24h Change: {((data['close'].iloc[-1] / data['close'].iloc[-24] - 1) * 100):.2f}%
- Price Trend: {price_trend}
- Volatility: {volatility:.2f}%
- Volume Trend: {volume_trend}

TECHNICAL INDICATORS:
{self._format_indicators(indicators)}

RECENT PRICE ACTION (Last 5 candles):
{chr(10).join(f"  {i+1}. {candle}" for i, candle in enumerate(recent_candles))}

SUPPORT/RESISTANCE LEVELS:
- 20-period SMA: ${data['close'].rolling(20).mean().iloc[-1]:.2f}
- 50-period SMA: ${data['close'].rolling(50).mean().iloc[-1] if len(data) >= 50 else 0:.2f}
- Recent High: ${data['high'].iloc[-20:].max():.2f}
- Recent Low: ${data['low'].iloc[-20:].min():.2f}

VALIDATION REQUIREMENTS:
1. Analyze all technical indicators for confluence
2. Assess market context and trend alignment
3. Identify key risk factors and potential pitfalls
4. Determine optimal entry timing and strategy
5. Calculate precise stop loss and take profit levels
6. Provide confidence score (0-100%)

Respond in JSON format:
{{
    "confidence": 0-100,
    "validation_status": "approved/rejected/conditional",
    "key_strengths": ["strength1", "strength2", ...],
    "key_risks": ["risk1", "risk2", ...],
    "entry_strategy": {{
        "timing": "immediate/wait_for_pullback/wait_for_breakout",
        "optimal_entry": price_level,
        "reasoning": "explanation"
    }},
    "risk_management": {{
        "stop_loss": price_level,
        "stop_loss_pct": percentage,
        "take_profit": price_level,
        "take_profit_pct": percentage,
        "position_size_recommendation": "small/medium/large"
    }},
    "market_context": {{
        "trend_alignment": "aligned/neutral/conflicting",
        "momentum": "strong/moderate/weak",
        "volume_confirmation": true/false
    }},
    "overall_assessment": "detailed assessment"
}}
"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "system",
                    "content": "You are an expert cryptocurrency trader with 10+ years of experience. Provide rigorous, data-driven analysis."
                }, {
                    "role": "user",
                    "content": prompt
                }],
                max_tokens=2000,
                temperature=0.5
            )

            result_text = response.choices[0].message.content

            # Try to extract JSON
            try:
                json_start = result_text.find('{')
                json_end = result_text.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    result = json.loads(result_text[json_start:json_end])
                else:
                    result = self._parse_validation_text(result_text)
            except:
                result = self._parse_validation_text(result_text)

            self.logger.info(f"Signal validated for {symbol}: {result.get('confidence', 0)}% confidence, Status: {result.get('validation_status', 'unknown')}")
            return result

        except Exception as e:
            self.logger.error(f"Error validating trade signal: {e}")
            return {
                'confidence': 50,
                'validation_status': 'error',
                'key_risks': ['AI validation unavailable'],
                'entry_strategy': {'timing': 'use_default'},
                'risk_management': {'stop_loss_pct': 2.0, 'take_profit_pct': 4.0},
                'overall_assessment': f'Error: {str(e)}'
            }

    def assess_portfolio_risk(self, portfolio_data: Dict[str, Any],
                             market_conditions: Dict[str, Any],
                             open_positions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Comprehensive portfolio risk assessment

        Args:
            portfolio_data: Portfolio positions and metrics
            market_conditions: Current market conditions
            open_positions: List of open positions

        Returns:
            Risk assessment with actionable recommendations
        """
        try:
            # Format open positions
            positions_summary = []
            for pos in open_positions:
                pnl_pct = ((pos.get('current_price', 0) - pos.get('entry_price', 1)) / pos.get('entry_price', 1)) * 100
                positions_summary.append(
                    f"  - {pos.get('symbol')}: {pos.get('side')} ${pos.get('size', 0):.2f} @ ${pos.get('entry_price', 0):.2f} (PnL: {pnl_pct:.2f}%)"
                )

            prompt = f"""
You are a risk management expert specializing in cryptocurrency portfolio management. Perform a comprehensive risk assessment.

PORTFOLIO OVERVIEW:
- Total Value: ${portfolio_data.get('total_value', 0):,.2f}
- Cash Available: ${portfolio_data.get('cash', 0):,.2f} ({(portfolio_data.get('cash', 0) / portfolio_data.get('total_value', 1) * 100):.1f}%)
- Open Positions: {len(open_positions)}
- Current Drawdown: {portfolio_data.get('drawdown', 0):.2f}%
- Total Exposure: {portfolio_data.get('exposure_pct', 0):.2f}%

OPEN POSITIONS:
{chr(10).join(positions_summary) if positions_summary else "  No open positions"}

MARKET CONDITIONS:
- Overall Volatility: {market_conditions.get('volatility', 'Unknown')}
- Market Trend: {market_conditions.get('trend', 'Unknown')}
- Market Sentiment: {market_conditions.get('sentiment', 'Unknown')}
- Fear & Greed Index: {market_conditions.get('fear_greed', 'Unknown')}

RISK ANALYSIS REQUIREMENTS:
1. Calculate overall portfolio risk score (0-100)
2. Identify concentration risks
3. Assess correlation between positions
4. Evaluate drawdown risk
5. Determine position sizing adequacy
6. Provide specific hedging recommendations if needed
7. Suggest portfolio rebalancing actions

Respond in JSON format:
{{
    "risk_score": 0-100,
    "risk_level": "low/moderate/high/critical",
    "specific_concerns": [
        {{"concern": "description", "severity": "low/medium/high", "action": "recommended action"}}
    ],
    "portfolio_health": {{
        "diversification": "poor/fair/good/excellent",
        "position_sizing": "appropriate/aggressive/conservative",
        "cash_reserves": "adequate/low/excessive"
    }},
    "immediate_actions": ["action1", "action2", ...],
    "recommendations": {{
        "reduce_exposure_in": ["symbol1", ...],
        "increase_exposure_in": ["symbol1", ...],
        "hedge_positions": ["symbol1", ...],
        "close_positions": ["symbol1", ...]
    }},
    "max_new_position_size": dollar_amount,
    "overall_assessment": "detailed assessment"
}}
"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "system",
                    "content": "You are an expert risk management advisor. Provide conservative, data-driven risk assessments."
                }, {
                    "role": "user",
                    "content": prompt
                }],
                max_tokens=2000,
                temperature=0.4
            )

            result_text = response.choices[0].message.content

            try:
                json_start = result_text.find('{')
                json_end = result_text.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    result = json.loads(result_text[json_start:json_end])
                else:
                    result = self._parse_risk_assessment_text(result_text)
            except:
                result = self._parse_risk_assessment_text(result_text)

            self.logger.info(f"Portfolio risk assessed: {result.get('risk_level', 'Unknown')} (Score: {result.get('risk_score', 0)})")
            return result

        except Exception as e:
            self.logger.error(f"Error assessing portfolio risk: {e}")
            return {
                'risk_score': 50,
                'risk_level': 'Unknown',
                'specific_concerns': [{'concern': str(e), 'severity': 'high', 'action': 'Monitor manually'}],
                'immediate_actions': ['Monitor portfolio manually'],
                'overall_assessment': f'Error: {str(e)}'
            }

    def generate_market_report(self, symbol: str, data: pd.DataFrame,
                              performance: Dict[str, Any],
                              recent_trades: List[Dict[str, Any]]) -> str:
        """
        Generate comprehensive market report

        Args:
            symbol: Trading symbol
            data: Market data
            performance: Trading performance metrics
            recent_trades: Recent trade history

        Returns:
            Formatted markdown report
        """
        try:
            # Calculate advanced metrics
            volatility = data['close'].pct_change().std() * np.sqrt(24) * 100

            prompt = f"""
Generate a professional cryptocurrency trading report for {symbol}.

MARKET DATA (Last 24 Hours):
- Current Price: ${data['close'].iloc[-1]:.2f}
- 24h High: ${data['high'].iloc[-24:].max():.2f}
- 24h Low: ${data['low'].iloc[-24:].min():.2f}
- 24h Volume: ${data['volume'].iloc[-24:].sum():,.0f}
- Price Change: {((data['close'].iloc[-1] / data['close'].iloc[-24] - 1) * 100):.2f}%
- Volatility: {volatility:.2f}%

TRADING PERFORMANCE:
- Total Trades: {performance.get('total_trades', 0)}
- Winning Trades: {performance.get('winning_trades', 0)}
- Losing Trades: {performance.get('losing_trades', 0)}
- Win Rate: {performance.get('win_rate', 0):.1f}%
- Profit Factor: {performance.get('profit_factor', 0):.2f}
- Total Return: {performance.get('total_return', 0):.2f}%
- Sharpe Ratio: {performance.get('sharpe_ratio', 0):.2f}
- Max Drawdown: {performance.get('max_drawdown', 0):.2f}%

RECENT TRADES: {len(recent_trades)}

Create a comprehensive report with:
1. Executive Summary (2-3 sentences)
2. Market Analysis
   - Price action review
   - Volume and liquidity analysis
   - Key support/resistance levels
   - Trend assessment
3. Technical Indicators Review
   - What indicators are showing strength
   - Warning signals if any
4. Trading Performance Analysis
   - Strategy effectiveness
   - Areas of improvement
   - Risk management review
5. Market Outlook (Next 24-48 hours)
   - Expected scenarios
   - Key levels to watch
   - Potential catalysts
6. Actionable Recommendations
   - Position adjustments
   - Entry/exit strategies
   - Risk management updates

Format in clean markdown. Be specific and actionable.
"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "system",
                    "content": "You are a professional cryptocurrency analyst. Write clear, actionable reports."
                }, {
                    "role": "user",
                    "content": prompt
                }],
                max_tokens=2500,
                temperature=0.7
            )

            report = response.choices[0].message.content
            self.logger.info(f"Market report generated for {symbol}")
            return report

        except Exception as e:
            self.logger.error(f"Error generating market report: {e}")
            return f"# Market Report Error\n\nUnable to generate report: {str(e)}"

    def _get_system_prompt(self) -> str:
        """Get system prompt for DeepSeek"""
        return """You are an elite cryptocurrency trading AI with expertise in:
- Technical analysis and chart pattern recognition
- Multi-timeframe market structure analysis
- Risk management and position sizing
- Market microstructure and order flow
- Sentiment analysis and market psychology
- Quantitative trading strategies

Provide data-driven, actionable insights. Be precise with numbers and specific with recommendations.
Always consider risk management first. Base your analysis on multiple confirming signals."""

    def _prepare_advanced_market_summary(self, symbol: str, data: pd.DataFrame,
                                        indicators: Dict[str, Any],
                                        multi_timeframe: bool) -> str:
        """Prepare comprehensive market summary"""
        latest = data.iloc[-1]
        prev = data.iloc[-2]

        # Calculate advanced metrics
        volatility = data['close'].pct_change().std() * 100
        volume_sma = data['volume'].rolling(20).mean().iloc[-1]
        volume_ratio = latest['volume'] / volume_sma if volume_sma > 0 else 1.0

        summary = f"""
Symbol: {symbol}

PRICE ACTION:
- Current: ${latest['close']:.2f}
- Change: {((latest['close'] / prev['close'] - 1) * 100):+.2f}%
- High: ${latest['high']:.2f}
- Low: ${latest['low']:.2f}
- Range: ${latest['high'] - latest['low']:.2f}
- Volatility: {volatility:.2f}%

VOLUME ANALYSIS:
- Current: {latest['volume']:,.0f}
- 20-period Avg: {volume_sma:,.0f}
- Volume Ratio: {volume_ratio:.2f}x
- Trend: {"Increasing" if data['volume'].iloc[-3:].mean() > volume_sma else "Decreasing"}

TECHNICAL INDICATORS:
"""
        for name, value in indicators.items():
            if isinstance(value, (int, float)):
                summary += f"- {name}: {value:.2f}\n"
            else:
                summary += f"- {name}: {value}\n"

        # Trend analysis
        if len(data) >= 50:
            sma_20 = data['close'].rolling(20).mean().iloc[-1]
            sma_50 = data['close'].rolling(50).mean().iloc[-1]

            summary += f"\nTREND ANALYSIS:\n"
            summary += f"- 20 SMA: ${sma_20:.2f} ({'Above' if latest['close'] > sma_20 else 'Below'})\n"
            summary += f"- 50 SMA: ${sma_50:.2f} ({'Above' if latest['close'] > sma_50 else 'Below'})\n"
            summary += f"- Moving Average Alignment: {'Bullish' if sma_20 > sma_50 else 'Bearish'}\n"

        # Support/Resistance
        recent_high = data['high'].iloc[-20:].max()
        recent_low = data['low'].iloc[-20:].min()
        summary += f"\nSUPPORT/RESISTANCE:\n"
        summary += f"- 20-period High: ${recent_high:.2f}\n"
        summary += f"- 20-period Low: ${recent_low:.2f}\n"

        return summary

    def _create_advanced_analysis_prompt(self, market_summary: str) -> str:
        """Create comprehensive analysis prompt"""
        return f"""
Analyze this cryptocurrency market data and provide expert trading insights:

{market_summary}

Perform comprehensive analysis covering:

1. TREND IDENTIFICATION
   - Primary trend (bullish/bearish/neutral)
   - Trend strength and momentum
   - Key trend levels

2. PATTERN RECOGNITION
   - Chart patterns (if any)
   - Candlestick patterns
   - Price structure

3. INDICATOR CONFLUENCE
   - Which indicators agree/disagree
   - Strength of signals
   - Divergences

4. VOLUME ANALYSIS
   - Volume confirmation
   - Accumulation/distribution
   - Volume patterns

5. MARKET CONTEXT
   - Overall market structure
   - Key support/resistance levels
   - Breakout/breakdown potential

6. TRADING SIGNALS
   - Buy/sell/hold recommendation
   - Entry zones
   - Risk/reward assessment

7. RISK FACTORS
   - Key risks to watch
   - Invalidation levels
   - Market conditions that could change the setup

Provide response in JSON format:
{{
    "sentiment": "bullish/bearish/neutral",
    "confidence": 0-100,
    "trend": {{
        "primary": "uptrend/downtrend/ranging",
        "strength": "strong/moderate/weak",
        "momentum": "accelerating/steady/decelerating"
    }},
    "signals": {{
        "buy_signal": true/false,
        "sell_signal": true/false,
        "hold": true/false,
        "strength": "strong/moderate/weak"
    }},
    "key_levels": {{
        "support": [price1, price2, ...],
        "resistance": [price1, price2, ...]
    }},
    "indicators_confluence": {{
        "bullish_count": number,
        "bearish_count": number,
        "neutral_count": number
    }},
    "risk_factors": ["factor1", "factor2", ...],
    "opportunities": ["opportunity1", "opportunity2", ...],
    "suggested_action": "specific recommendation with entry/exit levels",
    "outlook": "detailed market outlook (2-3 sentences)",
    "key_points": ["point1", "point2", ...]
}}

Be specific, quantitative, and actionable.
"""

    def _format_indicators(self, indicators: Dict[str, Any]) -> str:
        """Format indicators for display"""
        formatted = []
        for name, value in indicators.items():
            if isinstance(value, (int, float)):
                formatted.append(f"  - {name}: {value:.2f}")
            else:
                formatted.append(f"  - {name}: {value}")
        return "\n".join(formatted)

    def _parse_analysis(self, text: str) -> Dict[str, Any]:
        """Parse AI analysis response"""
        try:
            # Try to extract JSON
            json_start = text.find('{')
            json_end = text.rfind('}') + 1

            if json_start != -1 and json_end > json_start:
                result = json.loads(text[json_start:json_end])
                result['success'] = True
                result['raw_analysis'] = text
                return result
            else:
                # Fallback to text parsing
                return {
                    'success': True,
                    'sentiment': self._extract_sentiment(text),
                    'confidence': 60,
                    'raw_analysis': text,
                    'outlook': text[:500]
                }
        except Exception as e:
            self.logger.error(f"Error parsing analysis: {e}")
            return {
                'success': False,
                'error': str(e),
                'raw_analysis': text
            }

    def _extract_sentiment(self, text: str) -> str:
        """Extract sentiment from text"""
        text_lower = text.lower()

        bullish_count = text_lower.count('bullish') + text_lower.count('buy')
        bearish_count = text_lower.count('bearish') + text_lower.count('sell')

        if bullish_count > bearish_count:
            return 'bullish'
        elif bearish_count > bullish_count:
            return 'bearish'
        else:
            return 'neutral'

    def _parse_validation_text(self, text: str) -> Dict[str, Any]:
        """Parse validation response from text"""
        return {
            'confidence': 60,
            'validation_status': 'conditional',
            'key_risks': ['See full analysis'],
            'entry_strategy': {'timing': 'use_default'},
            'risk_management': {'stop_loss_pct': 2.0, 'take_profit_pct': 4.0},
            'overall_assessment': text[:500]
        }

    def _parse_risk_assessment_text(self, text: str) -> Dict[str, Any]:
        """Parse risk assessment from text"""
        text_lower = text.lower()

        if 'critical' in text_lower or 'very high' in text_lower:
            risk_level = 'critical'
            risk_score = 85
        elif 'high' in text_lower:
            risk_level = 'high'
            risk_score = 70
        elif 'moderate' in text_lower or 'medium' in text_lower:
            risk_level = 'moderate'
            risk_score = 50
        else:
            risk_level = 'low'
            risk_score = 30

        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'specific_concerns': [{'concern': 'See full assessment', 'severity': 'medium', 'action': 'Review'}],
            'immediate_actions': ['Review full AI analysis'],
            'overall_assessment': text[:500]
        }


# Add numpy import for volatility calculation
import numpy as np
