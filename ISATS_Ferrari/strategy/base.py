import asyncio
from abc import ABC, abstractmethod
import json

class BaseStrategy(ABC):
    """
    모든 매매 전략의 어머니 클래스 (Base Class).
    진화형 봇을 위해 공통된 유전자(DNA) 관리 기능을 제공합니다.
    """
    def __init__(self, dna_path="config/dna.json"):
        self.dna_path = dna_path
        self.params = self._load_dna()
        self.name = "Unknown Strategy"

    def _load_dna(self):
        """DNA 파일에서 유전자(설정값)를 읽어옵니다."""
        try:
            with open(self.dna_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print("⚠️ DNA 파일이 없어 기본값을 생성합니다.")
            return {"rsi_period": 14, "stop_loss": 0.02, "risk_level": 0.5}

    def reload_dna(self):
        """외부에서 DNA가 수정되었을 때 실시간으로 반영합니다 (진화)."""
        new_params = self._load_dna()
        if new_params != self.params:
            print(f"🧬 [EVOLUTION] 전략 '{self.name}'의 유전자가 업데이트되었습니다.")
            self.params = new_params
            return True
        return False

    @abstractmethod
    async def analyze(self, market_data):
        """
        [필수 구현] 시장 데이터를 받아 행동을 결정합니다.
        Return: 'BUY', 'SELL', 'HOLD'
        """
        pass
