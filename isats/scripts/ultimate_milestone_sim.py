import pandas as pd
import yfinance as yf
import numpy as np
import concurrent.futures
from datetime import datetime

# --- ULTIMATE STRATEGIC SETTINGS ---
INITIAL_CAPITAL = 100_000_000
MAX_NORMAL_BET = 30_000_000 # 3000만원 캡
FIXED_COST = 0.0015 # 0.15% (Fee + Slippage)
TAX_RATE = 0.22

# Optimized High-Alpha Universe
TICKERS = ["SOXL", "TQQQ", "FNGU", "BULZ", "NVDA", "TSLA", "AMD", "NFLX", "AVGO", "BOIL", "LABU", "UPRO", "TNA"]

# 85.7% Strategy + Human Confidence Logic
RSI_LEN = 2
NORMAL_ENTRY = 20 # Filter noise
STRONG_ENTRY = 8  # "Lethal" Confidence Point
EMA_LEN = 100
BB_STD = 1.2

STOP_LOSS = 5.0
SPLIT_TP = 2.5 # Efficiency: Higher target to cover fees
FINAL_TP = 7.0 # Aim higher for the secondary wave

def fetch_data(ticker):
    try:
        # Fetch 2 years of 1h data for a long enough horizon to see 1000%
        df = yf.download(ticker, period="2y", interval="1h", progress=False)
        if df.empty: return ticker, []
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0).str.lower()
        else:
            df.columns = df.columns.str.lower()
        df = df.loc[:, ~df.columns.duplicated()]
        
        close = df['close'].squeeze()
        if isinstance(close, pd.DataFrame): close = close.iloc[:, 0]
        
        ema = close.ewm(span=EMA_LEN, adjust=False).mean()
        bb_mid = close.rolling(20).mean()
        bb_s = close.rolling(20).std()
        bb_lower = bb_mid - (BB_STD * bb_s)
        
        delta = close.diff()
        up, down = delta.copy(), delta.copy()
        up[up < 0] = 0; down[down > 0] = 0
        roll_up = up.ewm(alpha=1/RSI_LEN, min_periods=RSI_LEN, adjust=False).mean()
        roll_down = down.abs().ewm(alpha=1/RSI_LEN, min_periods=RSI_LEN, adjust=False).mean()
        rs = roll_up / roll_down
        rsis = 100.0 - (100.0 / (1.0 + rs))
        
        # Pre-calculate signals
        closes, lowers, emas, rsis_v = close.values, bb_lower.values, ema.values, rsis.values
        times = df.index
        
        trades = []
        i = max(EMA_LEN, 20)
        while i < len(df) - 10:
            # 1. Normal Signal (RSI < 20)
            if rsis_v[i] < NORMAL_ENTRY and closes[i] < lowers[i] and closes[i] > emas[i]:
                # Confidence Level
                is_strong = (rsis_v[i] < STRONG_ENTRY)
                
                entry_p = float(closes[i])
                entry_t = times[i]
                pos, realized_pnl, highest_p = 1.0, 0.0, entry_p
                
                # Split-Exit Simulation
                for j in range(i+1, min(i+100, len(df))): # Shorter window for hourly
                    curr_p = float(closes[j])
                    pnl = (curr_p - entry_p) / entry_p * 100
                    highest_p = max(highest_p, curr_p)
                    mx_pnl = (highest_p - entry_p) / entry_p * 100
                    
                    if pnl <= -STOP_LOSS:
                        realized_pnl += pos * pnl
                        pos = 0; break
                    if pos == 1.0 and pnl >= SPLIT_TP:
                        realized_pnl += 0.5 * pnl
                        pos = 0.5
                    if pos > 0 and pnl >= FINAL_TP:
                        realized_pnl += pos * pnl
                        pos = 0; break
                    if pos > 0 and mx_pnl >= max(SPLIT_TP, 1.0):
                        if (highest_p - curr_p) / highest_p * 100 >= 1.0: # Trailing
                            realized_pnl += pos * pnl
                            pos = 0; break
                
                if pos > 0:
                    realized_pnl += pos * ((float(closes[min(i+100, len(df)-1)]) - entry_p) / entry_p * 100)
                
                trades.append({
                    'ticker': ticker,
                    'time': entry_t,
                    'exit_time': times[min(j, len(df)-1)],
                    'pnl': realized_pnl,
                    'strong': is_strong
                })
                i = j
            i += 1
        return ticker, trades
    except Exception as e:
        return ticker, []

def run_ultimate_sim():
    print(f"--- ULTIMATE QUANTUM LEAP SIMULATION (2YR DATA) ---")
    print(f"> Rules: Strong Signal(70% Bet) | Normal Signal(10% up to 30M)")
    print(f"> Constraints: Parallel Slots (Max 10), Fee 0.15%, Tax 22%\n")
    
    all_signals = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch_data, t) for t in TICKERS]
        for f in concurrent.futures.as_completed(futures):
            ticker, trades = f.result()
            all_signals.extend(trades)

    all_signals.sort(key=lambda x: x['time'])
    
    equity = INITIAL_CAPITAL
    slots = [None] * 10
    milestones = {100: "2X", 200: "3X", 300: "4X", 400: "5X", 500: "6X", 1000: "11X"}
    reached = set()
    
    executed_trades = 0
    total_vol = 0
    
    for t in all_signals:
        # Slot check
        available_idx = -1
        for s_idx in range(len(slots)):
            if slots[s_idx] is None or slots[s_idx] <= t['time']:
                available_idx = s_idx
                break
        
        if available_idx == -1: continue # All slots full
        
        # HUMAN SIZING LOGIC
        if t['strong']:
            bet = equity * 0.7
            mode = "🔥 STRONG"
        else:
            bet = min(equity * 0.1, MAX_NORMAL_BET)
            mode = "🛡️ NORMAL"
            
        # PnL Calculation
        net_pct = (t['pnl'] / 100) - FIXED_COST
        profit = bet * net_pct
        equity += profit
        total_vol += (bet * 2)
        executed_trades += 1
        slots[available_idx] = t['exit_time']
        
        # Milestone Marking
        roi = (equity - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100
        for m, label in milestones.items():
            if roi >= m and m not in reached:
                print(f"🚩 [{label} 마일스톤 돌파] 자산: {equity:,.0f} KRW | ROI: {roi:.1f}% | Mode: {mode} ({t['ticker']}) | 시점: {t['time']}")
                reached.add(m)
                
    net_pnl = equity - INITIAL_CAPITAL
    tax = max(0, net_pnl * TAX_RATE)
    final_net = equity - tax
    
    print("\n" + "="*60)
    print(f"총 매매 횟수:     {executed_trades} 회")
    print(f"총 거래 대금:     {total_vol:,.0f} KRW")
    print("-" * 60)
    print(f"세전 최종 자산:   {equity:,.0f} KRW")
    print(f"납부 예상 세금:   -{tax:,.0f} KRW (22%)")
    print(f"세후 최종 자산:   {final_net:,.0f} KRW")
    print(f"세후 최종 수익률: {(final_net - INITIAL_CAPITAL)/INITIAL_CAPITAL*100:.2f}%")
    print("="*60)

if __name__ == "__main__":
    run_ultimate_sim()
