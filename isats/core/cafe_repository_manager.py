import sqlite3
import datetime
import logging
import os

logger = logging.getLogger("CafeRepo")

class CafeRepositoryManager:
    """
    Persistent Storage for All Cafe Intelligence.
    Handles raw text, extracted signals, and member analysis.
    """
    def __init__(self, db_path="data/cafe_intelligence.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table 1: Raw Posts & Comments
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS raw_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id TEXT UNIQUE,
                board_name TEXT,
                author TEXT,
                title TEXT,
                content TEXT,
                comments TEXT,
                scraped_at TIMESTAMP
            )
        ''')
        
        # Table 2: Extracted Logic & Signals (Cleaned)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS extracted_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id TEXT,
                symbol_name TEXT,
                ticker TEXT,
                sentiment TEXT, -- e.g., 'BULLISH', 'BEARISH', 'SUCCESS_RECAP'
                profit_pct REAL,
                reasoning TEXT,
                extracted_at TIMESTAMP,
                FOREIGN KEY(post_id) REFERENCES raw_data(post_id)
            )
        ''')
        
        conn.commit()
        conn.close()

    def save_raw_post(self, post_id, board, author, title, content, comments=""):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO raw_data 
                (post_id, board_name, author, title, content, comments, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (post_id, board, author, title, content, comments, datetime.datetime.now()))
            conn.commit()
        except Exception as e:
            logger.error(f"Error saving raw post {post_id}: {e}")
        finally:
            conn.close()

    def save_signal(self, post_id, symbol_name, ticker, sentiment, profit, reasoning):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO extracted_signals 
                (post_id, symbol_name, ticker, sentiment, profit_pct, reasoning, extracted_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (post_id, symbol_name, ticker, sentiment, profit, reasoning, datetime.datetime.now()))
            conn.commit()
        except Exception as e:
            logger.error(f"Error saving signal for {symbol_name}: {e}")
        finally:
            conn.close()

    def get_recent_signals(self, hours=24):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cutoff = datetime.datetime.now() - datetime.timedelta(hours=hours)
        cursor.execute('SELECT * FROM extracted_signals WHERE extracted_at > ?', (cutoff,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

# Standard singleton for system-wide access
cafe_repo = CafeRepositoryManager()
