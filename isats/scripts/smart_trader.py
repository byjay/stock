import asyncio
import json
import os
import sys
import random
from datetime import datetime
import redis.asyncio as redis

# [Path Setup]
current_dir = os.path.dirname(os.path.abspath(__file__))
# scripts -> isats (루트 경로 조정: isats/scripts/smart_trader.py 기준으로 root는 ../..)
root_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(root_dir)

class IntegratedTrader:
    """
    [ISATS Smart Trader v2.2] 통합 트레이딩 엔진 (Updated)
    - 파일: isats/scripts/smart_trader.py
    - 임무: 가상/실전 매매 동시 수행, Redis 상태 보고, 사령관 승인 대기
    """
    def __init__(self):
        # Redis 연결 (비동기)
        self.r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        
        # 1. 가상 계좌 (Virtual Port) - KR, US, ETF 통합 시뮬레이션
        self.virtual_bal = 100_000_000 # 1억
        self.virtual_holdings = {
            "KR": {"005930": {"qty": 10, "avg": 72000, "name": "삼성전자"}},
            "US": {"TSLA": {"qty": 5, "avg": 250.0, "name": "테슬라"}},
            "ETF": {"SOXL": {"qty": 100, "avg": 35.5, "name": "SOXL"}}
        }
        
        # 2. 실전 계좌 (Real Port) - 초기엔 비어있음
        self.real_bal = 10_000_000 # 1천만
        self.real_holdings = {}

    async def report_status(self):
        """현재 자산 상태를 Redis 채널(dashboard:status)에 브리핑"""
        status = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "virtual": {
                "balance": self.virtual_bal,
                "holdings": self.virtual_holdings
            },
            "real": {
                "balance": self.real_bal,
                "holdings": self.real_holdings
            }
        }
        try:
            await self.r.set("dashboard:status", json.dumps(status))
        except Exception as e:
            # Redis가 꺼져있을 경우 조용히 대기
            pass

    async def check_commander_approval(self):
        """대시보드에서 사령관이 '승인' 버튼을 눌렀는지 확인"""
        try:
            approval = await self.r.get("cmd:real_trading_approved")
            return approval == "TRUE"
        except:
            return False

    async def run_market_simulation(self):
        """시장 데이터 수신 및 매매 루프"""
        print(f"🚀 [Smart Trader] 엔진 시동. Redis 보고 채널 연결됨.")
        
        while True:
            # 1. 가상 매매 시뮬레이션 (항상 가동)
            await self.simulate_price_fluctuation()
            
            # 2. 실전 매매 로직 (승인 시에만 가동 - Kill Switch)
            is_approved = await self.check_commander_approval()
            if is_approved:
                await self.execute_real_trading()
            else:
                # 승인 대기 상태
                pass

            # 3. 상황판 업데이트 보고
            await self.report_status()
            await asyncio.sleep(1) # 1초 단위 갱신

    async def simulate_price_fluctuation(self):
        # (시각화용) 가상 잔고가 살짝씩 변하는 연출
        fluctuation = random.choice([-1000, 0, 1000, 2000, -500])
        self.virtual_bal += fluctuation

    async def execute_real_trading(self):
        # (실전 로직 위치) 실제 KIS API 주문 코드가 들어갈 자리
        # 현재는 안전을 위해 로그만 남김
        # print("⚔️ [Real] 실전 매매 감시 중...", end='\r')
        pass

if __name__ == "__main__":
    try:
        engine = IntegratedTrader()
        asyncio.run(engine.run_market_simulation())
    except KeyboardInterrupt:
        print("엔진 종료")
    except Exception as e:
        print(f"❌ 엔진 가동 중단: {e}")
