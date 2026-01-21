import random
import json
import asyncio
import os
from datetime import datetime

class DNA:
    """
    봇의 성격을 결정하는 유전자 정보입니다.
    고정된 값(상수)이 아니라, 언제든지 변할 수 있는 상태입니다.
    """
    def __init__(self, config_path="isats/config/dna.json"):
        self.config_path = config_path
        self.generation = 1
        self.genes = {
            "strategy_name": "Adaptive_Volatility_Ferrari",
            "rsi_period": 14,          
            "stop_loss_pct": 0.02,     
            "take_profit_pct": 0.05,   
            "lookback_window": 100     
        }
        self.load_dna()

    def load_dna(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    stored = json.load(f)
                    self.genes.update(stored.get("genes", {}))
                    self.generation = stored.get("generation", 1)
                print(f"🧬 [DNA] {self.generation}세대 유전자 로드 완료.")
            except:
                pass

    def save_dna(self):
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump({"generation": self.generation, "genes": self.genes, "last_update": str(datetime.now())}, f, indent=4)

    def mutate(self, market_volatility):
        """
        [진화의 핵심] 시장 상황에 따라 유전자를 스스로 조작합니다.
        시장 변동성(volatility)이 높으면 더 민감하게(짧게) 반응하도록 진화합니다.
        """
        print(f"\n[🧬 EVOLUTION] 세대 {self.generation} -> {self.generation + 1} 진화 시작...")
        old_rsi = self.genes["rsi_period"]
        
        # 시나리오: 시장이 미쳐 날뛸 때 (변동성 높음) -> 기간을 짧게 잡아서 빠르게 대응
        if market_volatility > 0.8:
            self.genes["rsi_period"] = max(5, self.genes["rsi_period"] - 2)
            self.genes["stop_loss_pct"] = 0.01  # 손절을 짧게
            print(f"   -> 시장 폭주 감지! 반응 속도 높임 (RSI기간: {old_rsi} -> {self.genes['rsi_period']})")
            
        # 시나리오: 시장이 지루할 때 (변동성 낮음) -> 기간을 길게 잡아서 신중하게 대응
        elif market_volatility < 0.3:
            self.genes["rsi_period"] = min(30, self.genes["rsi_period"] + 2)
            self.genes["stop_loss_pct"] = 0.03  # 손절을 널널하게
            print(f"   -> 시장 침체 감지! 호흡을 길게 가져감 (RSI기간: {old_rsi} -> {self.genes['rsi_period']})")
        
        else:
            # 랜덤 돌연변이 (가끔 엉뚱한 시도가 대박을 냄)
            if random.random() < 0.1:
                mutation = random.randint(-1, 1)
                self.genes["rsi_period"] += mutation
                print(f"   -> 랜덤 돌연변이 발생! (RSI기간: {old_rsi} -> {self.genes['rsi_period']})")

        self.generation += 1
        self.save_dna()
        return self.genes
