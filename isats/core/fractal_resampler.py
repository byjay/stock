import numpy as np
import pandas as pd
from datetime import timedelta

class FractalResampler:
    """
    Upsamples coarse OHLC data (e.g., 1-Hour) to fine-grained data (e.g., 1-Minute)
    using constrained fractal noise to preserve price action realism.
    """
    
    @staticmethod
    def upsample_1h_to_1m(df_1h: pd.DataFrame) -> pd.DataFrame:
        """
        Converts a DataFrame with 1H frequency to 1M frequency.
        Constraint: The 1M bars must respect the O/H/L/C of the source 1H bar.
        """
        if df_1h.empty:
            return pd.DataFrame()
            
        all_1m_rows = []
        
        # Iterate over each 1H bar
        # This is computationally expensive for large datasets, 
        # so we optimize by vectorizing or processing in chunks if needed.
        # For scenario files (approx 2-3k rows), simple loop is acceptable for prototype.
        
        for idx, row in df_1h.iterrows():
            start_time = idx
            open_p = row['open']
            high_p = row['high']
            low_p = row['low']
            close_p = row['close']
            vol_total = row['volume']
            
            # Generate 60 steps
            steps = 60
            
            # 1. Generate Brownian Bridge from Open to Close
            t = np.linspace(0, 1, steps + 1)
            brownian_motion = np.cumsum(np.random.randn(steps + 1))
            brownian_bridge = brownian_motion - t * brownian_motion[-1]
            
            # Map valid 0..1 bridge to Open..Close logic? 
            # Simpler: Linear path + Bridge Noise
            linear_path = np.linspace(open_p, close_p, steps + 1)
            
            # Amplitude scaler based on High-Low range (Volatility)
            volatility = high_p - low_p
            noise = brownian_bridge * (volatility * 0.5) # Scale noise
            
            price_path = linear_path + noise
            
            # 2. Force Limits (Pinning) to respect High/Low
            current_max = np.max(price_path)
            current_min = np.min(price_path)
            
            # Scale to fit exactly within High and Low
            # Normalize to 0-1 range relative to min/max
            if current_max != current_min:
                price_path_norm = (price_path - current_min) / (current_max - current_min)
                # Scale to target High/Low
                price_path_scaled = price_path_norm * (high_p - low_p) + low_p
            else:
                price_path_scaled = price_path
                
            # 3. Force Start(Open) and End(Close) exactly?
            # The scaling above shifts everything. We need to be careful.
            # Pinning Open/Close is strict constraint. High/Low is boundary constraint.
            # Let's use a simpler heuristic for speed & robustness:
            # - Generate random walk
            # - Clip to Low/High
            # - Force first=Open, last=Close
            # - If High not reached, insert Spike. If Low not reached, insert Dip.
            
            # optimized_path = price_path_scaled # Use the scaled one for general shape
            # Force endpoints (Discontinuity is small usually)
            price_path_scaled[0] = open_p
            price_path_scaled[-1] = close_p
            
            # Ensure at least one point hits High and Low (Inject if missing)
            if np.max(price_path_scaled) < high_p:
                max_idx = np.argmax(price_path_scaled)
                price_path_scaled[max_idx] = high_p
                
            if np.min(price_path_scaled) > low_p:
                min_idx = np.argmin(price_path_scaled)
                price_path_scaled[min_idx] = low_p
                
            # Create Data Lines
            base_time = pd.Timestamp(start_time)
            
            # Distribute volume somewhat randomly
            vol_chunk = vol_total / steps
            
            for i in range(steps):
                time_offset = base_time + timedelta(minutes=i)
                # Simple 1m bar: O=C=H=L = price_point (Line Chart approx for 1m)
                # Or generate mini-bars? Line chart logic is sufficient for "Close" based indicators.
                p = price_path_scaled[i+1] # Next price
                prev_p = price_path_scaled[i]
                
                # Construct mini OHLCandle
                bar_o = prev_p
                bar_c = p
                bar_h = max(bar_o, bar_c)
                bar_l = min(bar_o, bar_c)
                
                all_1m_rows.append({
                    "datetime": time_offset,
                    "open": bar_o,
                    "high": bar_h,
                    "low": bar_l,
                    "close": bar_c,
                    "volume": vol_chunk * np.random.uniform(0.5, 1.5)
                })
                
        df_1m = pd.DataFrame(all_1m_rows)
        if not df_1m.empty:
            df_1m.set_index('datetime', inplace=True)
            
        return df_1m
