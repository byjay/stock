import logging
import pandas as pd
import numpy as np

logger = logging.getLogger("RegimeDetector")

class RegimeDetector:
    """
    [Anti-Fragility] Market Regime Analysis Engine.
    Detects 'Black Swan' conditions and macro regime shifts.
    Defends against 'Regime Blindness' critique in 비판.md.
    """
    def __init__(self, high_vol_threshold=30, trend_threshold=25):
        self.high_vol_threshold = high_vol_threshold # VIX-like threshold
        self.trend_threshold = trend_threshold       # ADX-like threshold

    def analyze_regime(self, market_data: pd.DataFrame):
        """
        Input: Market Proxy (e.g., KOSPI / S&P500 Index Data)
        Output: Regime Status (NORMAL, VOLATILE, CRASH_RISK)
        """
        if market_data is None or len(market_data) < 20:
            return "UNKNOWN"

        # 1. Volatility check (StdDev of returns)
        returns = market_data['close'].pct_change().dropna()
        volatility = returns.tail(10).std() * np.sqrt(252) * 100
        
        # 2. Trend Strength (ADX implementation simplified)
        # For simplicity, we use EMA crossover status as a proxy for 'Healthy Trend'
        ema_20 = market_data['close'].ewm(span=20).mean().iloc[-1]
        ema_50 = market_data['close'].ewm(span=50).mean().iloc[-1]
        
        # 3. Decision Logic
        if volatility > self.high_vol_threshold:
            logger.warning(f"⚠️ [REGIME-ALARM] High Volatility Detected: {volatility:.2f}%")
            return "CRUSH_RISK"
        
        if market_data['close'].iloc[-1] < ema_50:
            logger.info("🐻 [REGIME] Bear Market / Correction Territory.")
            return "BEAR"
            
        if ema_20 > ema_50:
            return "BULL_HEALTHY"
            
        return "NEUTRAL"

    def can_trade(self, regime):
        """
        Safety Switch: Disables buying in Crash/Bear regimes.
        """
        safe_regimes = ["BULL_HEALTHY", "NEUTRAL"]
        if regime not in safe_regimes:
            logger.info(f"🛑 [SAFETY] Trading Blocked due to Market Regime: {regime}")
            return False
        return True
