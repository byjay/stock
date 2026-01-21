import pandas as pd
import pandas_ta as ta
from typing import Dict, Any
import logging
from datetime import datetime
import pytz

logger = logging.getLogger("ISATS:SniperStrategy")

class SniperStrategy:
    """
    [Phase 40] 1% Sniper Strategy (Mean Reversion)
    
    Verified Logic (Win Rate 83.3% on SOXL):
    1. Time: Power Volatility Hours Only (UTC 14:30-16:30, 19:00-21:00)
    2. Setup: Price < BB_Lower (Statistically Oversold)
    3. Trigger: RSI(2) < 10 (Extreme Fear)
    4. Exit: Trailing Stop (Activate +0.5%, Trail 0.3%, Stop -1.0%)
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {
            'rsi_period': 2,
            'rsi_entry': 10,
            'bb_period': 20,
            'bb_std': 2.0,
            # EXIT PARAMS (Passed to Executor)
            'stop_loss_pct': 0.01,      # -1.0%
            'trail_activation': 0.005,  # +0.5%
            'trail_dist': 0.003         # 0.3%
        }
        
    def analyze(self, code: str, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze ticker data for 1% Sniper Setup.
        """
        result = {
            "signal": "HOLD",
            "reason": [],
            "score": 0.0,
            "indicators": {},
            "trade_params": {}
        }

        # Need at least 20 bars for BB
        if df.empty or len(df) < 25:
            result["reason"].append("INSUFFICIENT_DATA")
            return result
            
        # 1. Prepare Data (Lowercase mapping)
        # df columns might be 'open', 'high', 'low', 'close', 'volume'
        # pandas_ta expects capitalized or kwargs
        close = df['close'] if 'close' in df.columns else df['Close']
        
        # 2. Calculate Indicators
        # RSI(2)
        rsi = ta.rsi(close, length=self.config['rsi_period'])
        if rsi is None: return result
        
        # BB(20, 2)
        bb = ta.bbands(close, length=self.config['bb_period'], std=self.config['bb_std'])
        if bb is None: return result
        
        # Get latest values
        curr_idx = -1
        curr_rsi = rsi.iloc[curr_idx]
        curr_close = close.iloc[curr_idx]
        
        # Find BB Lower column (e.g., BBL_20_2.0)
        bb_lower_col = [c for c in bb.columns if c.startswith("BBL")][0]
        curr_bb_lower = bb.iloc[curr_idx][bb_lower_col]
        
        # 3. Time Filter (CRITICAL: UTC Logic)
        # We assume the system clock or passed df has time info.
        # If real-time, we check `datetime.utcnow()`
        now_utc = datetime.now(pytz.utc)
        h = now_utc.hour
        m = now_utc.minute
        
        # Morning: 14:30 - 16:30 UTC
        is_morning = (h == 14 and m >= 30) or (h == 15) or (h == 16 and m <= 30)
        # Afternoon: 19:00 - 21:00 UTC
        is_afternoon = (h == 19) or (h == 20)
        is_power_hour = is_morning or is_afternoon
        
        # 4. Logic Checks
        is_rsi_sold = curr_rsi < self.config['rsi_entry']
        is_bb_break = curr_close < curr_bb_lower
        
        # Scoring
        if is_rsi_sold: result["reason"].append(f"RSI({curr_rsi:.1f})<{self.config['rsi_entry']}")
        if is_bb_break: result["reason"].append("BB_LOWER_BREAK")
        if not is_power_hour: result["reason"].append("OUTSIDE_POWER_HOUR")
        
        result["indicators"] = {
            "rsi": curr_rsi,
            "bb_lower": curr_bb_lower,
            "close": curr_close,
            "utc_hour": h
        }
        
        # 5. Signal Decision
        if is_power_hour and is_rsi_sold and is_bb_break:
            result["signal"] = "BUY"
            result["score"] = 1.0
            result["trade_params"] = {
                "strategy": "Sniper_1pct",
                "stop_loss": self.config['stop_loss_pct'],
                "trail_activation": self.config['trail_activation'],
                "trail_dist": self.config['trail_dist']
            }
            logger.info(f"🔫 SNIPER SIGNAL DETECTED [{code}]: RSI={curr_rsi:.1f}, BB_Break=True")
            
        return result
