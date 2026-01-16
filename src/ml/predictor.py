"""Machine Learning-based price prediction"""

import numpy as np
import pandas as pd
from typing import Optional, Tuple
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')


class PricePredictor:
    """
    ML-based price prediction using multiple models

    Features:
    - Multiple ML models (Random Forest, Gradient Boosting)
    - Feature engineering from technical indicators
    - Model ensemble for robust predictions
    """

    def __init__(self, model_type: str = 'random_forest'):
        """
        Initialize price predictor

        Args:
            model_type: Type of model ('random_forest', 'gradient_boosting', 'ensemble')
        """
        self.model_type = model_type
        self.scaler = StandardScaler()
        self.model = None
        self.is_trained = False

        # Initialize models
        if model_type == 'random_forest':
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
        elif model_type == 'gradient_boosting':
            self.model = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
        elif model_type == 'ensemble':
            self.rf_model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
            self.gb_model = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )

    def create_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Create features from OHLCV data

        Args:
            data: DataFrame with OHLCV data

        Returns:
            DataFrame with engineered features
        """
        df = data.copy()

        # Price features
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))

        # Moving averages
        for period in [5, 10, 20, 50]:
            df[f'sma_{period}'] = df['close'].rolling(window=period).mean()
            df[f'ema_{period}'] = df['close'].ewm(span=period, adjust=False).mean()

        # Price momentum
        df['momentum_1'] = df['close'] - df['close'].shift(1)
        df['momentum_5'] = df['close'] - df['close'].shift(5)
        df['momentum_10'] = df['close'] - df['close'].shift(10)

        # Volatility
        df['volatility_5'] = df['returns'].rolling(window=5).std()
        df['volatility_20'] = df['returns'].rolling(window=20).std()

        # Volume features
        df['volume_sma_5'] = df['volume'].rolling(window=5).mean()
        df['volume_sma_20'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma_20']

        # Price position
        df['high_low_range'] = df['high'] - df['low']
        df['close_position'] = (df['close'] - df['low']) / df['high_low_range']

        # Lag features
        for lag in [1, 2, 3, 5, 10]:
            df[f'close_lag_{lag}'] = df['close'].shift(lag)
            df[f'volume_lag_{lag}'] = df['volume'].shift(lag)

        # Technical indicators
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))

        # MACD
        ema_12 = df['close'].ewm(span=12, adjust=False).mean()
        ema_26 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = ema_12 - ema_26
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']

        # Bollinger Bands
        bb_period = 20
        bb_std = 2
        df['bb_middle'] = df['close'].rolling(window=bb_period).mean()
        bb_std_val = df['close'].rolling(window=bb_period).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * bb_std_val)
        df['bb_lower'] = df['bb_middle'] - (bb_std * bb_std_val)
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])

        # Drop NaN values
        df = df.dropna()

        return df

    def prepare_data(self, data: pd.DataFrame, target_horizon: int = 1) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare data for training

        Args:
            data: DataFrame with features
            target_horizon: Number of periods ahead to predict

        Returns:
            Tuple of (X, y)
        """
        # Create features
        df = self.create_features(data)

        # Create target (future price or return)
        df['target'] = df['close'].shift(-target_horizon)
        df = df.dropna()

        # Select features (exclude OHLCV and target)
        feature_cols = [col for col in df.columns if col not in
                        ['open', 'high', 'low', 'close', 'volume', 'target', 'timestamp']]

        X = df[feature_cols].values
        y = df['target'].values

        return X, y

    def train(self, data: pd.DataFrame, target_horizon: int = 1,
              test_size: float = 0.2) -> Dict:
        """
        Train the prediction model

        Args:
            data: DataFrame with OHLCV data
            target_horizon: Number of periods ahead to predict
            test_size: Test set size

        Returns:
            Dictionary with training metrics
        """
        # Prepare data
        X, y = self.prepare_data(data, target_horizon)

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, shuffle=False
        )

        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Train model(s)
        if self.model_type == 'ensemble':
            self.rf_model.fit(X_train_scaled, y_train)
            self.gb_model.fit(X_train_scaled, y_train)

            # Evaluate
            rf_score = self.rf_model.score(X_test_scaled, y_test)
            gb_score = self.gb_model.score(X_test_scaled, y_test)

            metrics = {
                'rf_r2_score': rf_score,
                'gb_r2_score': gb_score,
                'ensemble_r2_score': (rf_score + gb_score) / 2,
                'train_samples': len(X_train),
                'test_samples': len(X_test)
            }
        else:
            self.model.fit(X_train_scaled, y_train)

            # Evaluate
            train_score = self.model.score(X_train_scaled, y_train)
            test_score = self.model.score(X_test_scaled, y_test)

            metrics = {
                'train_r2_score': train_score,
                'test_r2_score': test_score,
                'train_samples': len(X_train),
                'test_samples': len(X_test)
            }

        self.is_trained = True
        return metrics

    def predict(self, data: pd.DataFrame) -> float:
        """
        Predict future price

        Args:
            data: DataFrame with recent OHLCV data

        Returns:
            Predicted price
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")

        # Create features
        df = self.create_features(data)

        # Get last row features
        feature_cols = [col for col in df.columns if col not in
                        ['open', 'high', 'low', 'close', 'volume', 'timestamp']]

        X = df[feature_cols].iloc[-1:].values
        X_scaled = self.scaler.transform(X)

        # Make prediction
        if self.model_type == 'ensemble':
            rf_pred = self.rf_model.predict(X_scaled)[0]
            gb_pred = self.gb_model.predict(X_scaled)[0]
            prediction = (rf_pred + gb_pred) / 2
        else:
            prediction = self.model.predict(X_scaled)[0]

        return prediction

    def predict_direction(self, data: pd.DataFrame) -> str:
        """
        Predict price direction (up/down)

        Args:
            data: DataFrame with recent OHLCV data

        Returns:
            'up', 'down', or 'neutral'
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")

        current_price = data['close'].iloc[-1]
        predicted_price = self.predict(data)

        change_pct = ((predicted_price - current_price) / current_price) * 100

        if change_pct > 0.5:
            return 'up'
        elif change_pct < -0.5:
            return 'down'
        else:
            return 'neutral'

    def get_feature_importance(self) -> Optional[pd.DataFrame]:
        """
        Get feature importance

        Returns:
            DataFrame with feature importances
        """
        if not self.is_trained:
            return None

        if self.model_type == 'ensemble':
            # Average importance from both models
            rf_importance = self.rf_model.feature_importances_
            gb_importance = self.gb_model.feature_importances_
            importance = (rf_importance + gb_importance) / 2
        else:
            if hasattr(self.model, 'feature_importances_'):
                importance = self.model.feature_importances_
            else:
                return None

        # Note: This would need feature names from the last training
        # For simplicity, returning the importance values
        return pd.DataFrame({
            'importance': importance
        }).sort_values('importance', ascending=False)
