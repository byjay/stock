"""
🧬 ISATS PHOENIX S-CLASS: GENESIS EVOLUTION v2.0 (Integrated)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
역할:
- 유전 알고리즘을 통한 최적의 매매 DNA(Timeframe, MA, TP/SL) 추출
- 모든 시뮬레이션 과정에 'Savage Validator'를 통합하여 신호 무결성 검증
- 실전 투입이 가능한 '불사조 챔피언' 전략 파라미터 생성

원칙:
- "검증기를 통과하지 못하면 수익도 없다."
- 단순한 백테스트가 아닌, 가혹한 검증 과정을 거친 생존자만이 챔피언이 된다.
- 모든 데이터 처리는 Pandas/Numpy 가속을 통해 고속 수행한다.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import pandas as pd
import numpy as np
import random
import os
import sys
import copy
import json
from tqdm import tqdm
from typing import List, Dict, Any, Tuple, Optional

# 프로젝트 루트 및 모듈 경로 설정
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.signal_validator import SignalValidator

class DNA:
    """전략의 유전 정보를 담는 클래스."""
    def __init__(self) -> None:
        self.timeframe: str = random.choice(['3T', '5T', '7T', '13T', '17T'])
        self.ma_short: int = random.randint(3, 10)
        self.ma_long: int = random.randint(20, 60)
        # 리스크 관리 (S-Class Standard)
        self.take_profit: float = round(random.uniform(0.02, 0.15), 3)
        self.stop_loss: float = round(random.uniform(0.01, 0.05), 3)
        
    def mutate(self) -> None:
        """DNA 변이 발생."""
        if random.random() < 0.1:
            self.timeframe = random.choice(['3T', '7T', '13T', '17T'])
        if random.random() < 0.1:
            self.ma_short = random.randint(3, 10)
        if random.random() < 0.1:
            self.take_profit = round(random.uniform(0.02, 0.20), 3)

class IntegratedAgent:
    """Savage Validator가 장착된 시뮬레이션 에이전트."""
    def __init__(self, agent_id: int) -> None:
        self.id: int = agent_id
        self.dna: DNA = DNA()
        self.balance: float = 1000.0
        self.validator: SignalValidator = SignalValidator() # 🛡️ 각 선수마다 검증기 장착
        self.trades: int = 0

    def simulate(self, raw_1min_df: pd.DataFrame) -> None:
        """주어진 데이터에 대해 DNA 전략을 시뮬레이션합니다."""
        try:
            # 1. DNA 타임프레임으로 리샘플링
            df = raw_1min_df.resample(self.dna.timeframe).agg({
                'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'
            }).dropna()
        except Exception:
            return

        if len(df) < 60: return

        # 2. 기술적 지표 계산
        df['MA_S'] = df['Close'].rolling(self.dna.ma_short).mean()
        df['MA_L'] = df['Close'].rolling(self.dna.ma_long).mean()
        
        position: bool = False
        entry_price: float = 0.0
        
        # 가속을 위한 Numpy 변환
        closes = df['Close'].values
        highs = df['High'].values
        lows = df['Low'].values
        ma_s = df['MA_S'].values
        ma_l = df['MA_L'].values
        
        # 3. 시뮬레이션 루프
        for i in range(60, len(df)):
            curr_price = closes[i]
            
            # [매수 로직]
            if not position:
                # 1단계: 기술적 골든크로스
                if ma_s[i] > ma_l[i] and ma_s[i-1] <= ma_l[i-1]:
                    
                    # 2단계: 🛡️ Savage Validator 검증 (핵심)
                    curr_row = df.iloc[i]
                    past_data = df.iloc[:i+1] 
                    
                    # 시뮬레이션 모드("SIM")로 검증기 가동
                    is_valid, _ = self.validator.validate("SIM", curr_row.to_dict(), past_data, {})
                    
                    if is_valid:
                        position = True
                        entry_price = curr_price
                        self.trades += 1
            
            # [청산 로직]
            elif position:
                pct_high = (highs[i] - entry_price) / entry_price
                pct_low = (lows[i] - entry_price) / entry_price
                
                pnl: float = 0.0
                executed: bool = False
                
                if pct_low <= -self.dna.stop_loss:
                    pnl = -self.dna.stop_loss
                    executed = True
                elif pct_high >= self.dna.take_profit:
                    pnl = self.dna.take_profit
                    executed = True
                
                if executed:
                    self.balance *= (1 + pnl)
                    position = False

class GenesisV2:
    """통합 진화 매니저."""
    def __init__(self, data_path: str) -> None:
        self.data_path: str = data_path
        self.population: int = 100
        self.generations: int = 3
        self.agents: List[IntegratedAgent] = []
        
        print(f"📂 [GENESIS] 데이터 로드 중: {data_path}")
        self.raw_data = pd.read_csv(self.data_path)
        if 'Date' in self.raw_data.columns:
            self.raw_data['Date'] = pd.to_datetime(self.raw_data['Date'])
            self.raw_data.set_index('Date', inplace=True)

    def run(self) -> None:
        """진화 프로세스 시작."""
        self.agents = [IntegratedAgent(i) for i in range(self.population)]
        
        for g in range(1, self.generations + 1):
            print(f"\n⚔️ [Gen {g}] Savage Validator 통합 훈련 시작...")
            
            for agent in tqdm(self.agents):
                agent.balance = 1000.0 
                agent.simulate(self.raw_data)
            
            # 성적순 정렬
            self.agents.sort(key=lambda x: x.balance, reverse=True)
            top = self.agents[0]
            
            print(f"🏆 1위 수익률: {(top.balance/1000 - 1)*100:.2f}% ({top.trades}회 거래)")
            print(f"   🧬 DNA: {top.dna.timeframe} | MA:{top.dna.ma_short}/{top.dna.ma_long} | TP:{top.dna.take_profit} | SL:{top.dna.stop_loss}")
            
            # 하위 50% 도태 및 상위 50% 복제/변이
            survivors = self.agents[:50]
            for i in range(50, 100):
                parent = random.choice(survivors)
                child = copy.deepcopy(parent)
                child.dna.mutate()
                self.agents[i] = child
                
        self.save_dna(self.agents[0].dna)

    def save_dna(self, dna: DNA) -> None:
        """최종 DNA 저장."""
        os.makedirs("config", exist_ok=True)
        with open("config/dna.json", "w") as f:
            json.dump(dna.__dict__, f, indent=4)
        print("\n💾 [COMPLETE] 실전 최적화 DNA 저장 완료: config/dna.json")

if __name__ == "__main__":
    # 데이터 경로가 실제 환경에 따라 다를 수 있으므로 확인 필요
    DATA_FILE = "data/KR/BTC-KRW.csv"
    if os.path.exists(DATA_FILE):
        GenesisV2(DATA_FILE).run()
    else:
        # 파일이 없을 경우 예시 데이터 생성 또는 스킵
        print(f"⚠️ 데이터 파일 부재: {DATA_FILE}")
