"""Production notification system - Email, Telegram, Discord"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
import requests
from datetime import datetime

logger = logging.getLogger(__name__)


class NotificationManager:
    """Manage notifications across multiple channels"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize notification manager

        Args:
            config: Configuration dictionary with notification settings
        """
        self.config = config
        self.email_enabled = config.get('email', {}).get('enabled', False)
        self.telegram_enabled = config.get('telegram', {}).get('enabled', False)
        self.discord_enabled = config.get('discord', {}).get('enabled', False)

    def send_trade_notification(self, trade_data: Dict[str, Any]):
        """
        Send trade notification

        Args:
            trade_data: Trade information
        """
        message = self._format_trade_message(trade_data)

        if self.email_enabled:
            self._send_email("Trade Executed", message)

        if self.telegram_enabled:
            self._send_telegram(message)

        if self.discord_enabled:
            self._send_discord("Trade Executed", message)

    def send_alert(self, alert_type: str, message: str, severity: str = "info"):
        """
        Send alert notification

        Args:
            alert_type: Type of alert
            message: Alert message
            severity: Severity level (info, warning, error, critical)
        """
        formatted_message = f"[{severity.upper()}] {alert_type}\n\n{message}"

        # Send to all enabled channels for critical alerts
        if severity == "critical":
            if self.email_enabled:
                self._send_email(f"CRITICAL: {alert_type}", formatted_message)
            if self.telegram_enabled:
                self._send_telegram(f"🚨 {formatted_message}")
            if self.discord_enabled:
                self._send_discord(f"CRITICAL: {alert_type}", formatted_message)

        # Send to telegram for warnings and errors
        elif severity in ["warning", "error"]:
            if self.telegram_enabled:
                emoji = "⚠️" if severity == "warning" else "❌"
                self._send_telegram(f"{emoji} {formatted_message}")

        # Info messages to telegram only
        else:
            if self.telegram_enabled:
                self._send_telegram(f"ℹ️ {formatted_message}")

    def send_daily_report(self, report_data: Dict[str, Any]):
        """
        Send daily trading report

        Args:
            report_data: Daily report data
        """
        message = self._format_daily_report(report_data)

        if self.email_enabled:
            self._send_email("Daily Trading Report", message, html=True)

        if self.telegram_enabled:
            # Send summary to telegram
            summary = self._format_telegram_summary(report_data)
            self._send_telegram(summary)

    def _send_email(self, subject: str, message: str, html: bool = False):
        """Send email notification"""
        try:
            email_config = self.config.get('email', {})
            smtp_server = email_config.get('smtp_server')
            smtp_port = email_config.get('smtp_port', 587)
            sender = email_config.get('sender')
            password = email_config.get('password')
            recipients = email_config.get('recipients', [])

            if not all([smtp_server, sender, password, recipients]):
                logger.warning("Email configuration incomplete, skipping email notification")
                return

            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"[Crypto Trader] {subject}"
            msg['From'] = sender
            msg['To'] = ', '.join(recipients)

            if html:
                part = MIMEText(message, 'html')
            else:
                part = MIMEText(message, 'plain')

            msg.attach(part)

            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender, password)
                server.sendmail(sender, recipients, msg.as_string())

            logger.info(f"Email notification sent: {subject}")

        except Exception as e:
            logger.error(f"Failed to send email: {e}")

    def _send_telegram(self, message: str):
        """Send Telegram notification"""
        try:
            telegram_config = self.config.get('telegram', {})
            bot_token = telegram_config.get('bot_token')
            chat_id = telegram_config.get('chat_id')

            if not all([bot_token, chat_id]):
                logger.warning("Telegram configuration incomplete")
                return

            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }

            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()

            logger.info("Telegram notification sent")

        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")

    def _send_discord(self, title: str, message: str):
        """Send Discord notification"""
        try:
            discord_config = self.config.get('discord', {})
            webhook_url = discord_config.get('webhook_url')

            if not webhook_url:
                logger.warning("Discord webhook URL not configured")
                return

            data = {
                'embeds': [{
                    'title': title,
                    'description': message,
                    'color': 5814783,  # Blue color
                    'timestamp': datetime.utcnow().isoformat()
                }]
            }

            response = requests.post(webhook_url, json=data, timeout=10)
            response.raise_for_status()

            logger.info("Discord notification sent")

        except Exception as e:
            logger.error(f"Failed to send Discord message: {e}")

    def _format_trade_message(self, trade_data: Dict[str, Any]) -> str:
        """Format trade data into notification message"""
        action = trade_data.get('action', 'TRADE')
        symbol = trade_data.get('symbol', 'UNKNOWN')
        side = trade_data.get('side', '').upper()
        quantity = trade_data.get('quantity', 0)
        price = trade_data.get('price', 0)
        pnl = trade_data.get('pnl')

        message = f"""
{action}: {symbol}
{'='*40}
Side: {side}
Quantity: {quantity:.6f}
Price: ${price:.2f}
"""

        if pnl is not None:
            pnl_emoji = "✅" if pnl > 0 else "❌"
            message += f"PnL: {pnl_emoji} ${pnl:.2f}\n"

        if trade_data.get('reason'):
            message += f"Reason: {trade_data['reason']}\n"

        return message

    def _format_daily_report(self, report_data: Dict[str, Any]) -> str:
        """Format daily report as HTML email"""
        html = f"""
