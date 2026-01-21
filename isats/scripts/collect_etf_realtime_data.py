"""
ETF Real-time Data Collector
Collects ETF list, expiry dates, daily volume, and prices via KIS API
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.korea_inv_wrapper import KoreaInvWrapper
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import time

class ETFDataCollector:
    """
    Collect comprehensive ETF data from KIS API
    - ETF list (updated monthly)
    - Expiry dates
    - Daily volume
    - Daily prices (OHLCV)
    """
    
    def __init__(self):
        self.kis = KoreaInvWrapper()
        self.db_path = 'etf_realtime_data.db'
        self._init_database()
    
    def _init_database(self):
        """Initialize database for ETF data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # ETF master table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS etf_master (
                code TEXT PRIMARY KEY,
                name TEXT,
                category TEXT,
                leverage INTEGER,
                expiry_date TEXT,
                min_order_value INTEGER,
                last_updated DATETIME
            )
        ''')
        
        # Daily trading data
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS etf_daily_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT,
                date TEXT,
                open_price REAL,
                high_price REAL,
                low_price REAL,
                close_price REAL,
                volume INTEGER,
                trading_value REAL,
                UNIQUE(code, date)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def collect_etf_list(self):
        """
        Collect current ETF list from KIS API
        Focus on leverage/inverse ETFs for options trading
        """
        
        print("=" * 80)
        print("📊 ETF 목록 수집 (KIS API)")
        print("=" * 80)
        print()
        
        # Known leverage/inverse ETFs (will be expanded via API)
        etf_universe = {
            # 2x Leverage (CALL-like)
            "122630": {"name": "KODEX 레버리지", "category": "KOSPI_2X", "leverage": 2},
            "252670": {"name": "TIGER 레버리지", "category": "KOSPI_2X", "leverage": 2},
            "233740": {"name": "KODEX 코스닥150레버리지", "category": "KOSDAQ_2X", "leverage": 2},
            
            # 2x Inverse (PUT-like)
            "251340": {"name": "KODEX 레버리지인버스", "category": "KOSPI_INV_2X", "leverage": -2},
            
            # 1x Inverse
            "114800": {"name": "KODEX 인버스", "category": "KOSPI_INV", "leverage": -1},
            "123310": {"name": "TIGER 인버스", "category": "KOSPI_INV", "leverage": -1},
            "251350": {"name": "KODEX 코스닥150인버스", "category": "KOSDAQ_INV", "leverage": -1},
            
            # Sector Leverage
            "102780": {"name": "KODEX 삼성그룹레버리지", "category": "SECTOR_2X", "leverage": 2},
            "278530": {"name": "KODEX 2차전지산업레버리지", "category": "SECTOR_2X", "leverage": 2},
            "371460": {"name": "TIGER 2차전지테마레버리지", "category": "SECTOR_2X", "leverage": 2},
            
            # Futures
            "252710": {"name": "TIGER 200선물레버리지", "category": "FUTURES_2X", "leverage": 2},
            "252420": {"name": "KODEX 코스닥150선물인버스", "category": "FUTURES_INV", "leverage": -1},
        }
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for code, info in etf_universe.items():
            try:
                # Fetch current price to verify ETF is active
                price_data = self.kis.fetch_price(code)
                
                if price_data and "output" in price_data:
                    current_price = float(price_data["output"].get("stck_prpr", 0))
                    
                    if current_price > 0:
                        # Insert/Update ETF master
                        cursor.execute('''
                            INSERT OR REPLACE INTO etf_master 
                            (code, name, category, leverage, expiry_date, min_order_value, last_updated)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            code,
                            info["name"],
                            info["category"],
                            info["leverage"],
                            None,  # Will be updated with actual expiry
                            100000,  # 10만원 minimum
                            datetime.now().isoformat()
                        ))
                        
                        print(f"✓ {code} {info['name']}: {current_price:,.0f}원")
                        time.sleep(0.1)  # Rate limiting
                
            except Exception as e:
                print(f"✗ {code} {info['name']}: Error - {e}")
        
        conn.commit()
        
        # Summary
        cursor.execute("SELECT COUNT(*) FROM etf_master")
        total = cursor.fetchone()[0]
        
        print()
        print(f"📁 ETF 목록 저장 완료: {total}개")
        
        conn.close()
        return etf_universe
    
    def collect_daily_data(self, code, days=30):
        """
        Collect daily OHLCV data for specific ETF
        Note: KIS API provides limited historical data
        """
        
        print(f"📈 {code} 일별 데이터 수집 중...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Fetch current day data
        try:
            price_data = self.kis.fetch_price(code)
            
            if price_data and "output" in price_data:
                output = price_data["output"]
                
                today = datetime.now().strftime("%Y-%m-%d")
                
                cursor.execute('''
                    INSERT OR REPLACE INTO etf_daily_data
                    (code, date, open_price, high_price, low_price, close_price, volume, trading_value)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    code,
                    today,
                    float(output.get("stck_oprc", 0)),  # Open
                    float(output.get("stck_hgpr", 0)),  # High
                    float(output.get("stck_lwpr", 0)),  # Low
                    float(output.get("stck_prpr", 0)),  # Close
                    int(output.get("acml_vol", 0)),     # Volume
                    float(output.get("acml_tr_pbmn", 0))  # Trading value
                ))
                
                conn.commit()
                print(f"  ✓ {today} 데이터 저장")
        
        except Exception as e:
            print(f"  ✗ Error: {e}")
        
        conn.close()
    
    def get_etf_summary(self):
        """Get summary of collected ETF data"""
        
        conn = sqlite3.connect(self.db_path)
        
        print()
        print("=" * 80)
        print("📊 ETF 데이터 수집 현황")
        print("=" * 80)
        print()
        
        # ETF count by category
        df_master = pd.read_sql_query("SELECT * FROM etf_master", conn)
        
        print("【 카테고리별 ETF 수 】")
        print(df_master.groupby('category').size())
        print()
        
        # Data coverage
        df_daily = pd.read_sql_query("SELECT code, COUNT(*) as days FROM etf_daily_data GROUP BY code", conn)
        
        print("【 일별 데이터 수집 현황 】")
        print(df_daily)
        print()
        
        conn.close()

def main():
    """Main execution"""
    
    collector = ETFDataCollector()
    
    # Step 1: Collect ETF list
    etf_list = collector.collect_etf_list()
    
    # Step 2: Collect daily data for each ETF
    print()
    print("=" * 80)
    print("📈 일별 데이터 수집")
    print("=" * 80)
    print()
    
    for code in etf_list.keys():
        collector.collect_daily_data(code)
        time.sleep(0.2)  # Rate limiting
    
    # Step 3: Summary
    collector.get_etf_summary()
    
    print()
    print("=" * 80)
    print("✅ ETF 데이터 수집 완료!")
    print(f"📁 데이터베이스: {collector.db_path}")
    print("=" * 80)

if __name__ == "__main__":
    main()
