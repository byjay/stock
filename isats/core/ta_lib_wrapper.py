import pandas as pd
import numpy as np
import logging

logger = logging.getLogger("TAWrapper")

class TAWrapper:
    """
    Wrapper for Technical Analysis Library (Pure Pandas Implementation).
    Standardizes indicator parameter calls without external dependencies.
    """
    
    @staticmethod
    def add_all_indicators(df: pd.DataFrame):
        """Adds standard indicators defined in SKILL.md to the DataFrame."""
        if df.empty:
            return df
            
        close = df['close']
        high = df['high']
        low = df['low']

        # 1. Bollinger Bands (20, 2)
        # BBL_20_2.0, BBM_20_2.0, BBU_20_2.0
        mid = close.rolling(window=20).mean()
        std = close.rolling(window=20).std()
        df['BBM_20_2.0'] = mid
        df['BBU_20_2.0'] = mid + (std * 2)
        df['BBL_20_2.0'] = mid - (std * 2)
        
        # 2. RSI (14)
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI_14'] = 100 - (100 / (1 + rs))
        df['RSI_14'] = df['RSI_14'].fillna(50) # Fill NaN with neutral

        # 3. MACD (12, 26, 9)
        # MACD_12_26_9, MACDh_12_26_9, MACDs_12_26_9
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9, adjust=False).mean()
        hist = macd - signal
        
        df['MACD_12_26_9'] = macd
        df['MACDs_12_26_9'] = signal
        df['MACDh_12_26_9'] = hist
        
        # 4. ATR (14)
        lc = close.shift(1)
        tr1 = high - low
        tr2 = (high - lc).abs()
        tr3 = (low - lc).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df['ATRr_14'] = tr.rolling(window=14).mean()

        # 5. SMA (Moving Averages)
        df['SMA_5'] = close.rolling(window=5).mean()
        df['SMA_20'] = close.rolling(window=20).mean()
        df['SMA_60'] = close.rolling(window=60).mean()
        df['SMA_120'] = close.rolling(window=120).mean()
        
        return df

    @staticmethod
    def check_golden_cross(df: pd.DataFrame, short_window=20, long_window=60):
        """Checks for Golden Cross (Short > Long)."""
        if len(df) < 2:
            return False
            
        short_ma = f"SMA_{short_window}"
        long_ma = f"SMA_{long_window}"
        
        if short_ma not in df.columns or long_ma not in df.columns:
            return False
        
        # Check current and previous
        curr_short = df[short_ma].iloc[-1]
        curr_long = df[long_ma].iloc[-1]
        prev_short = df[short_ma].iloc[-2]
        prev_long = df[long_ma].iloc[-2]
        
        # Crossover logic
        if prev_short <= prev_long and curr_short > curr_long:
            return True
        return False
