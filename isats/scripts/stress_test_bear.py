import asyncio
import logging
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

# ISATS Core
from backend.core.multiplex_engine import MultiplexDecisionEngine
from backend.core.strategy_engine import StrategyEngine

# 셋업
os.makedirs("logs", exist_ok=True)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("StressTest")

def generate_bear_market_data(minutes=1000):
    """
    [Scenario Builder]
    Generates 1000 minutes of "The Great Crash".
    - Base Stock (Samsung Elec): -15% over 1000 mins
    - Inverse ETF (KODEX Inverse 2X): +30% over 1000 mins
    """
    dates = pd.date_range(start="2026-06-01 09:00:00", periods=minutes, freq='1T')
    
    # 1. SAMSUNG ELEC (Crashing)
    samsung_price = 80000
    samsung_data = []
    
    # 2. INVERSE ETF (Rising)
    inverse_price = 2500
    inverse_data = []
    
    for i in range(minutes):
        # Samsung: Drift -0.02% per minute + Noise
        drift_s = -0.0002
        noise_s = np.random.normal(0, 0.001)
        samsung_price *= (1 + drift_s + noise_s)
        
        # Inverse: Drift +0.04% per minute (2X Inverse) + Noise
        drift_i = 0.0004
        noise_i = np.random.normal(0, 0.001)
        inverse_price *= (1 + drift_i + noise_i)
        
        samsung_data.append(samsung_price)
        inverse_data.append(inverse_price)
        
    df_samsung = pd.DataFrame({
        'open': samsung_data, 'high': samsung_data, 'low': samsung_data, 'close': samsung_data,
        'volume': [100000]*minutes
    }, index=dates)
    df_samsung['datetime'] = df_samsung.index # Fix for Engine
    
    df_inverse = pd.DataFrame({
        'open': inverse_data, 'high': inverse_data, 'low': inverse_data, 'close': inverse_data,
        'volume': [500000]*minutes
    }, index=dates)
    df_inverse['datetime'] = df_inverse.index # Fix for Engine

    return df_samsung, df_inverse

def run_stress_test():
    logger.info("📉 [STRESS TEST] Initiating 'Bear Market' Simulation (1000 mins)...")
    
    # 1. Generate Data
    df_crash, df_hedge = generate_bear_market_data(1000)
    
    logger.info(f"   Samsung Start: {df_crash.iloc[0]['close']:.0f} -> End: {df_crash.iloc[-1]['close']:.0f} ({(df_crash.iloc[-1]['close']/df_crash.iloc[0]['close'] - 1)*100:.2f}%)")
    logger.info(f"   Inverse Start: {df_hedge.iloc[0]['close']:.0f} -> End: {df_hedge.iloc[-1]['close']:.0f} ({(df_hedge.iloc[-1]['close']/df_hedge.iloc[0]['close'] - 1)*100:.2f}%)")

    # 2. Setup Engine
    engine = MultiplexDecisionEngine()
    
    # 3. Simulate Loop
    logger.info(">>> Running Multiplex Engine on Crashing Market...")
    
    # A. Test Samsung (Should HOLD or SELL)
    # We slice data in chunks to simulate time passing? 
    # Or just run on the final state to see decision?
    # MultiplexEngine analyzes ONE snapshot. We should pick a moment mid-crash.
    
    mid_point = 500
    snapshot_crash = df_crash.iloc[:mid_point]
    
    res_crash = engine.analyze_ticker("005930", snapshot_crash, news_sentiment=-0.8)
    logger.info(f"   [005930] Decision at min {mid_point}: {res_crash['decision']} (Reason: {res_crash['reason']})")
    
    # B. Test Inverse ETF (252670) (Should BUY)
    # NOTE: MultiplexEngine's AlgoEngine needs to know this IS the Inverse ETF.
    snapshot_hedge = df_hedge.iloc[:mid_point]
    
    # StrategyEngine specific check for Inverse
    # The MultiplexEngine calls `algo_engine.evaluate`. 
    # Ensure '252670' triggers InverseLogic inside `evaluate`.
    
    res_hedge = engine.analyze_ticker("252670", snapshot_hedge, news_sentiment=-0.8)
    logger.info(f"   [252670] Decision at min {mid_point}: {res_hedge['decision']} (Reason: {res_hedge['reason']})")

    # 4. Result Validation
    if res_crash['decision'] != 'BUY' and res_hedge['decision'] == 'BUY':
        print("\n✅ [SUCCESS] Engine correctly avoided Crash Stock and bought Inverse Hedge.")
        print(f"   - Crash Stock Signal: {res_crash['decision']}")
        print(f"   - Inverse ETF Signal: {res_hedge['decision']}")
    else:
        print("\n❌ [FAIL] Engine failed to hedge properly.")
        print(f"   - Crash Stock Signal: {res_crash['decision']}")
        print(f"   - Inverse ETF Signal: {res_hedge['decision']}")

if __name__ == "__main__":
    run_stress_test()
