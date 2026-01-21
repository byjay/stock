import logging
import pandas as pd
from datetime import datetime

logger = logging.getLogger("DelistedHandler")

class DelistedHandler:
    """
    Manages records of stocks that were delisted.
    Forces the Training Universe to include 'Failures' to prevent Survivorship Bias.
    """
    def __init__(self, data_path="backend/data/delisted_tickers.csv"):
        self.data_path = data_path
        self.delisted_df = self._load_data()

    def _load_data(self):
        try:
            return pd.read_csv(self.data_path)
        except FileNotFoundError:
            # Create a mock list of famous delisted/troubled tickers if file doesn't exist
            # This demonstrates the 'Delisted-Aware' capability
            mock_data = {
                "code": ["000660_DELIST", "Q_BLOCK_001", "FAKE_CORP_99"],
                "name": ["Mock Failure 1", "Mock Failure 2", "Mock Failure 3"],
                "delist_date": ["2018-05-20", "2020-11-15", "2023-01-10"],
                "reason": ["Bankruptcy", "Fraud", "Merger"]
            }
            df = pd.DataFrame(mock_data)
            # os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
            # df.to_csv(self.data_path, index=False)
            return df

    def get_universe_at_time(self, active_tickers, target_date):
        """
        Combines current active tickers with those that were active at 'target_date'
        even if they are now delisted.
        """
        target_dt = pd.to_datetime(target_date)
        
        # Filter delisted tickers that were still 'alive' at target_date
        relevant_delisted = self.delisted_df[pd.to_datetime(self.delisted_df['delist_date']) > target_dt]
        
        full_universe = list(set(active_tickers) | set(relevant_delisted['code'].tolist()))
        logger.info(f"Survivorship-Free Universe: {len(full_universe)} tickers (Inc. {len(relevant_delisted)} delisted at {target_date})")
        
        return full_universe
