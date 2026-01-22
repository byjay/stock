import FinanceDataReader as fdr
import pandas as pd
import datetime
import os
import sys
import yfinance as yf

# 경로 보정
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ==========================================
# 📡 MARKET RADAR (KR/US 상한가 및 주도주 레이더)
# ==========================================

class MarketRadar:
    def __init__(self, market="KRX"):
        self.market = market
        self.today = datetime.datetime.now().strftime("%Y-%m-%d")

    def scan_kr_hot_stocks(self, top_n=20):
        print(f"\n📡 [Radar-KR] {self.today} 한국 시장 주도주 스캔 중...")
        try:
            df = fdr.StockListing("KRX")
            if 'ChagesRatio' in df.columns:
                target_col = 'ChagesRatio'
            elif 'Change' in df.columns:
                df['ChagesRatio'] = df['Change'] * 100
                target_col = 'ChagesRatio'
            else:
                return []

            hot_stocks = df[df[target_col] >= 15.0].copy()
            if 'Amount' in hot_stocks.columns:
                hot_stocks = hot_stocks.sort_values(by=[target_col, 'Amount'], ascending=False)
            else:
                hot_stocks = hot_stocks.sort_values(by=[target_col], ascending=False)
            
            results = []
            for idx, row in hot_stocks.head(top_n).iterrows():
                code = row['Code']
                name = row['Name']
                change = row[target_col]
                market_type = row.get('Market', 'KOSPI')
                suffix = ".KS" if "KOSPI" in market_type else ".KQ"
                results.append({'ticker': f"{code}{suffix}", 'name': name, 'change': change, 'market': 'KR'})
            
            return results
        except Exception as e:
            print(f"❌ [Radar-KR Error] {e}")
            return []

    def scan_us_premarket_hot_stocks(self, top_n=20):
        print(f"\n📡 [Radar-US] 미국 시장 실시간 급등주 스캔 중 (yfinance)...")
        try:
            # 변동성 높은 종목 풀 (대형주 제외, 중소형 성장주 중심)
            momentum_pool = [
                # 테크 중소형주
                "PLTR", "COIN", "MARA", "RIOT", "MSTR", "UPST", "AFRM", "SQ", "OPEN",
                # 바이오/헬스케어
                "MRNA", "BNTX", "NVAX", "CRSP", "EDIT", "BEAM",
                # EV/신재생
                "LCID", "RIVN", "XPEV", "NIO", "LI", "ENPH", "SEDG",
                # 레버리지 ETF (급등락)
                "TQQQ", "SQQQ", "SOXL", "SOXS", "TSLL", "TSLS",
                # 기타 고변동성
                "GME", "AMC", "BBBY", "HOOD", "SOFI", "DKNG"
            ]
            
            scanned = []
            print(f"🔍 {len(momentum_pool)}개 급등 후보 종목 스캔 중...")
            
            for sym in momentum_pool[:top_n]:
                try:
                    ticker = yf.Ticker(sym)
                    hist = ticker.history(period="1d", interval="1m")
                    if not hist.empty:
                        current = hist['Close'].iloc[-1]
                        prev_close = hist['Open'].iloc[0]
                        change = ((current - prev_close) / prev_close) * 100
                        volume = hist['Volume'].sum()
                        
                        # 급등 조건: 변동률 절대값 > 2% 또는 거래량 급증
                        if abs(change) > 2.0 or volume > 1000000:
                            scanned.append({
                                'ticker': sym,
                                'name': sym,
                                'price': round(current, 2),
                                'change': round(change, 2),
                                'volume': volume,
                                'market': 'US',
                                'signal': 'HOT' if change > 0 else 'COLD'
                            })
                except Exception as e:
                    continue
            
            # 변동률 기준 정렬 (절대값)
            scanned.sort(key=lambda x: abs(x['change']), reverse=True)
            print(f"🔥 [Detection-US] 급등 후보 {len(scanned)}개 포착 완료")
            return scanned
            
        except Exception as e:
            print(f"❌ [Radar-US Error] {e}")
            return []

if __name__ == "__main__":
    radar = MarketRadar()
    kr_targets = radar.scan_kr_hot_stocks(top_n=5)
    us_targets = radar.scan_us_premarket_hot_stocks(top_n=5)
    
    print("\n🎯 [Global Target Locked]")
    for t in kr_targets + us_targets:
        print(f"   - [{t['market']}] {t['name']} ({t['ticker']}): +{t['change']:.2f}%")
