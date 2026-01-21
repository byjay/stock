import sqlite3
import pandas as pd
import logging
from datetime import datetime
import os

logger = logging.getLogger("DataHandler")

class DataHandler:
    def __init__(self, db_path="market_data.db"):
        self.db_path = db_path
        self._initialize_db()

    def _initialize_db(self):
        """Creates the necessary tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # OHLCV Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ohlcv (
                code TEXT,
                datetime TEXT,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER,
                PRIMARY KEY (code, datetime)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")

    def save_candle(self, code, datetime_str, open_p, high_p, low_p, close_p, volume):
        """Saves a single candle to the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO ohlcv (code, datetime, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (code, datetime_str, open_p, high_p, low_p, close_p, volume))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to save candle: {e}")

    def get_price_data(self, code, start_date=None, end_date=None):
        """Retrieves price data as a Pandas DataFrame."""
        conn = sqlite3.connect(self.db_path)
        
        query = f"SELECT * FROM ohlcv WHERE code = '{code}'"
        if start_date:
            query += f" AND datetime >= '{start_date}'"
        if end_date:
            query += f" AND datetime <= '{end_date}'"
        
        query += " ORDER BY datetime ASC"
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return df
