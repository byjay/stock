
import pandas as pd
import logging
from datetime import datetime, timedelta
import os
import json
from typing import Dict, Optional, List

# Setup logging
logger = logging.getLogger("GlobalDataLake")
logger.setLevel(logging.INFO)

class GlobalDataLake:
    """
    The Single Source of Truth for 'Identity' and 'Fundamental Context' of stocks.
    Answers: "Who is this stock?", "What do they do?", "Are they cheap?", "Are they profitable?"
    
    Supports: KRX (via pykrx), US (via yfinance)
    """
    
    def __init__(self, cache_dir="./data/master_db"):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # In-memory Master Data
        self.krx_master: pd.DataFrame = pd.DataFrame()
        self.us_master: pd.DataFrame = pd.DataFrame()
        
        # Cache paths
        self.krx_cache_path = os.path.join(self.cache_dir, "krx_master.csv")
        self.us_cache_path = os.path.join(self.cache_dir, "us_master.csv")
        
        # Status
        self.last_update = None
        self.initialized = False

    def initialize(self):
        """Loads data from cache or fetches fresh if cache is stale/missing."""
        logger.info("[GlobalDataLake] Initializing Master Data Lake...")
        
        # Try load KRX
        if os.path.exists(self.krx_cache_path):
            try:
                # Check modification time
                mod_time = datetime.fromtimestamp(os.path.getmtime(self.krx_cache_path))
                if datetime.now() - mod_time < timedelta(hours=24):
                    self.krx_master = pd.read_csv(self.krx_cache_path, dtype={'Ticker': str})
                    self.krx_master.set_index('Ticker', inplace=True)
                    logger.info(f"[GlobalDataLake] Loaded KRX Master from cache ({len(self.krx_master)} tickers).")
                    self.initialized = True
                    return
            except Exception as e:
                logger.warning(f"[GlobalDataLake] Failed to load cache: {e}")

        # If we reached here, we need to fetch fresh data
        self.refresh_master_data()
        self.initialized = True

    def refresh_master_data(self):
        """Fetches fresh data using FinanceDataReader (FDR)."""
        logger.info("[GlobalDataLake] 🌏 Fetching FRESH Master Data using FinanceDataReader...")
        
        try:
            import FinanceDataReader as fdr
            
            # 1. Fetch KRX (KOSPI + KOSDAQ + KONEX)
            # FDR is very robust and handles the scraping internally
            df_master = fdr.StockListing('KRX')
            
            logger.info(f"[GlobalDataLake] Raw FDR fetch: {len(df_master)} rows.")
            
            # 2. Standardize Columns
            # FDR Columns: [Code, ISIN, Name, Market, Dept, Close, ChangeCode, Changes, ChagesRatio, Open, High, Low, Volume, Amount, Marcap, Stocks, MarketId]
            # We need: Index=Ticker, Name, MarketCap, Sector(optional), PER/PBR(optional)
            
            # Rename 'Code' to 'Ticker' and set index
            if 'Code' in df_master.columns:
                df_master['Ticker'] = df_master['Code']
                df_master.set_index('Ticker', inplace=True)
            elif 'Symbol' in df_master.columns:
                 df_master['Ticker'] = df_master['Symbol']
                 df_master.set_index('Ticker', inplace=True)

            # Map Columns
            rename_map = {
                'Marcap': 'MarketCap',
                'Stocks': 'Shares',
                'Amount': 'TradingValue',
                'Dept': 'Sector', # Sometimes Dept is not Sector, but closest
            }
            # FDR sometimes has 'Sector' column explicitly
            if 'Sector' not in df_master.columns and 'Industry' in df_master.columns:
                rename_map['Industry'] = 'Sector'
                
            cols_to_rename = {k: v for k, v in rename_map.items() if k in df_master.columns}
            df_master = df_master.rename(columns=cols_to_rename)
            
            # Ensure critical columns exist
            required_cols = ['Name', 'MarketCap']
            for col in required_cols:
                if col not in df_master.columns:
                    df_master[col] = 0 # Fill missing
            
            # PER/PBR might be missing from simple listing. 
            # We can try to use pykrx for JUST fundamentals if needed, or leave it for now.
            # Diversity (Name/MarketCap) is priority.
            if 'PER' not in df_master.columns:
                df_master['PER'] = 0.0
            if 'PBR' not in df_master.columns:
                df_master['PBR'] = 0.0
                
            # Filter valid tickers (numeric only for KRX usually, strict check)
            # FDR might return some weird ones
            
            self.krx_master = df_master
            self.krx_master.to_csv(self.krx_cache_path)
            logger.info(f"[GlobalDataLake] ✅ KRX Master Data Updated via FDR: {len(self.krx_master)} stocks.")

        except Exception as e:
            logger.error(f"[GlobalDataLake] ❌ Critical Error fetching KRX data via FDR: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            
            # Fallback
            self.krx_master = pd.DataFrame(columns=['Name', 'MarketCap', 'PER', 'PBR'])

    def get_identity(self, ticker: str) -> Dict:
        """
        Returns the 'Identity Card' of a stock.
        """
        if not self.initialized:
            self.initialize()
            
        # Check KRX
        if ticker in self.krx_master.index:
            row = self.krx_master.loc[ticker]
            return {
                "ticker": ticker,
                "name": str(row.get('Name', 'Unknown')),
                "market": "KRX",
                "market_cap": float(row.get('MarketCap', 0)),
                "per": float(row.get('PER', 0)),
                "pbr": float(row.get('PBR', 0)),
                "status": "Active" # Placeholder
            }
        
        # TODO: Check US
        
        return {"ticker": ticker, "name": "Unknown", "market": "Unknown", "status": "Unknown"}

    def is_investable(self, ticker: str, min_market_cap=100000000000) -> bool:
        """
        Policy: Do we play with this friend?
        Rule: Filters out penny stocks (e.g., Market Cap < 100B KRW) or dangerous stocks.
        """
        identity = self.get_identity(ticker)
        if identity['status'] == 'Unknown':
            return False
            
        cap = identity.get('market_cap', 0)
        # 100 Billion KRW ~ 80M USD
        if cap < min_market_cap:
            return False
            
        return True
