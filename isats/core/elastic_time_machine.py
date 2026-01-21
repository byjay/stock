
import pandas as pd
import logging
import asyncio
from datetime import datetime, timedelta
from backend.core.korea_inv_wrapper import KoreaInvWrapper
from backend.core.ta import TechnicalAnalysis, FractalTransformer
from backend.core.universe_provider import UniverseProvider

logger = logging.getLogger("ISATS_ElasticTimeMachine")

class ElasticTimeMachine:
    """
    [ISATS Elastic Time Machine]
    Implements 'Rubber Band' strategy learning.
    Regresses through history week-by-week to find patterns in 'Rubber Band' timeframes (2D, 3D, 22D).
    """
    def __init__(self):
        self.broker = KoreaInvWrapper()
        # Ensure we are in simulation/mock mode where appropriate, 
        # but here we mostly read data.
        self.results = []

    async def run_elastic_learning(self, ticker: str, lookback_weeks: int = 52, custom_frames: list = None):
        """
        Runs the elastic learning process.
        :param custom_frames: List of pandas resample rules (e.g. ['7D', '13D']). Overrides defaults if provided.
        """
        # 1. Fetch History (2 Years to allow for 52 weeks lookback + indicators)
        history = await self.broker._fetch_missing_history_logic(ticker, years=2)
        if not history:
            return None
            
        df = pd.DataFrame(history)
        df['date'] = pd.to_datetime(df['stck_bsop_date'])
        df['close'] = df['stck_clpr'].astype(float)
        df['open'] = df['stck_oprc'].astype(float)
        df['high'] = df['stck_hgpr'].astype(float)
        df['low'] = df['stck_lwpr'].astype(float)
        df['volume'] = df['acml_vol'].astype(float)
        df = df.sort_values('date').reset_index(drop=True)
        
        # Determine Frames to use
        frames_to_build = custom_frames if custom_frames else ['2D', '3D', '5D', '22D']
        
        # Pre-calculate 'Rubber Band' Dataframes
        rb_frames = {}
        for rule in frames_to_build:
             # Ideally we resample the whole DF once
             try:
                rb_frames[rule] = FractalTransformer.resample(df, rule)
                # Add indicators to these frames
                rb_frames[rule] = TechnicalAnalysis.add_all_indicators(rb_frames[rule])
             except Exception as e:
                logger.error(f"Failed to resample {rule} for {ticker}: {e}")

        # Add indicators to base daily frame
        df = TechnicalAnalysis.add_all_indicators(df)

        learning_results = []
        
        # 2. Iterate backwards week by week (approx 5 business days steps)
        # We start from the latest data and move back
        # We need at least 60 days of data for indicators
        if len(df) < 100:
            return None

        # Step size: 5 days (1 week)
        cursor = len(df) - 1
        
        while cursor > 60 and lookback_weeks > 0:
            # Define "Current Week" window [start_idx, end_idx]
            # Actually we want to predict the *next* week based on *current* state.
            # So let's look at `cursor`.
            
            # Check if Price Rose significantly in the 'Next Week' (Future relative to cursor)
            # We can't look into future if cursor is at the end. 
            # So we move cursor back by 5 days, and check if it rose in the *following* 5 days.
            
            check_date = df.iloc[cursor]['date']
            
            # 5-day return (Forward looking from cursor)
            # Find the price 5 days ahead (or approx)
            future_idx = min(cursor + 5, len(df) - 1)
            future_price = df.iloc[future_idx]['close']
            current_price = df.iloc[cursor]['close']
            
            # Calculate return
            weekly_return = (future_price - current_price) / current_price
            
            # Winner Logic: > 5% gain in 1 week
            if weekly_return > 0.05:
                # FOUND A WINNER!
                # Extract 'State' (DNA) from Rubber Band frames at this specific date
                dna = self.extract_dna(ticker, check_date, df, rb_frames)
                dna['return_1w'] = weekly_return
                dna['date'] = check_date.strftime("%Y-%m-%d")
                learning_results.append(dna)
                
                logger.info(f"🧬 [ELASTIC] Found Winner Pattern for {ticker} on {dna['date']} (+{weekly_return*100:.1f}%)")
            
            # Move cursor back by 5 days (1 week)
            cursor -= 5
            lookback_weeks -= 1
            
        return learning_results

    def extract_dna(self, ticker, date, daily_df, rb_frames):
        """
        Extracts technical indicators from all timeframes at a specific date.
        """
        dna = {'ticker': ticker}
        
        # 1. Daily DNA
        # Find row closest to date (<= date)
        mask_d = daily_df['date'] <= date
        if not mask_d.any(): return dna
        
        daily_row = daily_df[mask_d].iloc[-1]
        dna['D_RSI'] = daily_row.get('RSI', 50)
        dna['D_MACD_Hist'] = daily_row.get('MACD_Hist', 0)
        
        # Safe BB Calculation
        upper = daily_row.get('BBU_20_2.0', daily_row.get('BB_upper', 0))
        lower = daily_row.get('BBL_20_2.0', daily_row.get('BB_lower', 0))
        mid = daily_row.get('BBM_20_2.0', daily_row.get('BB_middle', 1))
        
        dna['D_BB_Width'] = (upper - lower) / mid if mid != 0 else 0
        
        # 2. Rubber Band DNA
        for rule, frame in rb_frames.items():
            mask = frame['date'] <= date
            if mask.any():
                row = frame[mask].iloc[-1]
                dna[f'{rule}_RSI'] = row.get('RSI', 50)
                dna[f'{rule}_MACD_Hist'] = row.get('MACD_Hist', 0)
            else:
                dna[f'{rule}_RSI'] = None
                dna[f'{rule}_MACD_Hist'] = None
                
        return dna

    async def predict_chaos_entry(self, ticker: str, current_df: pd.DataFrame) -> dict:
        """
        [Time Machine Projection]
        Applies the 'Golden Energy' (RSI 43-63) logic across Fractal Chaos timeframes 
        to predict if this stock is in the 'Rising Zone'.
        """
        from backend.core.elastic_timeframe import ElasticTimeframeManager, FractalTransformer
        import pandas_ta as ta
        
        # Chaos Intervals defined by User
        chaos_intervals = [30, 44, 55, 132, 325]
        
        predictions = {
            "ticker": ticker,
            "signal": "WAIT",
            "confidence": 0.0,
            "detected_frames": []
        }
        
        valid_frames = 0
        
        for minutes in chaos_intervals:
            # Resample current dataframe designed to mimic "Chaos"
            # In a real Time Machine, we would project *past* successful patterns here.
            # For now, we apply the "Winning Formula" derived from those patterns.
            
            resampled = ElasticTimeframeManager.resample_data(current_df, minutes)
            if len(resampled) < 20: continue
            
            # Indicators
            resampled.ta.rsi(length=14, append=True)
            resampled.ta.bbands(length=20, std=2.0, append=True)
            
            last = resampled.iloc[-1]
            rsi = last.get('RSI_14', 50)
            
            # The "Golden Energy" Rule found by PatternAnalyzer
            if 43 <= rsi <= 63:
                # Check for Squeeze?
                bbu = last.get('BBU_20_2.0', 0)
                bbl = last.get('BBL_20_2.0', 0)
                bbm = last.get('BBM_20_2.0', 1)
                width = (bbu - bbl) / bbm if bbm > 0 else 1.0
                
                if width < 0.2: # Squeeze condition
                    valid_frames += 1
                    predictions["detected_frames"].append(f"{minutes}m")
        
        if valid_frames >= 2: # At least 2 chaos frames align
            predictions["signal"] = "BUY_PREDICTION"
            predictions["confidence"] = min(0.5 + (valid_frames * 0.1), 0.95)
            predictions["reason"] = f"Fractal Alignment in {predictions['detected_frames']} (Golden Energy)"
            
        return predictions

    async def predict_drop_point(self, ticker: str, current_df: pd.DataFrame) -> dict:
        """
        [Drop Point Prediction]
        Scans for 'Exhaustion' signals in Chaos Timeframes to predict top.
        """
        from backend.core.elastic_timeframe import ElasticTimeframeManager
        import pandas_ta as ta
        
        chaos_intervals = [30, 44, 55, 132, 325]
        exhaustion_signals = 0
        
        for minutes in chaos_intervals:
            resampled = ElasticTimeframeManager.resample_data(current_df, minutes)
            if len(resampled) < 20: continue
            
            resampled.ta.rsi(length=14, append=True)
            last = resampled.iloc[-1]
            rsi = last.get('RSI_14', 50)
            
            # Overbought in Chaos Frame
            if rsi > 75:
                exhaustion_signals += 1
                
        if exhaustion_signals >= 2:
             return {
                 "ticker": ticker,
                 "signal": "SELL_PREDICTION",
                 "confidence": 0.9,
                 "reason": f"Fractal Exhaustion (Overheated in {exhaustion_signals} Chaos Frames)"
             }
             
        return {"ticker": ticker, "signal": "HOLD", "confidence": 0.5, "reason": "Trend Healthy"}
