"""Configuration management system"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv


class Config:
    """Configuration loader and manager"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration

        Args:
            config_path: Path to config file (default: config/local.yml)
        """
        load_dotenv()  # Load environment variables

        if config_path is None:
            config_path = "config/local.yml"

        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self._secrets: Dict[str, Any] = {}

        self._load_config()
        self._load_secrets()

    def _load_config(self):
        """Load main configuration file"""
        if not self.config_path.exists():
            # Try default config
            default_path = Path("config/default.yml")
            if default_path.exists():
                self.config_path = default_path
            else:
                raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            self._config = yaml.safe_load(f) or {}

    def _load_secrets(self):
        """Load secrets configuration"""
        secrets_path = Path("config/secrets.yml")
        if secrets_path.exists():
            with open(secrets_path, 'r') as f:
                self._secrets = yaml.safe_load(f) or {}

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value

        Args:
            key: Configuration key (supports nested keys with dots, e.g., 'strategy.params.fast')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def get_secret(self, key: str, default: Any = None) -> Any:
        """
        Get secret value

        Args:
            key: Secret key
            default: Default value if key not found

        Returns:
            Secret value
        """
        # First check environment variables
        env_key = key.upper().replace('.', '_')
        env_value = os.getenv(env_key)
        if env_value is not None:
            return env_value

        # Then check secrets file
        keys = key.split('.')
        value = self._secrets

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    @property
    def mode(self) -> str:
        """Get trading mode (backtest, paper, live)"""
        return self.get('mode', 'backtest')

    @property
    def exchange(self) -> str:
        """Get exchange name"""
        return self.get('exchange', 'binance')

    @property
    def symbols(self) -> list:
        """Get trading symbols"""
        return self.get('symbols', ['BTC/USDT'])

    @property
    def strategy_name(self) -> str:
        """Get strategy name"""
        return self.get('strategy.name', 'sma_cross')

    @property
    def strategy_params(self) -> Dict:
        """Get strategy parameters"""
        return self.get('strategy.params', {})

    @property
    def risk_params(self) -> Dict:
        """Get risk parameters"""
        return self.get('risk', {})

    def __getitem__(self, key: str) -> Any:
        """Allow dict-like access"""
        return self.get(key)

    def __repr__(self) -> str:
        return f"Config(mode={self.mode}, exchange={self.exchange}, strategy={self.strategy_name})"
