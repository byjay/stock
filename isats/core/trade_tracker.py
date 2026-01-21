import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import logging
import os
import json

logger = logging.getLogger("TradeTracker")

class TradeTracker:
    """
    매수 후 가격 변화 추적 및 패턴 분석
    
    Features:
    - 매수 시점 기록
    - 정기적 스냅샷 (3분, 10분, 30분, 1시간, 2시간 후)
    - 최적 진입/청산 타점 분석
    - "그때 들어갔으면 수익이었네" 분석
    """
    
    SNAPSHOT_INTERVALS = [3, 10, 30, 60, 120]  # minutes
    
    def __init__(self, db_path="data/trade_patterns.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.active_trades = {}
        self._init_db()
    
    def _init_db(self):
        """데이터베이스 초기화"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 매수 기록 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                trade_id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                entry_price REAL NOT NULL,
                entry_time DATETIME NOT NULL,
                strategy TEXT,
                strategy_score REAL,
                exit_price REAL,
                exit_time DATETIME,
                pnl_pct REAL,
                status TEXT DEFAULT 'ACTIVE',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 스냅샷 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id TEXT NOT NULL,
                minutes_elapsed INTEGER NOT NULL,
                snapshot_time DATETIME NOT NULL,
                price REAL NOT NULL,
                pnl_pct REAL NOT NULL,
                volume INTEGER,
                rsi REAL,
                FOREIGN KEY (trade_id) REFERENCES trades(trade_id)
            )
        ''')
        
        # 인덱스
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_snapshots_trade ON snapshots(trade_id)')
        
        conn.commit()
        conn.close()
        logger.info(f"✅ TradeTracker initialized at {self.db_path}")
    
    def record_buy(self, symbol: str, entry_price: float, strategy: str = "UNKNOWN", strategy_score: float = 0):
        """
        매수 기록
        
        Args:
            symbol: 종목 코드
            entry_price: 진입 가격
            strategy: 사용된 전략
            strategy_score: 전략 점수
        
        Returns:
            trade_id
        """
        timestamp = datetime.now()
        trade_id = f"{symbol}_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO trades (trade_id, symbol, entry_price, entry_time, strategy, strategy_score)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (trade_id, symbol, entry_price, timestamp, strategy, strategy_score))
            
            conn.commit()
            conn.close()
            
            # 메모리에도 저장
            self.active_trades[trade_id] = {
                'symbol': symbol,
                'entry_price': entry_price,
                'entry_time': timestamp,
                'strategy': strategy,
                'last_snapshot_minute': 0
            }
            
            logger.info(f"📝 Recorded BUY: {symbol} @ ${entry_price} (ID: {trade_id})")
            return trade_id
            
        except Exception as e:
            logger.error(f"Error recording buy: {e}")
            return None
    
    def take_snapshot(self, trade_id: str, current_price: float, volume: int = 0, rsi: float = 0):
        """
        정기적 스냅샷 기록
        
        Args:
            trade_id: 거래 ID
            current_price: 현재 가격
            volume: 현재 거래량
            rsi: 현재 RSI
        """
        if trade_id not in self.active_trades:
            # DB에서 로드 시도
            self._load_active_trade(trade_id)
            if trade_id not in self.active_trades:
                return
        
        trade = self.active_trades[trade_id]
        entry_time = trade['entry_time']
        entry_price = trade['entry_price']
        
        # 경과 시간 계산
        now = datetime.now()
        elapsed = (now - entry_time).total_seconds() / 60  # minutes
        
        # 스냅샷 간격 확인
        next_snapshot = None
        for interval in self.SNAPSHOT_INTERVALS:
            if elapsed >= interval and trade['last_snapshot_minute'] < interval:
                next_snapshot = interval
                break
        
        if next_snapshot is None:
            return  # 아직 스냅샷 시간이 아님
        
        # PnL 계산
        pnl_pct = ((current_price - entry_price) / entry_price) * 100
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO snapshots (trade_id, minutes_elapsed, snapshot_time, price, pnl_pct, volume, rsi)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (trade_id, next_snapshot, now, current_price, pnl_pct, volume, rsi))
            
            conn.commit()
            conn.close()
            
            # 마지막 스냅샷 시간 업데이트
            trade['last_snapshot_minute'] = next_snapshot
            
            logger.info(f"📸 Snapshot [{trade['symbol']}] {next_snapshot}min: ${current_price} ({pnl_pct:+.2f}%)")
            
        except Exception as e:
            logger.error(f"Error taking snapshot: {e}")
    
    def close_trade(self, trade_id: str, exit_price: float):
        """
        거래 종료 기록
        
        Args:
            trade_id: 거래 ID
            exit_price: 청산 가격
        """
        if trade_id not in self.active_trades:
            return
        
        trade = self.active_trades[trade_id]
        entry_price = trade['entry_price']
        pnl_pct = ((exit_price - entry_price) / entry_price) * 100
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE trades
                SET exit_price = ?, exit_time = ?, pnl_pct = ?, status = 'CLOSED'
                WHERE trade_id = ?
            ''', (exit_price, datetime.now(), pnl_pct, trade_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f"🏁 Closed [{trade['symbol']}]: ${exit_price} ({pnl_pct:+.2f}%)")
            
            # 메모리에서 제거
            del self.active_trades[trade_id]
            
        except Exception as e:
            logger.error(f"Error closing trade: {e}")
    
    def analyze_pattern(self, trade_id: str) -> dict:
        """
        패턴 분석: 최적 진입/청산 타점 찾기
        
        Returns:
            {
                'entry_was_good': bool,
                'best_exit_time': int (minutes),
                'best_pnl': float,
                'missed_opportunity': float,
                'snapshots': list
            }
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            # 스냅샷 조회
            query = '''
                SELECT minutes_elapsed, price, pnl_pct
                FROM snapshots
                WHERE trade_id = ?
                ORDER BY minutes_elapsed
            '''
            df = pd.read_sql_query(query, conn, params=(trade_id,))
            conn.close()
            
            if df.empty:
                return {'entry_was_good': False, 'reason': 'No snapshots'}
            
            # 최고 수익 타점
            best_snapshot = df.loc[df['pnl_pct'].idxmax()]
            
            # 최종 결과
            final_snapshot = df.iloc[-1]
            
            return {
                'entry_was_good': best_snapshot['pnl_pct'] > 2.0,
                'best_exit_time': int(best_snapshot['minutes_elapsed']),
                'best_pnl': float(best_snapshot['pnl_pct']),
                'final_pnl': float(final_snapshot['pnl_pct']),
                'missed_opportunity': float(best_snapshot['pnl_pct'] - final_snapshot['pnl_pct']),
                'snapshots': df.to_dict('records')
            }
            
        except Exception as e:
            logger.error(f"Error analyzing pattern: {e}")
            return {'error': str(e)}
    
    def get_active_trades(self) -> list:
        """현재 활성 거래 목록 조회"""
        try:
            conn = sqlite3.connect(self.db_path)
            query = '''
                SELECT trade_id, symbol, entry_price, entry_time, strategy, strategy_score
                FROM trades
                WHERE status = 'ACTIVE'
                ORDER BY entry_time DESC
            '''
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            return df.to_dict('records')
            
        except Exception as e:
            logger.error(f"Error getting active trades: {e}")
            return []
    
    def _load_active_trade(self, trade_id: str):
        """DB에서 활성 거래 로드"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT symbol, entry_price, entry_time, strategy
                FROM trades
                WHERE trade_id = ? AND status = 'ACTIVE'
            ''', (trade_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                self.active_trades[trade_id] = {
                    'symbol': row[0],
                    'entry_price': row[1],
                    'entry_time': datetime.fromisoformat(row[2]),
                    'strategy': row[3],
                    'last_snapshot_minute': 0
                }
                
        except Exception as e:
            logger.error(f"Error loading trade: {e}")
    
    def update_all_snapshots(self, price_data: dict):
        """
        모든 활성 거래의 스냅샷 업데이트
        
        Args:
            price_data: {symbol: {'price': float, 'volume': int, 'rsi': float}}
        """
        active = self.get_active_trades()
        
        for trade in active:
            symbol = trade['symbol']
            if symbol in price_data:
                data = price_data[symbol]
                self.take_snapshot(
                    trade['trade_id'],
                    data.get('price', 0),
                    data.get('volume', 0),
                    data.get('rsi', 0)
                )


# 전역 인스턴스
trade_tracker = TradeTracker()
