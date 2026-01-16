"""Claude AI Market Analyzer - AI-powered crypto market analysis"""

import os
from typing import Dict, List, Optional, Any
import pandas as pd
import json
import logging
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class ClaudeMarketAnalyzer:
    """
    AI-powered market analyzer using Claude API

    Provides:
    - Market sentiment analysis
    - Pattern recognition
    - Trade signal validation
    - Risk assessment
    - Market news interpretation
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-sonnet-4-5-20250929"):
        """
        Initialize Claude analyzer

        Args:
            api_key: Anthropic API key
            model: Claude model to use
        """
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("Anthropic API key required. Set ANTHROPIC_API_KEY environment variable.")

        self.client = Anthropic(api_key=self.api_key)
        self.model = model
        self.logger = logging.getLogger(__name__)

    def analyze_market_data(self, symbol: str, data: pd.DataFrame,
                           indicators: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze market data and provide AI-powered insights

        Args:
            symbol: Trading symbol
            data: OHLCV DataFrame
            indicators: Dictionary of calculated indicators

        Returns:
            Analysis results with sentiment, signals, and reasoning
        """
        try:
            # Prepare market summary
            market_summary = self._prepare_market_summary(symbol, data, indicators)

            # Create analysis prompt
            prompt = self._create_analysis_prompt(market_summary)

            self.logger.info(f"Requesting Claude AI analysis for {symbol}...")

            # Get AI analysis
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Parse response
            analysis_text = response.content[0].text
            analysis = self._parse_analysis(analysis_text)

            self.logger.info(f"Claude AI analysis complete for {symbol}")
            return analysis

        except Exception as e:
            self.logger.error(f"Error in Claude analysis: {e}")
            return {
                'success': False,
                'error': str(e),
                'sentiment': 'neutral',
                'confidence': 0
            }

    def validate_trade_signal(self, symbol: str, signal: str,
                             data: pd.DataFrame, reasoning: str) -> Dict[str, Any]:
        """
        Validate a trade signal using AI analysis

        Args:
            symbol: Trading symbol
            signal: Trade signal (buy/sell)
            data: Market data
            reasoning: Strategy reasoning

        Returns:
            Validation result with confidence and suggestions
        """
        try:
            prompt = f"""
You are an expert cryptocurrency trader. A trading algorithm has generated the following signal:

Symbol: {symbol}
Signal: {signal.upper()}
Strategy Reasoning: {reasoning}

Current Market Context:
- Current Price: ${data['close'].iloc[-1]:.2f}
- 24h Change: {((data['close'].iloc[-1] / data['close'].iloc[-24] - 1) * 100):.2f}%
- Volume Trend: {'Increasing' if data['volume'].iloc[-1] > data['volume'].iloc[-10:].mean() else 'Decreasing'}

Please validate this signal and provide:
1. Confidence level (0-100%)
2. Key risks to consider
3. Suggested entry strategy
4. Recommended stop loss level
5. Overall assessment

Format your response as JSON with keys: confidence, risks, entry_strategy, stop_loss, assessment
"""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )

            result_text = response.content[0].text

            # Try to extract JSON, fallback to text parsing
            try:
                # Look for JSON in response
                json_start = result_text.find('{')
                json_end = result_text.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    result = json.loads(result_text[json_start:json_end])
                else:
                    result = self._parse_validation_text(result_text)
            except:
                result = self._parse_validation_text(result_text)

            self.logger.info(f"Trade signal validated for {symbol}: {result.get('confidence', 0)}% confidence")
            return result

        except Exception as e:
            self.logger.error(f"Error validating trade signal: {e}")
            return {
                'confidence': 50,
                'risks': ['AI validation unavailable'],
                'entry_strategy': 'Use default strategy',
                'stop_loss': 'Use default stop loss',
                'assessment': f'Error: {str(e)}'
            }

    def assess_portfolio_risk(self, portfolio_data: Dict[str, Any],
                             market_conditions: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess portfolio risk using AI

        Args:
            portfolio_data: Portfolio positions and metrics
            market_conditions: Current market conditions

        Returns:
            Risk assessment with recommendations
        """
        try:
            prompt = f"""
You are a risk management expert for cryptocurrency trading. Analyze this portfolio:

Portfolio Overview:
- Total Value: ${portfolio_data.get('total_value', 0):,.2f}
- Cash: ${portfolio_data.get('cash', 0):,.2f}
- Open Positions: {portfolio_data.get('positions', 0)}
- Current Drawdown: {portfolio_data.get('drawdown', 0):.2f}%

Market Conditions:
- Volatility: {market_conditions.get('volatility', 'Unknown')}
- Trend: {market_conditions.get('trend', 'Unknown')}
- Market Sentiment: {market_conditions.get('sentiment', 'Unknown')}

Provide a risk assessment with:
1. Overall risk level (Low/Medium/High/Critical)
2. Specific concerns
3. Recommended actions
4. Position sizing suggestions

Format as JSON with keys: risk_level, concerns, actions, position_sizing
"""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )

            result_text = response.content[0].text

            try:
                json_start = result_text.find('{')
                json_end = result_text.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    result = json.loads(result_text[json_start:json_end])
                else:
                    result = self._parse_risk_assessment_text(result_text)
            except:
                result = self._parse_risk_assessment_text(result_text)

            self.logger.info(f"Portfolio risk assessed: {result.get('risk_level', 'Unknown')}")
            return result

        except Exception as e:
            self.logger.error(f"Error assessing portfolio risk: {e}")
            return {
                'risk_level': 'Unknown',
                'concerns': [str(e)],
                'actions': ['Monitor portfolio manually'],
                'position_sizing': 'Use conservative sizing'
            }

    def generate_market_report(self, symbol: str, data: pd.DataFrame,
                              performance: Dict[str, Any]) -> str:
        """
        Generate a comprehensive market report

        Args:
            symbol: Trading symbol
            data: Market data
            performance: Trading performance metrics

        Returns:
            Formatted market report
        """
        try:
            prompt = f"""
Generate a professional cryptocurrency trading report for {symbol}.

Market Data (Last 24h):
- Current Price: ${data['close'].iloc[-1]:.2f}
- 24h High: ${data['high'].iloc[-24:].max():.2f}
- 24h Low: ${data['low'].iloc[-24:].min():.2f}
- 24h Volume: {data['volume'].iloc[-24:].sum():,.0f}
- Price Change: {((data['close'].iloc[-1] / data['close'].iloc[-24] - 1) * 100):.2f}%

Trading Performance:
- Total Trades: {performance.get('total_trades', 0)}
- Win Rate: {performance.get('win_rate', 0):.1f}%
- Profit Factor: {performance.get('profit_factor', 0):.2f}
- Total Return: {performance.get('total_return', 0):.2f}%

Create a concise report with:
1. Market Summary
2. Technical Analysis
3. Trading Performance Review
4. Recommendations for Tomorrow

Keep it professional and actionable.
"""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            report = response.content[0].text
            self.logger.info(f"Market report generated for {symbol}")
            return report

        except Exception as e:
            self.logger.error(f"Error generating market report: {e}")
            return f"Error generating report: {str(e)}"

    def _prepare_market_summary(self, symbol: str, data: pd.DataFrame,
                               indicators: Dict[str, Any]) -> str:
        """Prepare market data summary for analysis"""
        latest = data.iloc[-1]
        prev = data.iloc[-2]

        summary = f"""
Symbol: {symbol}

Price Action:
- Current: ${latest['close']:.2f}
- Change: {((latest['close'] / prev['close'] - 1) * 100):+.2f}%
- High: ${latest['high']:.2f}
- Low: ${latest['low']:.2f}
- Volume: {latest['volume']:,.0f}

Technical Indicators:
"""
        for name, value in indicators.items():
            if isinstance(value, (int, float)):
                summary += f"- {name}: {value:.2f}\n"
            else:
                summary += f"- {name}: {value}\n"

        # Recent trend
        if len(data) >= 20:
            sma_20 = data['close'].rolling(20).mean().iloc[-1]
            trend = "Uptrend" if latest['close'] > sma_20 else "Downtrend"
            summary += f"\nTrend (20-period): {trend}\n"

        return summary

    def _create_analysis_prompt(self, market_summary: str) -> str:
        """Create analysis prompt for Claude"""
        return f"""
You are an expert cryptocurrency market analyst. Analyze this market data and provide insights:

{market_summary}

Provide your analysis in JSON format with the following structure:
{{
    "sentiment": "bullish/bearish/neutral",
    "confidence": 0-100,
    "key_points": ["point1", "point2", ...],
    "signals": {{
        "buy_signal": true/false,
        "sell_signal": true/false,
        "hold": true/false
    }},
    "risk_factors": ["factor1", "factor2", ...],
    "outlook": "short summary of market outlook",
    "suggested_action": "specific recommendation"
}}

Focus on actionable insights for trading decisions.
"""

    def _parse_analysis(self, text: str) -> Dict[str, Any]:
        """Parse Claude's analysis response"""
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
                    'confidence': 50,
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
        if 'bullish' in text_lower:
            return 'bullish'
        elif 'bearish' in text_lower:
            return 'bearish'
        else:
            return 'neutral'

    def _parse_validation_text(self, text: str) -> Dict[str, Any]:
        """Parse validation response from text"""
        return {
            'confidence': 50,
            'risks': ['See full analysis'],
            'entry_strategy': 'Use default strategy',
            'stop_loss': 'Use default stop loss',
            'assessment': text[:500]
        }

    def _parse_risk_assessment_text(self, text: str) -> Dict[str, Any]:
        """Parse risk assessment from text"""
        text_lower = text.lower()

        if 'critical' in text_lower or 'high risk' in text_lower:
            risk_level = 'High'
        elif 'medium' in text_lower or 'moderate' in text_lower:
            risk_level = 'Medium'
        else:
            risk_level = 'Low'

        return {
            'risk_level': risk_level,
            'concerns': ['See full assessment'],
            'actions': ['Review full AI analysis'],
            'position_sizing': 'Conservative',
            'full_assessment': text[:500]
        }
