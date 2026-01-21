import pandas as pd
import numpy as np
import os
import sys
import yfinance as yf
import random
import logging

# Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ISATS_MicroMiner")

class MicroGeneticMiner:
    def __init__(self):
        self.results = []
        
    def fetch_data(self, ticker):
        try:
            df = yf.download(ticker, period="5d", interval="1m", progress=False)
            if df.empty: return None
            
            # --- FIX: Handle Tuple Columns (MultiIndex) ---
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [c[0].lower() if isinstance(c, tuple) else c.lower() for c in df.columns]
            else:
                df.columns = [c.lower() for c in df.columns]

            if 'date' in df.columns: df.set_index('date', inplace=True)
            df.index = pd.to_datetime(df.index)
            df.rename(columns={'adj close': 'close', 'adjclose': 'close'}, inplace=True)
            return df
        except: return None

    def backtest_gene(self, df, trend_win, squeeze_win, trigger_win):
        """
        Tests a specific set of genes (Timeframes).
        """
        close = df['close']
        
        # 1. Macro Trend (EMA)
        ema = close.ewm(span=trend_win, adjust=False).mean()
        
        # 2. Squeeze (Bollinger Width)
        sma = close.rolling(window=squeeze_win).mean()
        std = close.rolling(window=squeeze_win).std()
        bbw = (std * 4) / sma
        
        # 3. Trigger (RSI-like Momentum)
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=trigger_win).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=trigger_win).mean()
        rs = gain / loss
        rsi_trigger = 100 - (100 / (1 + rs))

        trades = 0
        wins = 0
        total_profit = 0.0

        for i in range(max(trend_win, squeeze_win), len(df)-10):
            try:
                # Entry Logic
                # Trend is UP (Price > EMA)
                if not (close.iloc[i] > ema.iloc[i]): continue
                
                # Squeeze is ON (Width < 0.2%)
                if bbw.iloc[i] > 0.002: continue
                
                # Trigger Fired (RSI Cross UP 30 - Bounce)
                if not (rsi_trigger.iloc[i] > 30 and rsi_trigger.iloc[i-1] <= 30): continue
                
                # EXECUTE TRADE
                entry_price = close.iloc[i]
                # Exit after 5 mins (Scalping)
                exit_price = close.iloc[i+5]
                
                profit = (exit_price - entry_price) / entry_price
                trades += 1
                total_profit += profit
                if profit > 0: wins += 1
                
            except: continue
            
        if trades < 5: return -100, 0, 0 # Return tuple to match unpack
        
        win_rate = (wins / trades) * 100
        avg_profit = (total_profit / trades) * 100
        
        # Fitness Score: Win Rate * Profitability
        score = win_rate * avg_profit
        return score, win_rate, trades

    def run_mining(self):
        ticker = "NVDA" # Use the King of Volatility for mining
        df = self.fetch_data(ticker)
        if df is None: return
        
        logger.info(f"🧬 Mining 'Hidden Gems' on {ticker} 1-Minute Data ({len(df)} candles)...")
        
        best_genes = None
        best_score = -9999
        
        # Genetic Loop (Monte Carlo)
        # Search Space:
        # Trend: 20 mins ~ 240 mins (4 hours)
        # Squeeze: 5 mins ~ 30 mins
        # Trigger: 2 mins ~ 10 mins
        
        for i in range(500):
            t_win = random.choice([21, 34, 55, 75, 89, 100, 112, 144, 200, 233])
            s_win = random.choice([5, 8, 13, 17, 21, 26])
            tr_win = random.choice([2, 3, 4, 5, 7])
            
            score, win_rate, trades = self.backtest_gene(df, t_win, s_win, tr_win)
            
            if score > best_score:
                best_score = score
                best_genes = (t_win, s_win, tr_win)
                logger.info(f"💎 New Discovery! Genes: Trend={t_win}m / Squeeze={s_win}m / Trigger={tr_win}m | WinRate: {win_rate:.1f}% ({trades} Trades)")
                
        print("\n" + "="*40)
        print("🏆 OPTIMAL SCALPING FORMULA FOUND")
        print(f"Trend Gene: {best_genes[0]}m (vs 55m)")
        print(f"Squeeze Gene: {best_genes[1]}m (vs 8m)")
        print(f"Trigger Gene: {best_genes[2]}m (vs 3m)")
        print(f"Score: {best_score:.2f}")
        print("="*40 + "\n")

if __name__ == "__main__":
    miner = MicroGeneticMiner()
    miner.run_mining()
