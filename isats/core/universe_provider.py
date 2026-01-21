import os
import csv
import logging

logger = logging.getLogger("ISATS:UniverseProvider")

class UniverseProvider:
    """
    [ISATS Core Component]
    Provides the master list of tradable assets.
    Now upgraded to load the FULL KOSPI/KOSDAQ universe from `krx_master.csv`.
    """
    def __init__(self):
        # Path Priority: 1. krx_master.csv (Full), 2. universe_korea.csv (Top 200), 3. Hardcoded (Fallback)
        self.master_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/master_db/krx_master.csv"))
        self.fallback_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/universe_korea.csv"))
        self.tickers = []
        self._load_universe()

    def _load_universe(self):
        """Loads tickers from the best available source."""
        # 1. Try Full Master DB
        if os.path.exists(self.master_path):
            try:
                with open(self.master_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    # Expected columns: Code, Ticker, Name, Market, ...
                    # Normalize headers or check variations
                    for row in reader:
                        # Clean whitespace from keys just in case
                        row = {k.strip(): v for k, v in row.items() if k}
                        
                        if 'Code' in row:
                            self.tickers.append(row['Code'])
                        elif 'Ticker' in row:
                            self.tickers.append(row['Ticker'])
                        elif 'code' in row:
                            self.tickers.append(row['code'])
                            
                logger.info(f"🌌 [UNIVERSE] Loaded {len(self.tickers)} tickers from Full Master DB.")
                return
            except Exception as e:
                logger.error(f"❌ Failed to load Master DB: {e}")

        # 2. Try Top 200 Fallback
        if os.path.exists(self.fallback_path):
            try:
                with open(self.fallback_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.startswith("#") or not line.strip(): continue
                        parts = line.split(',')
                        if len(parts) >= 1:
                            self.tickers.append(parts[0].strip())
                            
                logger.info(f"⚠️ [UNIVERSE] Loaded {len(self.tickers)} tickers from Fallback (Top 200).")
                return
            except Exception as e:
                logger.error(f"❌ Failed to load Fallback: {e}")

        # 3. Last Resort
        self.tickers = ["005930", "000660"] # Samsung, Hynix
        logger.warning("🚨 [UNIVERSE] Critical Fail. Using Minimal Fallback.")

    def get_all_tickers(self):
        return self.tickers

    def get_kr_top_300(self):
        # Alias for backward compatibility or future filtering
        return self.tickers[:300] if self.tickers else []

    def get_kospi_tickers(self):
        # Ideally filter by market column if available, for now return all
        return self.tickers

    def get_kosdaq_tickers(self):
        return []

    def get_all_from_csv(self):
        return self.tickers
