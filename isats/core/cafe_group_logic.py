import re
import json
import logging
from .cafe_repository_manager import cafe_repo

logger = logging.getLogger("CafeGroupLogic")

class CafeGroupLogic:
    """
    The 'Filter & Cluster' Engine:
    Processes raw posts/comments and categorizes them into logic groups.
    """
    def __init__(self, hq):
        self.hq = hq

    def identify_group(self, raw_entry):
        """
        Categorizes a post into logic groups based on keywords and board name.
        """
        title = raw_entry.get("title", "").lower()
        content = raw_entry.get("content", "").lower()
        board = raw_entry.get("board_name", "")

        # 1. Expert Signal Group (High Confidence)
        if "단타매매일지" in title or "수익인증" in title:
            return "EXPERT_SIGNALS"
        
        # 2. Member Analysis Group (Strategic Intelligence)
        if "분석" in title or "차트" in title or board == "분석실":
            return "MEMBER_ANALYSIS"
        
        # 3. Market Sentiment Group (Qualitative Flow)
        if "오늘" in title or "내일" in title or board == "자유게시판":
            return "MARKET_SENTIMENT"

        return "GENERAL_INFO"

    def extract_deep_intelligence(self, raw_entry):
        """
        Filters and extracts actionable tokens for Deep Learning Ingestion.
        """
        group = self.identify_group(raw_entry)
        content = raw_entry.get("content", "")
        
        # Find all stock-like mentions (e.g., [한빛레이저])
        # We look for 2-8 Korean characters followed by common trading suffixes or percentages
        potential_stocks = re.findall(r'([가-힣]{2,8})(\s+[0-9\.]+\s*%)', content)
        
        results = []
        for stock, profit in potential_stocks:
            results.append({
                "group": group,
                "symbol": stock,
                "profit": profit.strip(),
                "original_post_id": raw_entry.get("post_id")
            })
        
        return results

    async def synchronize_all(self):
        """
        Reads ALL raw data and populates the signals table. 
        Ensures NO information is missed.
        """
        import sqlite3
        conn = sqlite3.connect(cafe_repo.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM raw_data")
        raw_rows = cursor.fetchall()
        
        processed_count = 0
        for row in raw_rows:
            signals = self.extract_deep_intelligence(dict(row))
            for sig in signals:
                # Save to 정형 데이터 테이블
                cafe_repo.save_signal(
                    post_id=sig["original_post_id"],
                    symbol_name=sig["symbol"],
                    ticker=self.hq.lookup_ticker(sig["symbol"]), # Link to Ticker
                    sentiment=sig["group"],
                    profit=float(sig["profit"].replace("%","")),
                    reasoning=f"Extracted from Group: {sig['group']}"
                )
            processed_count += 1
        
        conn.close()
        logger.info(f"✅ Group Logic Synced: {processed_count} posts processed.")
        return processed_count

# Integration with HQ:
# self.cafe_logic = CafeGroupLogic(self)
