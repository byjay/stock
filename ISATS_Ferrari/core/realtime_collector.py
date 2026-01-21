import asyncio
import aiohttp
import yaml
import os
from datetime import datetime

# ==========================================
# 📡 Ferrari Real-time Data Collector
# ==========================================

class RealtimeCollector:
    def __init__(self):
        self.load_config()
        self.running = True
        
    def load_config(self):
        """설정 로드"""
        config_path = "config/secrets.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        self.app_key = config['key']['kis_app_key']
        self.app_secret = config['key']['kis_secret_key']
        self.base_url = "https://openapi.koreainvestment.com:9443"
        self.access_token = None
        
    async def get_token(self):
        """Access Token 발급"""
        auth_url = f"{self.base_url}/oauth2/tokenP"
        payload = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }
        
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(auth_url, json=payload) as resp:
                data = await resp.json()
                self.access_token = data.get('access_token')
                
                if self.access_token:
                    print(f"✅ [Collector] Access Token 발급 완료")
                    return True
                else:
                    print(f"❌ [Collector] 토큰 발급 실패: {data}")
                    return False
    
    async def collect_market_data(self):
        """실시간 시장 데이터 수집"""
        # 상한가 종목 리스트 로드
        target_stocks = ["005930", "000660", "035720"]  # 예시
        
        print(f"\n📊 [Collector] 실시간 수집 시작 ({len(target_stocks)}개 종목)")
        
        while self.running:
            try:
                # 여기서 실제로는 WebSocket이나 REST API로 실시간 시세 수집
                # 현재는 시뮬레이션
                
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"   ⏱️ [{timestamp}] 데이터 수집 중... (정상)")
                
                # Redis나 공유 메모리에 저장하는 로직 추가 필요
                
                await asyncio.sleep(5)  # 5초마다 수집
                
            except Exception as e:
                print(f"⚠️ [Collector] 수집 오류: {e}")
                await asyncio.sleep(10)
    
    async def run(self):
        """메인 루프"""
        print("📡 [Collector] 실시간 수집기 초기화 중...")
        
        if not await self.get_token():
            print("❌ [Collector] 토큰 발급 실패로 중단")
            return
        
        await self.collect_market_data()

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
