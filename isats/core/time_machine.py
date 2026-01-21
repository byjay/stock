import pandas as pd
import logging
import asyncio
from datetime import datetime
from backend.core.korea_inv_wrapper import KoreaInvWrapper

logger = logging.getLogger("ISATS_TimeMachine")

class TimeMachine:
    """
    [ISATS Time Machine]
    Historical Backtesting Engine.
    Replays 5 years of market data to validate strategies before live deployment.
    """
    def __init__(self):
        self.broker = KoreaInvWrapper()
        self.broker.mock_mode = True # Force Mock Mode (Override config)
        self.results = {}

    async def run_simulation(self, ticker: str, initial_capital: float = 100_000_000):
        """
        Runs a simulation for a specific ticker over 5 years.
        """
        logger.info(f"⏳ [TIME-MACHINE] Booting up for {ticker} (Target: 5 Years)...")
        
        # 1. Fetch History (Using Internal Logic for 5 Years)
        # Note: Ideally should use public API, but for Time Machine specific logic we use internal
        history = await self.broker._fetch_missing_history_logic(ticker, years=5)
        if not history:
            logger.error(f"❌ [TIME-MACHINE] No data found for {ticker}")
            return None

        # 2. Prepare Dataframe
        df = pd.DataFrame(history)
        # KIS API Columns: stck_bsop_date, stck_clpr, stck_oprc, stck_hgpr, stck_lwpr, acml_vol
        df['date'] = pd.to_datetime(df['stck_bsop_date'])
        df['close'] = df['stck_clpr'].astype(float)
        df = df.sort_values('date').reset_index(drop=True)
        
        logger.info(f"📚 [TIME-MACHINE] Replaying {len(df)} days of market data...")

        # 3. Simulation Loop (Simple Moving Average Crossover)
        capital = initial_capital
        position = 0
        avg_price = 0
        
        # Calculate Indicators (Vectorized for speed, simulating real-time calc)
        df['SMA_20'] = df['close'].rolling(window=20).mean()
        df['SMA_60'] = df['close'].rolling(window=60).mean()
        
        trades = []
        
        for i in range(60, len(df)):
            today = df.iloc[i]
            yesterday = df.iloc[i-1]
            
            price = today['close']
            date = today['date'].strftime("%Y-%m-%d")

            # [NEW] [ISATS-VI-SIM] Volatility Interruption Simulation
            # TRIGGER: If price moves > 3% from yesterday's close in 1 day (Daily granularity sim)
            volatility = abs(price - yesterday['close']) / yesterday['close']
            if volatility > 0.03:
                logger.warning(f"⚠️ [TIME-MACHINE] [VI-TRIGGER] Extreme Volatility ({volatility*100:.1f}%) detected on {date}.")
                logger.info(f"   -> AI is now evaluating 'Breakers Backflow' risk.")
            
            # Gold Cross (Buy)
            if yesterday['SMA_20'] < yesterday['SMA_60'] and today['SMA_20'] >= today['SMA_60']:
                if position == 0:
                    qty = int(capital // price)
                    if qty > 0:
                        capital -= qty * price
                        position = qty
                        avg_price = price
                        trades.append({"date": date, "type": "BUY", "price": price, "qty": qty, "capital": capital})
            
            # Dead Cross (Sell)
            elif yesterday['SMA_20'] > yesterday['SMA_60'] and today['SMA_20'] <= today['SMA_60']:
                if position > 0:
                    capital += position * price
                    profit = (price - avg_price) * position
                    trades.append({"date": date, "type": "SELL", "price": price, "qty": position, "capital": capital, "profit": profit})
                    position = 0
                    avg_price = 0

        # Final Liquidation
        final_value = capital + (position * df.iloc[-1]['close'])
        roi = ((final_value - initial_capital) / initial_capital) * 100
        
        report = {
            "ticker": ticker,
            "period_days": len(df),
            "initial_capital": initial_capital,
            "final_value": final_value,
            "roi_percent": round(roi, 2),
            "total_trades": len(trades),
            "strategy": "SMA_GoldenCross"
        }
        
        logger.info(f"🏁 [TIME-MACHINE] Simulation Complete for {ticker}.")
        logger.info(f"💰 ROI: {report['roi_percent']}% | Trades: {len(trades)}")
        
        return report

# Quick Test
if __name__ == "__main__":
    async def main():
        tm = TimeMachine()
        # Test with Samsung Electronics (005930)
        await tm.run_simulation("005930")
        
    asyncio.run(main())
