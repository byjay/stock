import asyncio
import random
import datetime
import logging
from typing import Optional

logger = logging.getLogger("Kiwoom")

class KiwoomConnector:
    def __init__(self, mock_mode: bool = True, data_manager=None, realtime_manager=None):
        self.mock_mode = mock_mode
        self.connected = False
        self.data_manager = data_manager
        self.realtime_manager = realtime_manager # [NEW]
        self._running = False
        
        # Test Stock List for Mock Mode
        self.mock_stocks = ["005930", "000660", "035420", "035720"] # Samsung, SK Hynix, Naver, Kakao
        self.mock_prices = {code: 50000 + random.randint(-1000, 1000) for code in self.mock_stocks}

    async def start_connection(self):
        """Starts the connection process (Real or Mock)."""
        logger.info(f"Initializing Kiwoom Connector (MockMode={self.mock_mode})...")
        
        if self.mock_mode:
            self.connected = True
            self._running = True
            asyncio.create_task(self._mock_data_feed())
        else:
            # TODO: Implement Real PyKiwoom Connection here
            # This usually requires running in a 32-bit Python environment or using a separate process.
            # For this phase, we focus on the architecture, so we will stub this.
            logger.warning("Real connection logic not yet implemented. Switching to MOCK mode.")
            self.mock_mode = True
            await self.start_connection()

    async def disconnect(self):
        self._running = False
        self.connected = False
        logger.info("Kiwoom Connector Disconnected.")

    def get_market_time(self):
        return datetime.datetime.now().isoformat()

    async def _mock_data_feed(self):
        """Simulates real-time tick data stream."""
        logger.info("Starting Mock Data Feed...")
        while self._running:
            for code in self.mock_stocks:
                # Simulate Price Change
                change = random.choice([-100, -50, 0, 50, 100, 200])
                current_price = self.mock_prices[code] + change
                self.mock_prices[code] = current_price
                
                # Create Tick Data Packet
                tick_data = {
                    "code": code,
                    "timestamp": datetime.datetime.now().isoformat(),
                    "price": current_price,
                    "volume": random.randint(1, 100),
                    "change": change
                }
                
                # Send to Data Manager
                if self.data_manager:
                    await self.data_manager.process_tick(tick_data)

    async def _on_receive_real_data(self, code, real_type, real_data):
        """
        [Callback] Handles Real-Time Data (Price, Orderbook, Program).
        """
        if self.realtime_manager:
            if real_type == "주식뉴스":
                # Stub: in real OCX we parse `real_data`
                title = "Sample News Triggered" 
                self.realtime_manager.handle_realtime_news(code, title, "Content...", datetime.datetime.now())
            elif real_type == "VI발동/해제":
                self.realtime_manager.handle_vi_trigger(code, "UP")
            
            # Sleep for random interval (simulating irregualr tick arrival)
            await asyncio.sleep(random.uniform(0.5, 2.0))

