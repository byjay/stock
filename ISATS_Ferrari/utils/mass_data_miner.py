import os
import time
import pandas as pd
import FinanceDataReader as fdr
import yfinance as yf
from tqdm import tqdm
from datetime import datetime, timedelta

# ==========================================
# ⛏️ Operation: Mass Mining (대규모 데이터 채굴)
# ==========================================

# 1. 저장 경로 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # ISATS_Ferrari/
DATA_DIR = os.path.join(BASE_DIR, "data")

# 2. 수집 설정
YEARS_TO_COLLECT = 4  # 4년치
END_DATE = datetime.now()
START_DATE = END_DATE - timedelta(days=365 * YEARS_TO_COLLECT)
START_DATE_STR = START_DATE.strftime("%Y-%m-%d")

def setup_directories():
    """국가별 데이터 폴더 생성"""
    for market in ["KR", "US"]:
        path = os.path.join(DATA_DIR, market)
        os.makedirs(path, exist_ok=True)
    print(f"📂 [Storage] 데이터 저장소 준비 완료: {DATA_DIR}")

def get_kr_tickers(limit=500):
    """한국 시장(KOSPI+KOSDAQ) 시총 상위 n개 티커 가져오기"""
    print("\n🔍 [KR] 한국 주식 상위 500개 리스트 스캔 중...")
    
    try:
        # KRX 전체 상장 종목 가져오기
        df_krx = fdr.StockListing('KRX')
        
        # 시가총액 기준 정렬
        if 'Marcap' in df_krx.columns:
            df_krx = df_krx.sort_values(by='Marcap', ascending=False)
        elif 'MarketCap' in df_krx.columns:
            df_krx = df_krx.sort_values(by='MarketCap', ascending=False)
        
        top_n = df_krx.head(limit)
        
        tickers = []
        for idx, row in top_n.iterrows():
            code = row['Code']
            market = row.get('Market', 'KOSPI')
            
            # Yahoo Finance 호환 티커로 변환
            if 'KOSPI' in str(market):
                tickers.append(f"{code}.KS")
            else:
                tickers.append(f"{code}.KQ")
                
        print(f"   -> 한국 타겟 확보: {len(tickers)}개 (삼성전자, SK하이닉스 등)")
        return tickers
    except Exception as e:
        print(f"   ⚠️ 한국 종목 리스트 가져오기 실패: {e}")
        return []

def get_us_tickers(limit=500):
    """미국 시장(S&P 500) 티커 가져오기"""
    print("\n🔍 [US] 미국 S&P 500 리스트 스캔 중...")
    
    try:
        df_sp500 = fdr.StockListing('S&P500')
        tickers = df_sp500['Symbol'].head(limit).tolist()
        
        print(f"   -> 미국 타겟 확보: {len(tickers)}개 (Apple, Tesla, NVDA 등)")
        return tickers
    except Exception as e:
        print(f"   ⚠️ 미국 종목 리스트 가져오기 실패: {e}")
        return []

def download_and_save(tickers, market_code):
    """야후 파이낸스에서 데이터 다운로드 및 CSV 저장"""
    print(f"\n⬇️ [{market_code}] 데이터 다운로드 시작 (기간: {START_DATE_STR} ~ 현재)...")
    
    success_count = 0
    fail_count = 0
    
    # 진행바 표시
    pbar = tqdm(tickers, desc=f"Mining {market_code}", unit="stock")
    
    for ticker in pbar:
        try:
            save_path = os.path.join(DATA_DIR, market_code, f"{ticker}.csv")
            
            # 데이터 다운로드 (progress=False로 개별 로그 숨김)
            df = yf.download(ticker, start=START_DATE_STR, progress=False, threads=False)
            
            if df.empty:
                fail_count += 1
                continue
            
            # 컬럼 정리 (MultiIndex 문제 해결)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            # 필요한 컬럼만 선택 및 저장
            df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
            df.to_csv(save_path)
            
            success_count += 1
            
        except Exception as e:
            fail_count += 1

    print(f"✅ [{market_code}] 완료! 성공: {success_count}, 실패: {fail_count}")
    return success_count

def run_miner():
    print("="*50)
    print("      ⛏️  ISATS MASS DATA MINER v1.0      ")
    print("      Target: KR(500) + US(500) / 4 Years ")
    print("="*50)
    
    setup_directories()
    
    # 1. 티커 확보
    us_tickers = get_us_tickers(500)
    kr_tickers = get_kr_tickers(500)
    
    total_collected = 0
    
    # 2. 다운로드 수행
    if us_tickers:
        total_collected += download_and_save(us_tickers, "US")
    
    if kr_tickers:
        total_collected += download_and_save(kr_tickers, "KR")
    
    print("\n🎉 [Mission Complete] 모든 데이터 채굴이 완료되었습니다.")
    print(f"   📂 저장 위치: {DATA_DIR}")
    print(f"   📊 총 수집 종목: {total_collected}개")
    print(f"   💾 예상 용량: ~{total_collected * 0.5:.1f}MB")

if __name__ == "__main__":
    run_miner()
