import subprocess
import sys
import time
import os
import yfinance as yf
import pandas as pd
import numpy as np

# Same as worker for core calculation
def calculate_all_10_indicators(df):
    close = df['close'].squeeze()
    high = df['high'].squeeze()
    low = df['low'].squeeze()
    vol = df['volume'].squeeze()
    df['ema_long'] = close.ewm(span=100, adjust=False).mean()
    delta = close.diff()
    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0; down[down > 0] = 0
    roll_up = up.ewm(alpha=1/14, adjust=False).mean()
    roll_down = down.abs().ewm(alpha=1/14, adjust=False).mean()
    df['rsi'] = 100.0 - (100.0 / (1.0 + roll_up / (roll_down + 1e-9)))
    df['bb_mid'] = close.rolling(20).mean()
    df['bb_std'] = close.rolling(20).std()
    df['bb_low'] = df['bb_mid'] - 1.2 * df['bb_std']
    exp1 = close.ewm(span=12, adjust=False).mean()
    exp2 = close.ewm(span=26, adjust=False).mean()
    df['macd'] = exp1 - exp2
    df['macd_sig'] = df['macd'].ewm(span=9, adjust=False).mean()
    low_14 = low.rolling(14).min(); high_14 = high.rolling(14).max()
    df['stoch_k'] = 100 * (close - low_14) / (high_14 - low_14 + 1e-9)
    tr = pd.concat([high - low, abs(high - close.shift()), abs(low - close.shift())], axis=1).max(axis=1)
    df['atr'] = tr.rolling(14).mean()
    tp = (high + low + close) / 3; mf = tp * vol
    pos_mf = mf.where(tp > tp.shift(1), 0).rolling(14).sum()
    neg_mf = mf.where(tp < tp.shift(1), 0).rolling(14).sum()
    df['mfi'] = 100 - (100 / (1 + pos_mf / (neg_mf + 1e-9)))
    tp_rolling = tp.rolling(20).mean()
    mad = tp.rolling(20).apply(lambda x: np.abs(x - x.mean()).mean())
    df['cci'] = (tp - tp_rolling) / (0.015 * mad + 1e-9)
    df['cmo'] = 100 * (pos_mf - neg_mf) / (pos_mf + neg_mf + 1e-9)
    df['vol_ma'] = vol.rolling(20).mean()
    return df.dropna()

def prepare_cache():
    print("📡 PRE-CACHING MARKET DATA FOR ALL AGENTS...")
    TICKERS = ["SOXL", "TQQQ", "FNGU", "BULZ", "NVDA", "TSLA", "AMD"]
    data_dict = {}
    for t in TICKERS:
        df = yf.download(t, period="2y", interval="1h", progress=False)
        if df.empty: continue
        df.columns = df.columns.get_level_values(0).str.lower() if isinstance(df.columns, pd.MultiIndex) else df.columns.str.lower()
        data_dict[t] = calculate_all_10_indicators(df)
    
    # Save as pickle for fast loading in workers
    pd.to_pickle(data_dict, "market_data_cache.pkl")
    print("✅ CACHE READY: market_data_cache.pkl")

def run_mega_coordinator():
    prepare_cache()
    
    print("\n🔥 MEGA CLUSTER ACTIVATION: 1,000,000 SCENARIOS")
    
    ranges = [
        ("01_Scalp", 0.5, 1.5), ("02_Sniper", 1.5, 3.0), ("03_Swing", 3.0, 5.0),
        ("04_TrendA", 5.1, 8.0), ("05_TrendB", 8.1, 12.0), ("06_WaveA", 12.1, 18.0),
        ("07_WaveB", 18.1, 25.0), ("08_HighBeta", 25.1, 40.0), ("09_MoonshotA", 40.1, 70.0),
        ("10_MoonshotB", 70.1, 100.0)
    ]

    processes = []
    for agent_id, r_min, r_max in ranges:
        p = subprocess.Popen([
            sys.executable, "million_test_worker.py",
            "--agent_id", agent_id, "--range_min", str(r_min), "--range_max", str(r_max)
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        processes.append((agent_id, p))

    while any(p[1].poll() is None for p in processes):
        comp = sum(1 for p in processes if p[1].poll() is not None)
        print(f"Cluster Running... {comp}/10 Ready", end="\r")
        time.sleep(10)

    print("\n✅ ALL AGENTS COMPLETED. ANALYZING DATA...")

if __name__ == "__main__":
    run_mega_coordinator()
