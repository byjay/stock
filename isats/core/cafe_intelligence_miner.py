import re
import logging
from datetime import datetime

logger = logging.getLogger("CafeMiner")

class CafeIntelligenceMiner:
    """
    Expert Sentiment Extractor:
    Scrapes Naver Cafe journals and extracts trading signals.
    """
    def __init__(self, hq):
        self.hq = hq
        self.last_scraped_id = None

    def extract_deep_reasoning(self, content):
        """
        Extracts strategic keywords from the text to use in DL training.
        """
        keywords = {
            "7번 검색식": "SEARCH_FORMULA_7",
            "피봇 2차": "PIVOT_R2_BREAKOUT",
            "눌림목": "NULIM_POINT",
            "상한가": "UPPER_LIMIT_FOLLOW",
            "거래량 폭증": "VOL_SURGE",
            "기관 매집": "INST_BUYING"
        }
        found_logic = []
        for kw, logic_id in keywords.items():
            if kw in content:
                found_logic.append(logic_id)
        return found_logic

    async def inject_expert_signals(self, scraped_posts):
        """
        Processes deep post data and injects rich signals.
        """
        signals_found = 0
        for post in scraped_posts:
            title = post.get("title", "")
            content = post.get("content", "")
            
            signal = self.parse_journal_title(title)
            reasoning = self.extract_deep_reasoning(content)
            
            if signal:
                ticker = self.lookup_ticker(signal["symbol_name"])
                if ticker:
                    # Injected data now includes reasoning for DL ingestion
                    self.hq.bus.publish_signal(
                        ticker, 
                        "EXPERT_SENTIMENT", 
                        {
                            "reason": f"Expert Profit: {signal['profit']}%", 
                            "logic": reasoning,
                            "source": "NaverCafe_DeepResearch"
                        }
                    )
                    logger.info(f"💡 DEEP RESEARCH SIGNAL: [{signal['symbol_name']}] Logic: {reasoning}")
                    signals_found += 1
        return signals_found

    def lookup_ticker(self, name):
        """Mock Ticker Lookup. In real system, use a DB or API."""
        mock_db = {
            "한빛레이저": "S0001",
            "한라IMS": "S0002",
            "휴림로봇": "S0003",
            "노을": "S0004",
            "두리": "S0005"
        }
        return mock_db.get(name)

# Usage Example:
# miner = CafeIntelligenceMiner(hq)
# await miner.inject_expert_signals(["2025.10.28 단타매매일지(한빛레이저 6.07%, ...)"])
