import logging
from datetime import datetime, time
import pytz

logger = logging.getLogger("Core:GlobalMarket")

class MarketSessionManager:
    """
    Handles Global Market Sessions (KR, US) and Phases (Pre, Main, Post).
    """
    def __init__(self):
        self.tz_kr = pytz.timezone('Asia/Seoul')
        self.tz_us = pytz.timezone('America/New_York')

    def get_session_status(self):
        now_kr = datetime.now(self.tz_kr)
        now_us = datetime.now(self.tz_us)
        
        status = {
            "KR": self._check_kr(now_kr),
            "US": self._check_us(now_us)
        }
        return status

    def _check_kr(self, now):
        # KR: 09:00 ~ 15:30
        current_time = now.time()
        if time(8, 30) <= current_time < time(9, 0):
            return "PRE_MARKET"
        elif time(9, 0) <= current_time < time(15, 30):
            return "MAIN_SESSION"
        else:
            return "CLOSED"

    def _check_us(self, now):
        # US: 04:00~09:30 (Pre), 09:30~16:00 (Main)
        current_time = now.time()
        if time(4, 0) <= current_time < time(9, 30):
            return "PRE_MARKET"
        elif time(9, 30) <= current_time < time(16, 0):
            return "MAIN_SESSION"
        else:
            return "CLOSED"

class GlobalScanner:
    """
    [Phase 6 Stub]
    Scans Top Traded Stocks in US/KR.
    """
    def get_top_traded(self, market="KR", limit=10):
        # Connect to Data Pipeline in real implementation
        if market == "KR":
            return ["005930", "000660", "035420"] # Samsung, SK Hynix, Naver
        elif market == "US":
            return ["NVDA", "TSLA", "AAPL", "AMD", "MSFT"]
        return []
