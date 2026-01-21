import pandas as pd
import numpy as np
import logging

logger = logging.getLogger("VolumeContext")

class VolumeContext:
    """
    [Phase F] Semantic Market Understanding.
    Goes beyond 'Volume' as a number, analyzing its 'Structure'.
    Detects Absorption, Distribution, and Exhaustion patterns.
    """
    def __init__(self, window=20):
        self.window = window

    def analyze_texture(self, df: pd.DataFrame) -> dict:
        """
        Analyzes the 'texture' of volume relative to price action.
        - High Volume + Small Price Move = Absorption (Smart Money cumulative)
        - High Volume + Large Price Move = Momentum/Breakout
        - Low Volume + Large Price Move = Exhaustion (Retail Trap)
        """
        if len(df) < self.window:
            return {"pattern": "INSUFFICIENT_DATA", "score": 0.0}

        recent = df.tail(self.window).copy()
        
        # 1. Volume Relative to Average
        avg_vol = recent['volume'].mean()
        curr_vol = recent.iloc[-1]['volume']
        vol_ratio = curr_vol / avg_vol if avg_vol > 0 else 1.0
        
        # 2. Price Displacement vs Volume (Efficiency)
        # Displacement = Abs(Close - Open)
        displacement = abs(recent.iloc[-1]['close'] - recent.iloc[-1]['open'])
        vol_efficiency = displacement / curr_vol if curr_vol > 0 else 0
        
        # 3. Categorize Pattern
        pattern = "STABLE"
        score = 0.5
        
        if vol_ratio > 2.0:
            if vol_efficiency < 0.0001: # High volume, tiny move
                pattern = "ABSORPTION_OR_DISTRIBUTION"
                score = 0.8
            else:
                pattern = "STRONG_HAND_MOMENTUM"
                score = 0.9
        elif vol_ratio < 0.5 and displacement > recent['close'].std():
            pattern = "LOW_LIQUIDITY_TRAP"
            score = 0.2
            
        logger.debug(f"[VOL-CONTEXT] Pattern: {pattern}, Ratio: {vol_ratio:.2f}, Efficiency: {vol_efficiency:.6f}")
        
        return {
            "pattern": pattern,
            "vol_ratio": vol_ratio,
            "efficiency": vol_efficiency,
            "semantic_score": score
        }

    def get_latent_features(self, df: pd.DataFrame) -> np.ndarray:
        """
        Returns a vector representation of volume status for Embedding injection.
        """
        analysis = self.analyze_texture(df)
        # Simplified vector: [vol_ratio, efficiency, score, is_absorption]
        is_abs = 1.0 if analysis['pattern'] == "ABSORPTION_OR_DISTRIBUTION" else 0.0
        return np.array([analysis['vol_ratio'], analysis['efficiency'], analysis['semantic_score'], is_abs])
