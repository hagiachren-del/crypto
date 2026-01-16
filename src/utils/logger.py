"""Production-grade logging system"""

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path
import json
from typing import Optional


class ProductionLogger:
    """Production-ready logging with rotation, formatting, and multiple outputs"""

    def __init__(self, name: str = 'crypto_trader',
                 log_dir: str = 'logs',
                 log_level: str = 'INFO'):
        """
        Initialize production logger

        Args:
            name: Logger name
            log_dir: Directory for log files
            log_level: Logging level
        """
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.log_level = getattr(logging, log_level.upper())
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Setup logger with multiple handlers"""
        logger = logging.getLogger(self.name)
        logger.setLevel(self.log_level)

        # Remove existing handlers
        logger.handlers.clear()

        # Format
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Console handler with color support
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(ColoredFormatter())
        logger.addHandler(console_handler)

        # File handler with rotation (10MB per file, keep 10 files)
        log_file = self.log_dir / f'{self.name}.log'
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Error file handler
        error_log_file = self.log_dir / f'{self.name}_errors.log'
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=10 * 1024 * 1024,
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        logger.addHandler(error_handler)

        # JSON structured logging for production
        json_log_file = self.log_dir / f'{self.name}_structured.json'
        json_handler = logging.handlers.RotatingFileHandler(
            json_log_file,
            maxBytes=10 * 1024 * 1024,
            backupCount=10
        )
        json_handler.setLevel(logging.INFO)
        json_handler.setFormatter(JSONFormatter())
        logger.addHandler(json_handler)

        logger.info(f"Production logger initialized: {self.name}")
        return logger

    def get_logger(self) -> logging.Logger:
        """Get the logger instance"""
        return self.logger


class ColoredFormatter(logging.Formatter):
    """Colored console output formatter"""

    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        record.msg = f"{log_color}{record.msg}{self.RESET}"
        return super().format(record)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""

    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)

        return json.dumps(log_data)


class TradeLogger:
    """Specialized logger for trade events"""

    def __init__(self, log_dir: str = 'logs'):
        """Initialize trade logger"""
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.trade_log_file = self.log_dir / 'trades.jsonl'

    def log_trade(self, trade_data: dict):
        """
        Log a trade event

        Args:
            trade_data: Trade information dictionary
        """
        trade_data['timestamp'] = datetime.utcnow().isoformat()

        with open(self.trade_log_file, 'a') as f:
            f.write(json.dumps(trade_data) + '\n')

    def log_signal(self, signal_data: dict):
        """
        Log a trading signal

        Args:
            signal_data: Signal information dictionary
        """
        signal_file = self.log_dir / 'signals.jsonl'
        signal_data['timestamp'] = datetime.utcnow().isoformat()

        with open(signal_file, 'a') as f:
            f.write(json.dumps(signal_data) + '\n')

    def log_error(self, error_data: dict):
        """
        Log a trading error

        Args:
            error_data: Error information dictionary
        """
        error_file = self.log_dir / 'trading_errors.jsonl'
        error_data['timestamp'] = datetime.utcnow().isoformat()

        with open(error_file, 'a') as f:
            f.write(json.dumps(error_data) + '\n')


def setup_production_logging(app_name: str = 'crypto_trader',
                            log_level: str = 'INFO') -> logging.Logger:
    """
    Setup production logging for the application

    Args:
        app_name: Application name
        log_level: Logging level

    Returns:
        Configured logger
    """
    prod_logger = ProductionLogger(app_name, log_level=log_level)
    return prod_logger.get_logger()
