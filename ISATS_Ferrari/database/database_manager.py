import sqlite3
import os
from datetime import datetime

# ==========================================
# 📊 EXPERIENCE DATABASE (틱 데이터 블랙박스)
# ==========================================

class DatabaseManager:
    def __init__(self, db_path="database/experience.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def init_db(self):
        """데이터베이스 및 테이블 초기화"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 1. 실시간 틱 데이터 테이블 (Tick Data)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_ticks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT,
                market TEXT,
                timestamp DATETIME,
                price REAL,
                volume INTEGER,
                bid_price REAL,
                ask_price REAL,
                tick_type TEXT
            )
        ''')
        
        # 2. 1분봉 요약 테이블 (OHLCV)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS candle_minutes (
                ticker TEXT,
                market TEXT,
                timestamp DATETIME,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER,
                PRIMARY KEY (ticker, timestamp)
            )
        ''')
        
        conn.commit()
        conn.close()

    def save_tick(self, ticker, market, price, volume, bid=0, ask=0, tick_type='NORMAL'):
        """실시간 틱 데이터 저장"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO market_ticks (ticker, market, timestamp, price, volume, bid_price, ask_price, tick_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (ticker, market, datetime.now(), price, volume, bid, ask, tick_type))
        conn.commit()
        conn.close()

    def save_candle(self, ticker, market, timestamp, o, h, l, c, v):
        """분봉 데이터 저장"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO candle_minutes (ticker, market, timestamp, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (ticker, market, timestamp, o, h, l, c, v))
        conn.commit()
        conn.close()

    def get_recent_ticks(self, ticker, limit=100):
        """최근 틱 데이터 조회 (AI 학습용)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM market_ticks WHERE ticker = ? ORDER BY timestamp DESC LIMIT ?', (ticker, limit))
        rows = cursor.fetchall()
        conn.close()
        return rows

if __name__ == "__main__":
    db = DatabaseManager()
    db.save_tick("AAPL", "US", 150.5, 100)
    print("✅ [Database] 테스트 틱 저장 완료")
