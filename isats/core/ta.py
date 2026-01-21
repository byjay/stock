import pandas as pd
import numpy as np

class TechnicalAnalysis:
    """
    Centralized Technical Analysis Engine.
    Implements the logic defined in 'skills/chart_analysis/SKILL.md'.
    """
    
    @staticmethod
    def add_all_indicators(df: pd.DataFrame):
        """Adds all core indicators to the DataFrame in-place."""
        df = TechnicalAnalysis.add_bollinger_bands(df)
        df = TechnicalAnalysis.add_macd(df)
        df = TechnicalAnalysis.add_rsi(df)
        df = TechnicalAnalysis.add_volume_ma(df)
        return df

    @staticmethod
    def add_bollinger_bands(df: pd.DataFrame, period=20, std_dev=2):
        """Adds BB_upper, BB_middle, BB_lower"""
        # Using simple rolling mean and std
        df['BB_middle'] = df['close'].rolling(window=period).mean()
        df['BB_std'] = df['close'].rolling(window=period).std()
        df['BB_upper'] = df['BB_middle'] + (df['BB_std'] * std_dev)
        df['BB_lower'] = df['BB_middle'] - (df['BB_std'] * std_dev)
        return df

    @staticmethod
    def add_macd(df: pd.DataFrame, fast=12, slow=26, signal=9):
        """Adds MACD, MACD_Signal, MACD_Hist"""
        df['EMA_fast'] = df['close'].ewm(span=fast, adjust=False).mean()
        df['EMA_slow'] = df['close'].ewm(span=slow, adjust=False).mean()
        df['MACD'] = df['EMA_fast'] - df['EMA_slow']
        df['MACD_Signal'] = df['MACD'].ewm(span=signal, adjust=False).mean()
        df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
        return df

    @staticmethod
    def add_rsi(df: pd.DataFrame, period=14):
        """Adds RSI using Wilder's Smoothing (Standard)"""
        delta = df['close'].diff()
        
        # Make the positive gains (up) and negative gains (down) Series
        up, down = delta.copy(), delta.copy()
        up[up < 0] = 0
        down[down > 0] = 0
        
        # Calculate the EWMA
        # Wilder's smoothing: alpha = 1/period
        roll_up = up.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
        roll_down = down.abs().ewm(alpha=1/period, min_periods=period, adjust=False).mean()

        # Calculate the RSI
        rs = roll_up / roll_down
        df['RSI'] = 100.0 - (100.0 / (1.0 + rs))
        return df
    
    @staticmethod
    def add_volume_ma(df: pd.DataFrame, period=20):
        """Adds Volume_MA"""
        df['Volume_MA'] = df['volume'].rolling(window=period).mean()
        return df

class FractalTransformer:
    """
    [ISATS] Fractal Chaos Timeframe Transformer.
    (Formerly TimeframeResampler)
    Converts base linear time into 'Elastic/Fractal' bars (2D, 3D, 55D, etc.) using Time Dilation logic.
    """
    
    @staticmethod
    def resample(df: pd.DataFrame, rule: str) -> pd.DataFrame:
        """
        Resamples the DataFrame to the specified rule (e.g., '2D', '3D', 'W').
        
        Args:
            df: DataFrame with datetime index or 'date' column.
            rule: Resampling rule (e.g., '2D', '3D', 'W-FRI').
            
        Returns:
            Resampled DataFrame with Open, High, Low, Close, Volume.
        """
        df = df.copy()
        
        # Ensure 'date' is datetime and set as index
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
        # Resample logic
        # 'D' based rules (2D, 3D) need custom aggregation
        resampled = df.resample(rule).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        })
        
        # Drop rows with NaN (incomplete periods or missing data)
        resampled.dropna(inplace=True)
        
        # Reset index to make 'date' a column again
        resampled.reset_index(inplace=True)
        
        return resampled
