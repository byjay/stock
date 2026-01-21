import asyncio
import logging
import pandas as pd
import sys
import time
from datetime import datetime
import warnings

# Suppress warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=UserWarning)

# Config Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("RealBacktest1000")

# Import Backend
from backend.core.korea_inv_wrapper import KoreaInvWrapper
from backend.core.multiplex_engine import MultiplexDecisionEngine
# from backend.core.descision_context import DecisionContext # Removed

# Target Real Tickers (Top Market Cap & Active Volatility Mix)
REAL_TICKERS = [
    "005930", "000660", "373220", "207940", "005380", "000270", "068270", "005490", "035420", "035720", # Top 10 KOSPI
    "006400", "051910", "105560", "055550", "012330", "072020", "015760", "032830", "003550", "034020", # 11-20
    "247540", "086520", "091990", "028300", "293490", "035900", "122870", "066970", "005290", "036570", # KOSDAQ Active
    "000990", "004370", "017670", "010950", "252670", "122630", "114800", "251270", "233740", "000100", # Misc + ETF(Inverse/Lev)
    "011070", "051900", "096770", "011170", "009150", "030000", "032640", "010130", "000810", "010140"  # Diverse
]

async def run_real_backtest():
    logger.info("🚀 Starting 1000-Trade Real Data Backtest...")
    
    # 1. Initialize Wrapper in REAL MODE (No Mock Fallback)
    broker = KoreaInvWrapper(mock_mode=False, allow_mock_fallback=False)
    
    if broker.mock_mode:
        logger.error("❌ CRITICAL: Broker is still in MOCK MODE! Check secrets.yaml or initialization.")
        # Try to proceed anyway if it's just a config fallback issue but we wanted real
        # But for 'real data backtest', mock is useless.
        if "PASTE_YOUR" in broker.app_key:
             logger.error("❌ No Real API Keys found. Cannot perform REAL DATA backtest.")
             return

    multiplex = MultiplexDecisionEngine()
    
    total_trades = 0
    wins = 0
    losses = 0
    total_pnl = 0.0
    
    trade_log = [] # List of {ticker, entry_date, entry_price, exit_date, exit_price, pnl, return_p}

    # 2. Iterate Tickers
    for ticker_idx, ticker in enumerate(REAL_TICKERS):
        if total_trades >= 1100: # Aim for a bit more than 1000
            break
            
        logger.info(f"📊 [{ticker_idx+1}/{len(REAL_TICKERS)}] Fetching History for {ticker}...")
        
        # Fetch 2 years (approx 500 days)
        try:
            raw_data = await broker.fetch_history(ticker, days=700)
        except Exception as e:
            logger.error(f"Fetch error: {e}")
            raw_data = []

        if not raw_data or len(raw_data) < 100:
            logger.warning(f"⚠️ Insufficient Data for {ticker}. Skipping.")
            continue
            
        # Convert to DataFrame
        df = pd.DataFrame(raw_data)
        # KIS keys: stck_bsop_date, stck_oprc, stck_hgpr, stck_lwpr, stck_clpr, acml_vol
        df.rename(columns={
            'stck_bsop_date': 'date',
            'stck_oprc': 'open',
            'stck_hgpr': 'high',
            'stck_lwpr': 'low',
            'stck_clpr': 'close',
            'acml_vol': 'volume'
        }, inplace=True)
        
        df = df.astype({'open': float, 'high': float, 'low': float, 'close': float, 'volume': float})
        df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
        df.sort_values('date', inplace=True)
        # Multiplex Engine needs DatetimeIndex for Resampling
        df.set_index('date', inplace=True)
        # Also needs 'datetime' column for StrategyEngine compatibility sometimes? 
        # But Multiplex handles passing to resampler. Resampler needs index.
        # StrategyEngine needs 'datetime' col sometimes? Let's ensure it exists just in case.
        df['datetime'] = df.index
        
        # 3. Simulate Trading Loop
        position = None # None or {'price': float, 'date': datetime}
        
        # Requires at least 60 days for indicators
        start_idx = 60 
        
        for i in range(start_idx, len(df)):
            current_slice = df.iloc[:i+1].copy()
            current_price = float(current_slice.iloc[-1]['close'])
            current_date = current_slice.index[-1]
            
            # Analyze
            try:
                # Use analyze_ticker which returns a dict
                decision_result = multiplex.analyze_ticker(ticker, current_slice)
                decision_signal = decision_result.get('decision', 'HOLD')
            except Exception as e:
                # logger.warning(f"Err analyzing {ticker}: {e}")
                decision_signal = "HOLD"

            # B. Execute Logic
            if position:
                entry_price = position['price']
                pnl_pct = (current_price - entry_price) / entry_price * 100
                
                # Sell Signal or trailing stop or Hard Stop
                if decision_signal == "SELL" or pnl_pct < -5.0 or pnl_pct > 15.0:  # Hard SL -5%, TP +15%
                    # EXECUTE SELL
                    profit = current_price - entry_price
                    total_pnl += profit
                    trade = {
                        "ticker": ticker,
                        "entry_date": position['date'],
                        "entry_price": entry_price,
                        "exit_date": current_date,
                        "exit_price": current_price,
                        "pnl": profit,
                        "return_p": pnl_pct
                    }
                    trade_log.append(trade)
                    total_trades += 1
                    
                    if profit > 0: wins += 1
                    else: losses += 1
                    
                    position = None
                    # logger.info(f"  🔻 SELL {ticker} @ {current_price} ({pnl_pct:.2f}%)")
                    
            elif decision_signal == "BUY":
                if not position:
                    position = {'price': current_price, 'date': current_date}
                    # logger.info(f"  🔺 BUY {ticker} @ {current_price}")
        
        print(f"   > {ticker}: Trades So Far: {total_trades} | WinRate: {wins/total_trades*100 if total_trades>0 else 0:.1f}%")

    # 4. Final Report
    logger.info("="*50)
    logger.info("📢 FINAL BACKTEST REPORT (Real Data)")
    logger.info("="*50)
    logger.info(f"Total Trades: {total_trades}")
    if total_trades > 0:
        win_rate = (wins / total_trades) * 100
        avg_pnl = total_pnl / total_trades
        logger.info(f"Win Rate: {win_rate:.2f}%")
        logger.info(f"Avg PnL per Trade: {avg_pnl:.2f} KRW")
        
        # Calculate MDD (Simple Proxy)
        cum_pnl = [0]
        for t in trade_log:
            cum_pnl.append(cum_pnl[-1] + t['pnl'])
        
        peak = -999999999
        mdd = 0
        for val in cum_pnl:
            if val > peak: peak = val
            dd = val - peak
            if dd < mdd: mdd = dd
            
        logger.info(f"Max Drawdown (PnL): {mdd:.2f} KRW")
        
        # Save Log
        log_df = pd.DataFrame(trade_log)
        log_df.to_csv("real_backtest_log.csv", index=False)
        logger.info("Saved trade log to real_backtest_log.csv")

    else:
        logger.warning("No trades executed.")

if __name__ == "__main__":
    asyncio.run(run_real_backtest())
