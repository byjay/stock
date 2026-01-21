import asyncio
import sys
import os

# 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from brain.evolution import DNA

class EvolutionaryStrategy:
    """
    [ISATS Ferrari Strategy] 진화하는 전략
    - 역할: DNA 유전자에서 파라미터를 추출하여 매매 실행
    """
    def __init__(self, dna: DNA):
        self.dna = dna
        # 하드코딩된 변수는 하나도 없습니다. 모두 DNA에서 가져옵니다.
        self.params = self.dna.genes 

    async def execute(self, market_data):
        """매매 실행 로직"""
        current_period = self.params["rsi_period"]
        stop_loss = self.params["stop_loss_pct"]
        
        # 🤖 AI 두뇌(Deep Eyes) 또는 기술적 지표 연동 가능
        # print(f"   [🤖 ACT] 전략: RSI({current_period}) 기준 가동 중... (손절: {stop_loss*100}%)")
        
        # 실제 매매 로직 (시장 데이터 분석 후 주문)
        pass

    def update_genes(self):
        """주기적으로 DNA를 최신 상태로 동기화"""
        self.params = self.dna.genes
        print(f"🧬 [Strategy] 유전자 동기화 완료 (Generation {self.dna.generation})")
