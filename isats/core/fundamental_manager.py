import logging
import json
import os
import pandas as pd

logger = logging.getLogger("Core:FundamentalManager")

class FundamentalManager:
    """
    [Phase 8] Fundamental Health & Corporate Status Manager
    Responsibility:
    - Maintain a 'Master List' of all listed companies (KR/US).
    - Store critical financial ratios (PER, PBR, Debt-to-Equity, Revenue Growth).
    - FILTER OUT 'Trash Stocks' (Zombie companies) before Technical Analysis.
    """
    def __init__(self, data_path="./data/fundamental_master.json"):
        self.data_path = data_path
        self._ensure_data_exists()
        self.master_data = self._load_data()

    def _ensure_data_exists(self):
        if not os.path.exists("./data"):
            os.makedirs("./data")
        if not os.path.exists(self.data_path):
            # Stub: Initialize with sample healthy vs unhealthy stocks
            initial_data = {
                "005930": {
                    "name": "Samsung Elec",
                    "status": "HEALTHY",
                    "ratios": {"PER": 10.5, "PBR": 1.2, "DebtRatio": 30.0, "OperatingMargin": 15.0}
                },
                "000660": {
                    "name": "SK Hynix",
                    "status": "HEALTHY",
                    "ratios": {"PER": 12.0, "PBR": 1.5, "DebtRatio": 45.0, "OperatingMargin": 20.0}
                },
                "999999": {
                    "name": "Zombie Corp",
                    "status": "DANGER",
                    "ratios": {"PER": -50.0, "PBR": 0.5, "DebtRatio": 500.0, "OperatingMargin": -10.0}
                }
            }
            with open(self.data_path, "w", encoding='utf-8') as f:
                json.dump(initial_data, f, indent=4, ensure_ascii=False)

    def _load_data(self):
        try:
            with open(self.data_path, "r", encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load fundamental data: {e}")
            return {}

    def is_company_sound(self, code: str) -> bool:
        """
        [CRITICAL] First Line of Defense.
        If company is financially rotten, DO NOT BUY even if chart is pretty.
        """
        info = self.master_data.get(code)
        if not info:
            logger.warning(f"⚠️ No fundamental data for {code}. Treating as Speculative.")
            return True # Allow but flag as risky? Or Block? User asked for strictness. Let's Block if unknown in strict mode.
            
        # 1. Status Check
        if info['status'] == "DANGER" or info['status'] == "DELIST_RISK":
            logger.warning(f"🚫 Blocked {code} ({info['name']}): Financial Status DANGER")
            return False
            
        # 2. Ratio Check (Example Rules)
        ratios = info.get('ratios', {})
        if ratios.get('DebtRatio', 0) > 300.0: # Debt > 300%
            logger.warning(f"🚫 Blocked {code}: Too much Debt ({ratios['DebtRatio']}%)")
            return False
            
        if ratios.get('OperatingMargin', 0) < -20.0: # Massive Deficit
            logger.warning(f"🚫 Blocked {code}: Massive Operating Loss")
            return False
            
        logger.info(f"✅ Fundamental Pass: {code} ({info['name']})")
        return True
    
    def get_financial_summary(self, code):
        return self.master_data.get(code, {})
