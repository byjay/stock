import asyncio
import logging
from backend.core.korea_inv_wrapper import KoreaInvWrapper
from backend.core.dynamic_universe import DynamicUniverseManager

logger = logging.getLogger("RealtimeScanner")

class RealtimeScanner:
    """
    [Predator Eye]
    Scans the market for volatility/volume anomalies and feeds the Dynamic Universe.
    """
    def __init__(self, broker: KoreaInvWrapper, universe_mgr: DynamicUniverseManager):
        self.broker = broker
        self.universe = universe_mgr
        
    async def scan_market(self):
        """
        Fetches Top Gainers/Losers and adds them to watchlist.
        """
        try:
            # 1. Fetch Top Gainers (Volatility Sources)
            gainers = await self.broker.fetch_upper_limit_ranking()
            
            count = 0
            for item in gainers[:10]: # Top 10 only
                code = item['mksc_shrn_iscd']
                name = item['hts_kor_isnm']
                price = float(item['stck_prpr'])
                rate = float(item['prdy_ctrt'])
                
                # Filter: Price > 1000 KRW (Avoid Penny Stocks if preferred)
                if price < 1000: continue
                
                self.universe.add_target(code, f"Top Gainer (+{rate}%)", price)
                count += 1
                
            if count > 0:
                logger.info(f"👀 [SCAN] Discovered {count} new hot targets.")
                
        except Exception as e:
            logger.error(f"Scan Error: {e}")
