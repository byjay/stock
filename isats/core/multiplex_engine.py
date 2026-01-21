import logging
import pandas as pd
import numpy as np
from typing import List, Dict

# Core Components
from backend.core.strategy_engine import StrategyEngine
from backend.core.risk_manager import RiskManager
from backend.ai.resampler import Resampler
from backend.ai.stockformer import Stockformer
from backend.core.data_manager import DataManager

logger = logging.getLogger("MultiplexEngine")

class MultiplexDecisionEngine:
    """
    [ISATS Multiplex Engine]
    The Ultimate Orchestrator that combines:
    1. Multi-Timeframe Analysis (Rubber Band Strategy)
    2. Deep Learning Oracle (Stockformer)
    3. Traditional Algo Strategies (Triple Conf, etc.)
    4. Safety & Risk Management
    
    This engine does NOT just run one strategy. 
    It runs 'Encyclopedia of Strategies' across 'Infinite Timeframes' 
    and acts as a supreme judge.
    """
    
    def __init__(self):
        logger.info("🌌 Initializing Multiplex Decision Engine...")
        
        # 1. The Sub-Engines
        self.algo_engine = StrategyEngine()  # Classical Algo Rules
        self.oracle = Stockformer()          # Deep Learning Brain
        self.risk_manager = RiskManager()    # Safety Guard
        
        # 2. The "Rubber Band" Configuration
        # We look at markets through these diverse lenses
        self.adaptive_timeframes = [
            '1T',   # Micro-Scope
            '5T',   # Scalping Standard
            '15T',  # Day Trading Standard
            '30T',  # Half-Hour
            '60T',  # Hourly
            '61T',  # [Elastic] Prime Number Frame 1
            '121T', # [Elastic] Prime Number Frame 2
            '4H',   # Swing Standard
            '1D'    # Macro Trend
        ]
        
        self.consensus_threshold = 0.60 # Need 60% agreement to consider entry
        
    def analyze_ticker(self, ticker: str, base_data_1m: pd.DataFrame, news_sentiment: float = 0.5) -> dict:
        """
        Conducts a 'Full Spectrum' analysis on a single ticker.
        """
        if base_data_1m.empty:
            return {"decision": "SKIP", "reason": "No Data"}

        results_matrix = []
        
        # --- Step 1: Multi-Scale Scanning (The Rubber Band) ---
        for tf in self.adaptive_timeframes:
            # A. Resample
            df_resampled = Resampler.resample_ohlcv(base_data_1m, tf)
            
            if len(df_resampled) < 20: continue # Not enough data for this timeframe

            # [FIX] StrategyEngine expects 'datetime' column, but Resampler returns DatetimeIndex
            df_resampled['datetime'] = df_resampled.index

            # B. Run Traditional Algos on this timeframe
            # Note: StrategyEngine typically expects standard timeframes, 
            # but our strategies (BaseStrategy based) should handle any DataFrame with O/H/L/C.
            signals = self.algo_engine.evaluate(ticker, df_resampled)
            
            # C. Score the signals
            score = 0
            if signals:
                # If ANY strategy says BUY on this timeframe
                score = 1 
                # (Future: Weighted score by strategy performance)
            
            results_matrix.append({
                "timeframe": tf,
                "score": score,
                "signals": len(signals)
            })

        # --- Step 2: Calculate Consensus Score ---
        if not results_matrix:
            return {"decision": "HOLD", "reason": "Insufficient Data for Matrix"}
            
        total_frames = len(results_matrix)
        positive_frames = sum([r['score'] for r in results_matrix])
        consensus_ratio = positive_frames / total_frames
        
        # --- Step 3: Deep Learning Validation (The Oracle) ---
        # We feed the Macro (1D) and Micro (5T) to the Stockformer for a 'Vibe Check'
        # (In full version, inputs are richer)
        
        oracle_context = {
            "chart_short": Resampler.resample_ohlcv(base_data_1m, '5T'),
            "chart_long": Resampler.resample_ohlcv(base_data_1m, '1D'),
            "news_sentiment": news_sentiment,
            "market_regime": self.algo_engine.check_market_phase(base_data_1m) # Check on 1m or Daily? Daily better.
        }
        
        oracle_verdict = self.oracle.predict(oracle_context)
        oracle_confidence = oracle_verdict.get("confidence", 0.0)
        
        # --- Step 4: Final Judiciary Decision ---
        
        # Base Decision Logic
        final_decision = "HOLD"
        reason = []
        
        # A. Consensus Check
        if consensus_ratio >= self.consensus_threshold:
            reason.append(f"Consensus High ({consensus_ratio:.1%})")
            
            # B. Oracle Check
            if oracle_verdict["action"] == "BUY" or oracle_confidence > 0.7:
                 reason.append(f"Oracle Approved ({oracle_confidence:.2f})")
                 final_decision = "BUY"
            elif consensus_ratio >= 0.8:
                 # SUPER CONSENSUS OVERRIDE
                 reason.append(f"Super Consensus ({consensus_ratio:.1%} > 80%) Overrides Oracle")
                 final_decision = "BUY"
            else:
                 reason.append(f"Oracle Skeptical ({oracle_confidence:.2f})")
                 final_decision = "HOLD" 
        else:
            reason.append(f"Consensus Low ({consensus_ratio:.1%})")

        # --- Step 5: Risk Sizing (Kelly) ---
        bet_size_ratio = 0.0
        if final_decision == "BUY":
            # Synthesize Win Probability from Consensus & Oracle
            estimated_win_rate = (consensus_ratio + oracle_confidence) / 2
            
            # Ask Risk Manager for Sizing
            # 100M KRW dummy capital for calculation
            bet_money = self.risk_manager.calculate_bet_size(
                capital=100_000_000, 
                win_rate=estimated_win_rate,
                risk_reward=2.5 # Target 2.5 RR
            )
            # Convert back to ratio for report
            bet_size_ratio = bet_money / 100_000_000

        return {
            "decision": final_decision,
            "consensus_ratio": round(consensus_ratio, 2),
            "oracle_confidence": oracle_confidence,
            "participating_timeframes": total_frames,
            "positive_timeframes": positive_frames,
            "recommended_bet_size": round(bet_size_ratio, 2),
            "reason": " | ".join(reason)
        }

if __name__ == "__main__":
    # System Integrity Check (Test Stub)
    logging.basicConfig(level=logging.INFO)
    
    # Generate Synthetic Market Data (Standard Gaussian Walk)
    dates = pd.date_range(start="2026-01-01", periods=1000, freq='1min')
    data = {
        'open': np.linspace(100, 110, 1000), 
        'high': np.linspace(101, 111, 1000),
        'low': np.linspace(99, 109, 1000),
        'close': np.linspace(100, 110, 1000) + np.random.normal(0, 1, 1000),
        'volume': np.random.randint(100, 1000, 1000)
    }
    df = pd.DataFrame(data, index=dates)
    # [FIX] Essential for StrategyEngine compliance
    df['datetime'] = df.index 
    
    engine = MultiplexDecisionEngine()
    result = engine.analyze_ticker("005930", df, news_sentiment=0.8)
    
    print("\n[Multiplex Analysis Result - System Check]")
    print(result)
