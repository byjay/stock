import pandas as pd
import logging

logger = logging.getLogger("Core:ElasticTimeframe")

class ElasticTimeframeManager:
    """
    [ISATS] Elastic Timeframe Manager (고무줄 분석).
    
    User Philosophy: "Don't look at standard 5m/20m/60m charts. Look at 11m, 39m, 49m."
    Why? To avoid HFT noise and standard algorithmic patterns.
    
    Supported Intervals:
    - 11m: 'Quick Pulse' (Fast trends)
    - 39m: 'Deep Breath' (Mid-term accumulation)
    - 49m: 'Golden Rhythm' (Major trend shifts)
    - 11D: 'Macro Wave' (11-Day candles for long-term cycle)
    """

    @staticmethod
    def resample_data(df: pd.DataFrame, interval_minutes: int) -> pd.DataFrame:
        """
        Resamples minute-level data into custom Elastic Timeframes.
        """
        if df.empty:
            return df
            
        # Ensure 'timestamp' or 'date' is index
        df = df.copy()
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
        elif 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
        rule = f"{interval_minutes}T" # e.g., '11T' for 11 minutes
        
        # Resample logic
        resampled = df.resample(rule).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        })
        
        # Drop incomplete or empty bins
        resampled.dropna(inplace=True)
        
        # Reset index to make it accessible
        resampled.reset_index(inplace=True)
        
        logger.info(f"📐 [Elastic] Resampled to {interval_minutes}m bars. (Count: {len(resampled)})")
        return resampled

    @staticmethod
    def apply_rubber_band_logic(df: pd.DataFrame) -> dict:
        """
        [Rubber Band Logic]
        Analyzes the custom timeframe data for 'Snap Back' potential.
        """
        if len(df) < 20: return {"signal": "NEUTRAL", "reason": "Insufficient Data"}
        
        # Calculate Bollinger Bands on this weird timeframe
        period = 20
        df['MA'] = df['close'].rolling(period).mean()
        df['STD'] = df['close'].rolling(period).std()
        df['Upper'] = df['MA'] + (df['STD'] * 2)
        df['Lower'] = df['MA'] - (df['STD'] * 2)
        
        last = df.iloc[-1]
        
        # Logic: Price < Lower Band = "Stretched Down" (Buy)
        if last['close'] < last['Lower']:
            return {
                "signal": "BUY", 
                "strength": "HIGH", 
                "reason": f"Rubber Band Stretched on Custom Timeframe (Close < LowerBB)"
            }
            
        # Logic: Price > Upper Band = "Stretched Up" (Sell)
        if last['close'] > last['Upper']:
            return {
                "signal": "SELL", 
                "strength": "HIGH", 
                "reason": "Rubber Band Stretched Up (Close > UpperBB)"
            }
            
        return {"signal": "HOLD", "strength": "NEUTRAL", "reason": "Inside Bands"}

class FractalTransformer:
    """
    Implements 'Fractal Chaos' logic:
    1. Time Dilation: Treating Daily data as Minute data (and vice versa).
    2. Chaos Resampling: Aggregating into non-standard, prime, or random intervals.
    """
    
    @staticmethod
    def dilate_time(df: pd.DataFrame, target_freq: str = '1min') -> pd.DataFrame:
        """
        [Time Dilation]
        Tricks the strategy by replacing the index with a synthetic high-frequency index.
        Useful for applying 'Scalper Logic' to 'Daily Data'.
        """
        if df.empty: return df
        
        dilated = df.copy()
        # Generate synthetic index starting from now, working backwards
        end_date = pd.Timestamp.now()
        periods = len(df)
        
        # Create synthetic range
        synthetic_index = pd.date_range(end=end_date, periods=periods, freq=target_freq)
        dilated.index = synthetic_index
        return dilated

    @staticmethod
    def chaos_resample(df: pd.DataFrame, intervals: list = None) -> dict:
        """
        [Chaos Aggregation]
        Resamples data into a wild mix of user-defined intervals (30, 44, 55, 132, 325...).
        """
        if intervals is None:
            # User's specific "Chaos Logic" numbers + Fibonacci
            intervals = [30, 44, 55, 132, 325, 1, 3, 5, 8, 13, 21] 
            
        results = {}
        for minutes in intervals:
            key = f"Chaos_{minutes}m"
            try:
                # Use the existing robust resampler
                resampled = ElasticTimeframeManager.resample_data(df, minutes)
                if not resampled.empty and len(resampled) > 10:
                    results[key] = resampled
            except Exception:
                continue
                
        return results
