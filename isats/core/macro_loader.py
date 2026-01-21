import pandas as pd
import logging
from typing import Dict

logger = logging.getLogger("MacroLoader")

class MacroLoader:
    def __init__(self):
        self.data_cache = {}

    def load_interest_rates(self, start_date: str) -> pd.DataFrame:
        """Mock method to load interest rate data (Fed/BOK)."""
        logger.info("Loading Interest Rate Data...")
        # Return mock DataFrame with Date / Rate columns
        return pd.DataFrame()

    def load_exchange_rates(self, currency_pair="USD/KRW") -> pd.DataFrame:
        """Mock method to load exchange rates."""
        logger.info(f"Loading Exchange Rates for {currency_pair}...")
        return pd.DataFrame()

    def load_news_sentiment(self, code: str) -> pd.DataFrame:
        """
        Mock method to load news sentiment scores.
        Columns: [datetime, sentiment_score, impact_label]
        """
        logger.info(f"Loading News Sentiment for {code}...")
        return pd.DataFrame()

    def get_macro_context(self, date_str: str) -> Dict[str, float]:
        """Returns macro snapshot for a specific date."""
        return {
            "interest_rate": 3.50,
            "usd_krw": 1300.0,
            "market_sentiment": 0.65 # 0-1 scale
        }
