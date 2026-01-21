
import asyncio
import random
import logging
from datetime import datetime, timedelta

# Mock Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DataCollector")

class HistoricalDataCollector:
    """
    Background worker that fetches historical data (News, Disclosures, Prices)
    while respecting API rate limits.
    """
    def __init__(self):
        self.is_running = False
        self.targets = ["NVDA", "TSLA", "AAPL", "MSFT", "AMD"]
        self.years_back = 3
        self.request_delay = 1.5 # Seconds between requests to prevent overload
    
    async def start(self):
        self.is_running = True
        logger.info("📡 [DataCollector] Starting Historical Scan (3 Years Back)...")
        asyncio.create_task(self._run_collection_loop())

    async def stop(self):
        self.is_running = False
        logger.info("🛑 [DataCollector] Stopped.")

    async def _run_collection_loop(self):
        """
        Sequential collection logic:
        Iterate years -> Iterate months -> Iterate tickers -> Fetch -> Sleep
        """
        current_date = datetime.now()
        start_date = current_date - timedelta(days=365 * self.years_back)
        
        # Simulation loop
        check_date = start_date
        
        while self.is_running and check_date < current_date:
            for symbol in self.targets:
                if not self.is_running: break
                
                # Mock API Call
                await self._fetch_news(symbol, check_date)
                await self._fetch_disclosure(symbol, check_date)
                
                # Rate Limit Sleep
                await asyncio.sleep(self.request_delay)
            
            # Advance time (speed up for demo: 1 loop = 1 week of data)
            check_date += timedelta(weeks=1)
            print(f"📚 [DataMining] Completed Indexing for Week: {check_date.strftime('%Y-%m-%d')} | Data Synced to Cloud.")

    async def _fetch_news(self, symbol, date):
        # Simulate API Latency
        await asyncio.sleep(0.1)
        # Randomly find something
        if random.random() > 0.8:
            print(f"📰 [NEWS] Found Archive: {symbol} - 'Major announcement...' ({date.strftime('%Y-%m-%d')})")

    async def _fetch_disclosure(self, symbol, date):
        await asyncio.sleep(0.1)
        if random.random() > 0.9:
            print(f"📄 [DISCLOSURE] 10-K/Q Filing Detected: {symbol} ({date.strftime('%Y-%m-%d')})")

# Singleton
data_collector = HistoricalDataCollector()
