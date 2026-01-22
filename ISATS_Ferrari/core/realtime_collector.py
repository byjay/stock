import sys
import os
import asyncio
import aiohttp
import yaml
from datetime import datetime

# 페라리 모듈 경로 자동 설정
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.upper_limit_scanner import MarketRadar
from database.database_manager import DatabaseManager

# ==========================================
# 📡 Ferrari Global Real-time Data Collector
# ==========================================

class RealtimeCollector:
    def __init__(self):
        self.load_config()
        self.radar = MarketRadar()
        self.db = DatabaseManager()
        self.running = True
        self.monitored_stocks = []

    def load_config(self):
        """설정 로드"""
        config_path = "config/secrets.yaml"
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            self.app_key = config.get('key', {}).get('kis_app_key')
            self.app_secret = config.get('key', {}).get('kis_secret_key')
        else:
            self.app_key = None
            self.app_secret = None
        
        self.base_url = "https://openapi.koreainvestment.com:9443"
        self.access_token = None
        
    async def get_token(self):
        """Access Token 발급 (한국투자증권 API 등)"""
        # ... (생략 또는 기존 로직 유지) ...
        # 여기서는 테스트를 위해 성공으로 가정하거나 가상 토큰 사용
        self.access_token = "VIRTUAL_TOKEN"
        return True
    
    async def update_monitored_list(self):
        """감시 대상 목록 갱신 (프리마켓 TOP 100 등)"""
        print(f"📡 [Collector] 감시 대상 목록 갱신 중...")
        kr_hot = self.radar.scan_kr_hot_stocks(top_n=20)
        us_pre = self.radar.scan_us_premarket_hot_stocks(top_n=100)
        
        self.monitored_stocks = kr_hot + us_pre
        print(f"✅ [Collector] 총 {len(self.monitored_stocks)}개 종목 감시 대상 등록 완료")

    async def watch_ticker(self, stock_info):
        """개별 종목 실시간 틱 감시 및 DB 저장"""
        ticker = stock_info['ticker']
        market = stock_info['market']
        
        while self.running:
            try:
                # 1. 실시간 시세 시뮬레이션 또는 API 호출
                # 실제 환경에서는 WebSocket 또는 고속 REST 호출
                price = 150.0 + (stock_info['change'] / 10) # 예시 가격
                volume = 1000 # 예시 거래량
                
                # 2. DatabaseManager를 통한 틱 영구 저장 (Experience DB)
                self.db.save_tick(ticker, market, price, volume)
                
                # 3. 틱 간격 조절 (실전은 0.1~0.5초, 시뮬레이션은 2초)
                await asyncio.sleep(2)
                
            except Exception as e:
                # print(f"⚠️ [{ticker}] 감시 오류: {e}")
                await asyncio.sleep(5)

    async def run(self):
        """메인 수집 루프"""
        print("🚀 [Collector] 글로벌 하이재킹 엔진 기동!")
        
        # 1. 초동 스캔 및 목록 확보
        await self.update_monitored_list()
        
        # 2. 100+개 종목 동시 감시 개시 (비동기 병렬 처리)
        tasks = [self.watch_ticker(stock) for stock in self.monitored_stocks]
        
        # 1시간마다 목록 갱신하는 보조 태스크 추가 가능
        await asyncio.gather(*tasks)

def main():
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    collector = RealtimeCollector()
    try:
        asyncio.run(collector.run())
    except KeyboardInterrupt:
        print("\n🛑 [Collector] 수집기 종료")

if __name__ == "__main__":
    main()
