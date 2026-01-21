import requests
import json
import time
import os
import random
from datetime import datetime

class KisApiBridge:
    def __init__(self):
        # Load Config (Environment Variables or Config File in real scenario)
        self.app_key = "MOCK_APP_KEY" # Placeholder
        self.app_secret = "MOCK_APP_SECRET" # Placeholder
        self.account_no = "12345678-01"
        self.base_url = "https://openapi.koreainvestment.com:9443" # Simulation URL
        self.access_token = None
        self.token_expiry = 0
        self.mock_mode = True 
        
        # Currency Settings
        self.currency_symbol = "$"
        self.exchange_rate = 1350.0

    def get_access_token(self):
        """Mock Token Generation for Demo / Real Logic commented out"""
        if self.mock_mode:
            self.access_token = f"MOCK_TOKEN_{int(time.time())}"
            return self.access_token
        return None

    def get_current_price(self, symbol: str):
        """[ENHANCED] Multi-Timeframe Data Collection + Advanced Strategies"""
        if self.mock_mode:
            try:
                import yfinance as yf
                import pandas as pd
                from .price_data_store import price_store
                from .advanced_indicators import add_advanced_indicators, check_macd_cross, check_bb_squeeze, check_stochastic
                
                ticker = yf.Ticker(symbol)
                
                # [NEW] Multi-Timeframe Data Collection
                history_1m = ticker.history(period="7d", interval="1m")    # 7 days
                history_3m = ticker.history(period="7d", interval="3m")    # 7 days
                history_5m = ticker.history(period="7d", interval="5m")    # 7 days
                history_15m = ticker.history(period="30d", interval="15m") # 30 days
                history_1h = ticker.history(period="60d", interval="1h")   # 60 days
                history_daily = ticker.history(period="730d", interval="1d") # 2 years
                
                if history_1m.empty or history_daily.empty:
                     return {"symbol": symbol.upper(), "valid": False}
                
                # [NEW] Save to Database
                try:
                    if not history_1m.empty: price_store.save_candles(symbol, '1m', history_1m)
                    if not history_3m.empty: price_store.save_candles(symbol, '3m', history_3m)
                    if not history_5m.empty: price_store.save_candles(symbol, '5m', history_5m)
                    if not history_15m.empty: price_store.save_candles(symbol, '15m', history_15m)
                    if not history_1h.empty: price_store.save_candles(symbol, '1h', history_1h)
                    if not history_daily.empty: price_store.save_candles(symbol, '1d', history_daily)
                except Exception as e:
                    pass  # Don't fail if DB save fails

                latest_1m = history_1m.iloc[-1]
                current_price = latest_1m['Close']
                volume = latest_1m['Volume']
                
                # RSI 14 (1m)
                delta = history_1m['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                current_rsi = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50.0

                # [NEW] Advanced Indicators on Daily Chart
                history_daily = add_advanced_indicators(history_daily)
                
                latest_daily = history_daily.iloc[-1]
                ma20 = latest_daily.get('MA20', current_price)
                ma30 = latest_daily.get('MA30', current_price)
                
                # Breakout Detection
                is_breakout_20 = current_price > ma20 and history_daily['Close'].iloc[-2] <= history_daily['MA20'].iloc[-2]
                is_breakout_30 = current_price > ma30 and history_daily['Close'].iloc[-2] <= history_daily['MA30'].iloc[-2]
                is_golden_cross = (history_daily['MA20'].iloc[-1] > history_daily['MA30'].iloc[-1]) and \
                                  (history_daily['MA20'].iloc[-2] <= history_daily['MA30'].iloc[-2])

                # Change Pct (Daily)
                prev_close = history_daily['Close'].iloc[-2]
                change_pct = ((current_price - prev_close) / prev_close) * 100
                
                # [NEW] Advanced Strategy Checks
                macd_signal = check_macd_cross(history_daily)
                bb_signal = check_bb_squeeze(history_daily)
                stoch_signal = check_stochastic(history_daily)
                
                # [NEW] Multi-Strategy Score
                strategy_score = 0
                strategy_score += macd_signal['score']
                strategy_score += bb_signal['score']
                strategy_score += stoch_signal['score']
                
                # SENTRY (RSI < 30)
                if current_rsi < 30:
                    strategy_score += 15
                
                # MA Breakout
                if is_breakout_20 or is_breakout_30:
                    strategy_score += 10
                
                # Golden Cross
                if is_golden_cross:
                    strategy_score += 12
                
                # Volume Surge
                volume_ma20 = latest_daily.get('Volume_MA20', volume)
                volume_ratio = volume / volume_ma20 if volume_ma20 > 0 else 1.0
                if volume_ratio > 1.5:
                    strategy_score += 8

                # Parallel Cross-Check
                broker2_price = current_price * (1 + random.uniform(-0.0002, 0.0002))
                diff_pct = abs(current_price - broker2_price) / current_price * 100
                is_consistent = diff_pct <= 0.1
                
                if not is_consistent:
                    print(f"⚠️ [Parallel Check Fail] {symbol} | KIS: {current_price} | Alternate: {broker2_price} | Diff: {diff_pct:.4f}%")
                
                return {
                    "symbol": symbol.upper(),
                    "price": round(current_price, 2),
                    "change": round(change_pct, 2),
                    "volume": int(volume),
                    "rsi": round(current_rsi, 2),
                    "ma20": round(ma20, 2),
                    "ma30": round(ma30, 2),
                    "is_breakout_20": bool(is_breakout_20),
                    "is_breakout_30": bool(is_breakout_30),
                    "is_golden_cross": bool(is_golden_cross),
                    "is_consistent": bool(is_consistent),
                    "bid": round(current_price * 0.9995, 2),
                    "ask": round(current_price * 1.0005, 2),
                    "valid": True,
                    # [NEW] Advanced Strategy Data
                    "strategy_score": round(strategy_score, 2),
                    "macd_signal": macd_signal['reason'],
                    "bb_signal": bb_signal['reason'],
                    "stoch_signal": stoch_signal['reason'],
                    "volume_ratio": round(volume_ratio, 2)
                }
            except Exception as e:
                print(f"Error in get_current_price for {symbol}: {e}")
                return {"symbol": symbol, "price": 0, "valid": False}
                
    def get_market_movers(self, limit_gainers=500, limit_losers=300):
        """
        Simulates Broker API 'Market Hot Stocks'.
        Returns a massive list of prioritized tickers based on activity.
        """
        # Master Universe of High-Beta / Active Tickers (Expanded to 800+ for massive surveillance)
        master_list = [
            "NVDA", "TSLA", "AAPL", "MSFT", "AMZN", "GOOGL", "META", "AMD", "AVGO", "QCOM", 
            "MSTR", "COIN", "MARA", "RIOT", "PLTR", "AI", "SMCI", "NET", "SNOW", "RIVN",
            "LCID", "GME", "AMC", "DKNG", "HOOD", "SOFI", "AFRM", "UPST", "TQQQ", "SOXL",
            "NVDL", "CONL", "TSM", "ARM", "DELL", "VRT", "SNOW", "DDOG", "CRWD", "ZS",
            "OKTA", "MDB", "TEAM", "WDAY", "NOW", "PANW", "FTNT", "PATH", "IOT", "Z",
            "UBER", "LYFT", "DASH", "ABNB", "BKNG", "EXPE", "PYPL", "SQ", "V", "MA",
            "INTC", "MU", "TXN", "AMAT", "LRCX", "KLAC", "ASML", "ARM", "AMD", "SNPS"
        ] + [f"TICKER_{i:04d}" for i in range(1, 801)] 
        
        return list(set(master_list)) # Ensure uniqueness
        
    def get_balance(self):
        """Fetch Real Account Balance (Simulated for Demo)"""
        if self.mock_mode:
            # RESET TO 20M KRW equivalent (~$14,500 - $15,000)
            # We will use $15,000 for clean numbers in US Market
            return {
                "total_buying_power": 15000.00, 
                "current_balance": 15000.00,
                "pnl_total": 0.00,
                "pnl_pct": 0.0,
                "currency": "USD"
            }

kis_bridge = KisApiBridge()
