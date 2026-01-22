"""
📡 ISATS v6.0 - Universal Data Collector
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

역할:
- 미국 전 종목 리스트 수집 (NASDAQ, NYSE, AMEX)
- 한국 전 종목 리스트 수집 (KOSPI, KOSDAQ)
- 5년치 일봉 데이터 자동 다운로드
- CSV 파일로 저장 (data/US/, data/KR/)

작성자: ISATS Neural Swarm
버전: 6.0 (Universal Data Collector)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import sys
import time
import pandas as pd
from datetime import datetime, timedelta
from tqdm import tqdm

# 프로젝트 루트 경로
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 선택적 임포트
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False
    print("⚠️ [Warning] yfinance not found. Installing...")
    os.system("pip install yfinance --quiet")
    import yfinance as yf
    HAS_YFINANCE = True

try:
    import FinanceDataReader as fdr
    HAS_FDR = True
except ImportError:
    HAS_FDR = False
    print("⚠️ [Warning] FinanceDataReader not found. Installing...")
    os.system("pip install finance-datareader --quiet")
    import FinanceDataReader as fdr
    HAS_FDR = True


# ==========================================
# 🌎 Universal Data Collector
# ==========================================

class UniversalDataCollector:
    """전 세계 종목 데이터 수집기"""
    
    def __init__(self, base_dir="ISATS_Ferrari/data"):
        self.base_dir = base_dir
        self.us_dir = os.path.join(base_dir, "US")
        self.kr_dir = os.path.join(base_dir, "KR")
        
        # 디렉토리 생성
        os.makedirs(self.us_dir, exist_ok=True)
        os.makedirs(self.kr_dir, exist_ok=True)
        
        # 날짜 범위 (5년치)
        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=365 * 5)
        
        print(f"\n{'='*80}")
        print(f"📡 ISATS v6.0 - Universal Data Collector")
        print(f"{'='*80}")
        print(f"📂 저장 경로: {base_dir}")
        print(f"📅 데이터 범위: {self.start_date.strftime('%Y-%m-%d')} ~ {self.end_date.strftime('%Y-%m-%d')}")
        print(f"{'='*80}\n")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 미국 종목
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def get_us_stock_list(self):
        """
        미국 전 종목 리스트 수집
        
        Returns:
            DataFrame: 종목 리스트 (Symbol, Name, Exchange)
        """
        print(f"\n{'='*80}")
        print(f"🇺🇸 미국 종목 리스트 수집 중...")
        print(f"{'='*80}\n")
        
        all_stocks = []
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 1. NASDAQ
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        try:
            print("📊 NASDAQ 종목 수집 중...")
            nasdaq = fdr.StockListing('NASDAQ')
            nasdaq['Exchange'] = 'NASDAQ'
            all_stocks.append(nasdaq)
            print(f"✅ NASDAQ: {len(nasdaq):,}개 종목")
        except Exception as e:
            print(f"⚠️ NASDAQ 수집 실패: {e}")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 2. NYSE
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        try:
            print("📊 NYSE 종목 수집 중...")
            nyse = fdr.StockListing('NYSE')
            nyse['Exchange'] = 'NYSE'
            all_stocks.append(nyse)
            print(f"✅ NYSE: {len(nyse):,}개 종목")
        except Exception as e:
            print(f"⚠️ NYSE 수집 실패: {e}")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 3. AMEX
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        try:
            print("📊 AMEX 종목 수집 중...")
            amex = fdr.StockListing('AMEX')
            amex['Exchange'] = 'AMEX'
            all_stocks.append(amex)
            print(f"✅ AMEX: {len(amex):,}개 종목")
        except Exception as e:
            print(f"⚠️ AMEX 수집 실패: {e}")
        
        # 통합
        if all_stocks:
            df = pd.concat(all_stocks, ignore_index=True)
            
            # 중복 제거
            df = df.drop_duplicates(subset=['Symbol'])
            
            # 정리
            df = df[['Symbol', 'Name', 'Exchange']].reset_index(drop=True)
            
            print(f"\n✅ 총 {len(df):,}개 미국 종목 수집 완료")
            
            # 저장
            list_path = os.path.join(self.us_dir, "US_STOCK_LIST.csv")
            df.to_csv(list_path, index=False, encoding='utf-8-sig')
            print(f"💾 저장: {list_path}")
            
            return df
        else:
            print("❌ 미국 종목 리스트 수집 실패")
            return pd.DataFrame()
    
    def download_us_data(self, stock_list, max_stocks=None):
        """
        미국 종목 데이터 다운로드
        
        Args:
            stock_list: DataFrame (Symbol, Name, Exchange)
            max_stocks: 최대 다운로드 종목 수 (None이면 전체)
        """
        print(f"\n{'='*80}")
        print(f"📥 미국 종목 데이터 다운로드 중...")
        print(f"{'='*80}\n")
        
        if max_stocks:
            stock_list = stock_list.head(max_stocks)
        
        success_count = 0
        fail_count = 0
        
        for idx, row in tqdm(stock_list.iterrows(), total=len(stock_list), desc="US Stocks"):
            symbol = row['Symbol']
            
            try:
                # yfinance로 다운로드
                ticker = yf.Ticker(symbol)
                df = ticker.history(start=self.start_date, end=self.end_date, interval='1d')
                
                if len(df) > 0:
                    # 저장
                    file_path = os.path.join(self.us_dir, f"{symbol}.csv")
                    df.to_csv(file_path)
                    success_count += 1
                else:
                    fail_count += 1
                
                # API 제한 방지
                time.sleep(0.1)
            
            except Exception as e:
                fail_count += 1
                continue
        
        print(f"\n✅ 다운로드 완료: {success_count:,}개 성공, {fail_count:,}개 실패")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 한국 종목
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def get_kr_stock_list(self):
        """
        한국 전 종목 리스트 수집
        
        Returns:
            DataFrame: 종목 리스트 (Symbol, Name, Market)
        """
        print(f"\n{'='*80}")
        print(f"🇰🇷 한국 종목 리스트 수집 중...")
        print(f"{'='*80}\n")
        
        all_stocks = []
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 1. KOSPI
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        try:
            print("📊 KOSPI 종목 수집 중...")
            kospi = fdr.StockListing('KOSPI')
            kospi['Market'] = 'KOSPI'
            all_stocks.append(kospi)
            print(f"✅ KOSPI: {len(kospi):,}개 종목")
        except Exception as e:
            print(f"⚠️ KOSPI 수집 실패: {e}")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 2. KOSDAQ
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        try:
            print("📊 KOSDAQ 종목 수집 중...")
            kosdaq = fdr.StockListing('KOSDAQ')
            kosdaq['Market'] = 'KOSDAQ'
            all_stocks.append(kosdaq)
            print(f"✅ KOSDAQ: {len(kosdaq):,}개 종목")
        except Exception as e:
            print(f"⚠️ KOSDAQ 수집 실패: {e}")
        
        # 통합
        if all_stocks:
            df = pd.concat(all_stocks, ignore_index=True)
            
            # 중복 제거
            df = df.drop_duplicates(subset=['Symbol'])
            
            # 정리
            df = df[['Symbol', 'Name', 'Market']].reset_index(drop=True)
            
            print(f"\n✅ 총 {len(df):,}개 한국 종목 수집 완료")
            
            # 저장
            list_path = os.path.join(self.kr_dir, "KR_STOCK_LIST.csv")
            df.to_csv(list_path, index=False, encoding='utf-8-sig')
            print(f"💾 저장: {list_path}")
            
            return df
        else:
            print("❌ 한국 종목 리스트 수집 실패")
            return pd.DataFrame()
    
    def download_kr_data(self, stock_list, max_stocks=None):
        """
        한국 종목 데이터 다운로드
        
        Args:
            stock_list: DataFrame (Symbol, Name, Market)
            max_stocks: 최대 다운로드 종목 수 (None이면 전체)
        """
        print(f"\n{'='*80}")
        print(f"📥 한국 종목 데이터 다운로드 중...")
        print(f"{'='*80}\n")
        
        if max_stocks:
            stock_list = stock_list.head(max_stocks)
        
        success_count = 0
        fail_count = 0
        
        for idx, row in tqdm(stock_list.iterrows(), total=len(stock_list), desc="KR Stocks"):
            symbol = row['Symbol']
            
            try:
                # FinanceDataReader로 다운로드
                df = fdr.DataReader(
                    symbol,
                    start=self.start_date.strftime('%Y-%m-%d'),
                    end=self.end_date.strftime('%Y-%m-%d')
                )
                
                if len(df) > 0:
                    # 저장
                    file_path = os.path.join(self.kr_dir, f"{symbol}.csv")
                    df.to_csv(file_path)
                    success_count += 1
                else:
                    fail_count += 1
                
                # API 제한 방지
                time.sleep(0.1)
            
            except Exception as e:
                fail_count += 1
                continue
        
        print(f"\n✅ 다운로드 완료: {success_count:,}개 성공, {fail_count:,}개 실패")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 전체 실행
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def collect_all(self, us_max=None, kr_max=None):
        """
        전체 데이터 수집
        
        Args:
            us_max: 미국 종목 최대 개수 (None이면 전체)
            kr_max: 한국 종목 최대 개수 (None이면 전체)
        """
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 1. 미국 종목
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        us_list = self.get_us_stock_list()
        
        if len(us_list) > 0:
            self.download_us_data(us_list, max_stocks=us_max)
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 2. 한국 종목
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        kr_list = self.get_kr_stock_list()
        
        if len(kr_list) > 0:
            self.download_kr_data(kr_list, max_stocks=kr_max)
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 완료
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        print(f"\n{'='*80}")
        print(f"✅ 전체 데이터 수집 완료")
        print(f"{'='*80}")
        print(f"📂 미국: {self.us_dir}")
        print(f"📂 한국: {self.kr_dir}")
        print(f"{'='*80}\n")


# ==========================================
# 실행
# ==========================================

if __name__ == "__main__":
    collector = UniversalDataCollector()
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 옵션 1: 전체 수집 (시간 오래 걸림)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    # collector.collect_all()
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 옵션 2: 상위 N개만 수집 (테스트용)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    print("\n⚠️ [알림] 전체 수집은 시간이 오래 걸립니다.")
    print("   테스트: 미국 100개 + 한국 100개")
    print("   전체: us_max=None, kr_max=None\n")
    
    choice = input("전체 수집하시겠습니까? (y/N): ").strip().lower()
    
    if choice == 'y':
        collector.collect_all()
    else:
        # 테스트: 상위 100개씩
        collector.collect_all(us_max=100, kr_max=100)
