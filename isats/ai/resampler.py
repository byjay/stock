import pandas as pd
import logging

logger = logging.getLogger("ISATS_Resampler")

class Resampler:
    """
    [ISATS Universal Bar Generator]
    Transforms base candle data (1m/Daily) into arbitrary timeframes requested by the Deep Learning Engine.
    Supports complex intervals like '61T' (61 mins), '11D' (11 days), '121B' (121 Base Bars).
    """

    @staticmethod
    def resample_ohlcv(df: pd.DataFrame, rule: str) -> pd.DataFrame:
        """
        Resamples a 1-minute OHLCV DataFrame into a custom timeframe.
        
        Args:
            df (pd.DataFrame): Base 1-minute Data with index as DatetimeIndex.
                               Columns: open, high, low, close, volume
            rule (str): Pandas offset alias (e.g., '15T', '60T', '1D') or custom '121B'.
            
        Returns:
            pd.DataFrame: Resampled OHLCV Data.
        """
        if df.empty:
            return df
            
        # Ensure index is datetime
        if not isinstance(df.index, pd.DatetimeIndex):
            if 'timestamp' in df.columns:
                df = df.set_index('timestamp')
            elif 'date' in df.columns:
                df = df.set_index('date')
            else:
                logger.error("❌ DataFrame must have DatetimeIndex or 'timestamp' column")
                return pd.DataFrame()

        # Handle purely count-based bars (e.g., "121 bars" aggregation) -> Not standard time
        # This is strictly "Time-based" resampling for now as requested (30s, 60m etc)
        
        try:
            # 1. Map Custom Rules
            # User said "30초(30s)", "61분(61T)", "3일(3D)"
            
            resampled = df.resample(rule).agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            })
            
            # Remove empty rows (Market closed times)
            resampled = resampled.dropna()
            
            logger.debug(f"✨ Resampled {len(df)} bars -> {len(resampled)} bars (Rule: {rule})")
            return resampled

        except Exception as e:
            logger.error(f"❌ Resampling Failed (Rule: {rule}): {e}")
            return pd.DataFrame()

    @staticmethod
    def detect_golden_cross(df: pd.DataFrame, fast: int = 20, slow: int = 60):
        """
        Checks for Golden Cross in the provided (Resampled) DataFrame.
        Returns the row where the cross happened.
        """
        df['SMA_Fast'] = df['close'].rolling(window=fast).mean()
        df['SMA_Slow'] = df['close'].rolling(window=slow).mean()
        
        # Logic: Fast > Slow (Today) AND Fast < Slow (Yesterday)
        # Using vectorized shift
        df['Prev_Fast'] = df['SMA_Fast'].shift(1)
        df['Prev_Slow'] = df['SMA_Slow'].shift(1)
        
        # Boolean Mask for Golden Cross
        mask = (df['SMA_Fast'] > df['SMA_Slow']) & (df['Prev_Fast'] <= df['Prev_Slow'])
        
        crosses = df[mask]
        return crosses

# Test stub
if __name__ == "__main__":
    # Create Mock 1-minute data
    dates = pd.date_range(start="2026-01-01", periods=1000, freq='1T')
    data = {
        'open': [100] * 1000, 'high': [105] * 1000,
        'low': [95] * 1000, 'close': [102] * 1000,
        'volume': [10] * 1000
    }
    df = pd.DataFrame(data, index=dates)
    
    # Test 61-minute resampling
    result = Resampler.resample_ohlcv(df, '61T')
    print(f"61-min Bars:\n{result.head()}")