<html>
<body style="font-family: Arial, sans-serif;">
    <h2>Daily Trading Report - {datetime.now().strftime('%Y-%m-%d')}</h2>

    <h3>Performance Summary</h3>
    <table border="1" cellpadding="5" style="border-collapse: collapse;">
        <tr><td><b>Total Trades</b></td><td>{report_data.get('total_trades', 0)}</td></tr>
        <tr><td><b>Win Rate</b></td><td>{report_data.get('win_rate', 0):.1f}%</td></tr>
        <tr><td><b>Total PnL</b></td><td>${report_data.get('total_pnl', 0):.2f}</td></tr>
        <tr><td><b>Return</b></td><td>{report_data.get('return_pct', 0):.2f}%</td></tr>
    </table>

    <h3>Portfolio Status</h3>
    <table border="1" cellpadding="5" style="border-collapse: collapse;">
        <tr><td><b>Equity</b></td><td>${report_data.get('equity', 0):,.2f}</td></tr>
        <tr><td><b>Cash</b></td><td>${report_data.get('cash', 0):,.2f}</td></tr>
        <tr><td><b>Open Positions</b></td><td>{report_data.get('open_positions', 0)}</td></tr>
    </table>

    <p><i>Generated by Crypto Trading Platform</i></p>
</body>
</html>
"""
        return html

    def _format_telegram_summary(self, report_data: Dict[str, Any]) -> str:
        """Format summary for Telegram"""
        return f"""
📊 <b>Daily Trading Report</b>

<b>Performance:</b>
• Trades: {report_data.get('total_trades', 0)}
• Win Rate: {report_data.get('win_rate', 0):.1f}%
• PnL: ${report_data.get('total_pnl', 0):.2f}
• Return: {report_data.get('return_pct', 0):.2f}%

<b>Portfolio:</b>
• Equity: ${report_data.get('equity', 0):,.2f}
• Cash: ${report_data.get('cash', 0):,.2f}
• Positions: {report_data.get('open_positions', 0)}
"""


# Convenience function for quick notifications
def send_quick_alert(message: str, severity: str = "info"):
    """Send a quick alert using environment variables"""
    config = {
        'telegram': {
            'enabled': bool(os.getenv('TELEGRAM_BOT_TOKEN')),
            'bot_token': os.getenv('TELEGRAM_BOT_TOKEN'),
            'chat_id': os.getenv('TELEGRAM_CHAT_ID')
        }
    }

    notifier = NotificationManager(config)
    notifier.send_alert("Alert", message, severity)
