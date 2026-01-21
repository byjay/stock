import asyncio
import json
import os
import sys
import random
from datetime import datetime
import redis.asyncio as redis

# 경로 설정
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from brain.evolution import DNA
from strategy.active_bot import EvolutionaryStrategy

class FerrariEngine:
    """
    [ISATS Ferrari Engine] 초경량 통합 엔진
    - 역할: DNA 진화 루프, Redis 자산 보고, 사령관 승인 제어
    """
    def __init__(self):
        # 1. 인프라 연결
        try:
            self.r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        except:
            self.r = None
            
        # 2. 지능/전략 이식
        self.dna = DNA()
        self.bot = EvolutionaryStrategy(self.dna)
        
        # 3. 자산 관리 (Virtual/Real)
        self.virtual_bal = 100_000_000
        self.real_bal = 10_000_000
        self.holdings = {"V": {}, "R": {}}

    async def report_status(self):
        """대시보드로 자산 및 DNA 상태 보고"""
        if not self.r: return
        status = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "generation": self.dna.generation,
            "genes": self.dna.genes,
            "virtual_bal": self.virtual_bal,
            "real_bal": self.real_bal,
            "approved": await self.check_approval()
        }
        await self.r.set("dashboard:status", json.dumps(status))

    async def check_approval(self):
        """사령관의 '실전 매매 승인' 체크"""
        if not self.r: return False
        val = await self.r.get("cmd:real_trading_approved")
        return val == "TRUE"

    async def run(self):
        print("=== 🚀 ISATS v2.5 Ferrari Engine Ignition ===")
        
        while True:
            # 1. 시장 변동성 시뮬레이션 (0.0 ~ 1.0)
            volatility = random.random()
            
            # 2. 전략 실행 (데이터 수신 모방)
            await self.bot.execute({"volatility": volatility})
            
            # 3. 야간 자가 진화 (Mutation)
            # 여기서는 매 루프(가상 1일)마다 시장 상황에 맞춰 진화
            self.dna.mutate(volatility)
            self.bot.update_genes()
            
            # 4. 상태 브리핑
            await self.report_status()
            
            await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        engine = FerrariEngine()
        asyncio.run(engine.run())
    except KeyboardInterrupt:
        print("\n🏁 엔진 가동 중단 (Safe Stop)")
    except Exception as e:
        print(f"❌ 엔진 오류: {e}")
