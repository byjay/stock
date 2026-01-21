import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import logging
import os

logger = logging.getLogger("PriceDataStore")

class PriceDataStore:
    """
    다중 타임프레임 가격 데이터 영구 저장소
    
    Features:
    - 6개 타임프레임 지원 (1m, 3m, 5m, 15m, 1h, 1d)
    - 최소 30일 이상 데이터 저장
    - 빠른 조회를 위한 인덱스 최적화
    """
    
    TIMEFRAMES = ['1m', '3m', '5m', '15m', '1h', '1d']
    
    def __init__(self, db_path="data/price_history.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """데이터베이스 초기화 및 테이블 생성"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 타임프레임별 테이블 생성
        for tf in self.TIMEFRAMES:
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS prices_{tf} (
                    symbol TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (symbol, timestamp)
                )
            ''')
            
            # 인덱스 생성 (빠른 조회)
            cursor.execute(f'''
                CREATE INDEX IF NOT EXISTS idx_{tf}_symbol_time 
                ON prices_{tf}(symbol, timestamp DESC)
            ''')
        
        conn.commit()
        conn.close()
        logger.info(f"✅ PriceDataStore initialized at {self.db_path}")
    
    def save_candles(self, symbol: str, timeframe: str, df: pd.DataFrame):
        """
        캔들 데이터 저장
        
        Args:
            symbol: 종목 코드
            timeframe: 타임프레임 (1m, 3m, 5m, 15m, 1h, 1d)
            df: OHLCV 데이터프레임 (index=timestamp)
        """
        if timeframe not in self.TIMEFRAMES:
            logger.error(f"Invalid timeframe: {timeframe}")
            return
        
        if df.empty:
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            # 데이터 준비
            df_copy = df.copy()
            df_copy['symbol'] = symbol
            df_copy['timestamp'] = df_copy.index
            df_copy = df_copy.rename(columns={
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })
            
            # 필요한 컬럼만 선택
            cols = ['symbol', 'timestamp', 'open', 'high', 'low', 'close', 'volume']
            df_save = df_copy[cols]
            
            # 저장 (중복 시 무시)
            df_save.to_sql(
                f'prices_{timeframe}', 
                conn, 
                if_exists='append', 
                index=False,
                method='multi'
            )
            
            conn.commit()
            conn.close()
            
            logger.info(f"💾 Saved {len(df_save)} candles for {symbol} ({timeframe})")
            
        except sqlite3.IntegrityError:
            # 중복 데이터는 무시
            pass
        except Exception as e:
            logger.error(f"Error saving candles: {e}")
    
    def get_candles(self, symbol: str, timeframe: str, days: int = 30) -> pd.DataFrame:
        """
        저장된 캔들 데이터 조회
        
        Args:
            symbol: 종목 코드
            timeframe: 타임프레임
            days: 조회 기간 (일)
        
        Returns:
            DataFrame with OHLCV data
        """
        if timeframe not in self.TIMEFRAMES:
            logger.error(f"Invalid timeframe: {timeframe}")
            return pd.DataFrame()
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = f'''
                SELECT timestamp, open, high, low, close, volume
                FROM prices_{timeframe}
                WHERE symbol = ? 
                AND timestamp >= datetime('now', '-{days} days')
                ORDER BY timestamp ASC
            '''
            
            df = pd.read_sql_query(query, conn, params=(symbol,))
            conn.close()
            
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.set_index('timestamp')
                df = df.rename(columns={
                    'open': 'Open',
                    'high': 'High',
                    'low': 'Low',
                    'close': 'Close',
                    'volume': 'Volume'
                })
            
            return df
            
        except Exception as e:
            logger.error(f"Error loading candles: {e}")
            return pd.DataFrame()
    
    def get_latest_timestamp(self, symbol: str, timeframe: str) -> datetime:
        """마지막 저장된 데이터의 타임스탬프 조회"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(f'''
                SELECT MAX(timestamp) FROM prices_{timeframe}
                WHERE symbol = ?
            ''', (symbol,))
            
            result = cursor.fetchone()[0]
            conn.close()
            
            if result:
                return datetime.fromisoformat(result)
            else:
                return datetime.now() - timedelta(days=365)
                
        except Exception as e:
            logger.error(f"Error getting latest timestamp: {e}")
            return datetime.now() - timedelta(days=365)
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """오래된 데이터 정리 (디스크 공간 절약)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for tf in self.TIMEFRAMES:
                cursor.execute(f'''
                    DELETE FROM prices_{tf}
                    WHERE timestamp < datetime('now', '-{days_to_keep} days')
                ''')
            
            conn.commit()
            deleted = cursor.rowcount
            conn.close()
            
            logger.info(f"🧹 Cleaned up {deleted} old records")
            
        except Exception as e:
            logger.error(f"Error cleaning up data: {e}")


# 전역 인스턴스
price_store = PriceDataStore()
