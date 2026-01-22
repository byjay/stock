import pandas as pd
import numpy as np
import random
import os
import sys
import copy
import json
from tqdm import tqdm

# 프로젝트 루트 및 모듈 경로 설정
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.signal_validator import SignalValidator

# ==========================================
# 🧬 GENESIS EVOLUTION v2.0 (Integrated)
# "검증기를 통과하지 못하면 수익도 없다."
# ==========================================

class DNA:
    """전략 유전자: 매매 성향 결정"""
    def __init__(self):
        # 고무줄 분봉 (소수 포함)
        self.timeframe = random.choice(['3T', '5T', '7T', '13T', '17T'])
        # 이동평균선
        self.ma_short = random.randint(3, 10)
        self.ma_long = random.randint(20, 60)
        # 리스크 관리 (익절/손절)
        self.take_profit = round(random.uniform(0.02, 0.15), 3) # 2% ~ 15%
        self.stop_loss = round(random.uniform(0.01, 0.05), 3)   # 1% ~ 5%
        
    def mutate(self):
        """유전자 변이"""
        if random.random() < 0.1:
            self.timeframe = random.choice(['3T', '7T', '13T'])
        if random.random() < 0.1:
            self.take_profit = round(random.uniform(0.02, 0.20), 3)

class IntegratedAgent:
    """검증기를 장착한 훈련생"""
    def __init__(self, agent_id):
        self.id = agent_id
        self.dna = DNA()
        self.balance = 1000.0
        self.validator = SignalValidator() # 🛡️ 각 선수마다 검증기 장착 (핵심)
        self.trades = 0

    def simulate(self, raw_1min_df):
        # 1. DNA 분봉 생성 (Resampling)
        try:
            df = raw_1min_df.resample(self.dna.timeframe).agg({
                'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'
            }).dropna()
        except:
            return

        if len(df) < self.dna.ma_long: return

        # 2. 지표 계산
        df['MA_S'] = df['Close'].rolling(self.dna.ma_short).mean()
        df['MA_L'] = df['Close'].rolling(self.dna.ma_long).mean()
        
        position = False
        entry_price = 0
        
        # Numpy 변환 가속 (속도 최적화)
        closes = df['Close'].values
        highs = df['High'].values
        lows = df['Low'].values
        ma_s = df['MA_S'].values
        ma_l = df['MA_L'].values
        
        # 3. 시뮬레이션 루프
        # (지표 계산을 위해 ma_long 이후부터 시작)
        for i in range(self.dna.ma_long, len(df)):
            curr_price = closes[i]
            
            # [매수 시도]
            if not position:
                # 1차: 기술적 신호 (골든크로스)
                if ma_s[i] > ma_l[i] and ma_s[i-1] <= ma_l[i-1]:
                    
                    # 2차: 🛡️ Savage Validator 검증 (실전과 동일한 검문소)
                    # 시뮬레이션 속도를 위해 DataFrame Row 하나를 넘김
                    curr_row = df.iloc[i]
                    past_data = df.iloc[:i+1] # 현재 시점까지의 데이터
                    
                    # 검증기 호출 ("가짜 신호면 진입 불허")
                    is_valid, _ = self.validator.validate("SIM", curr_row.to_dict(), past_data, {})
                    
                    if is_valid:
                        position = True
                        entry_price = curr_price
                        self.trades += 1
            
            # [청산 시도]
            elif position:
                pct_high = (highs[i] - entry_price) / entry_price
                pct_low = (lows[i] - entry_price) / entry_price
                
                action = None
                pnl = 0
                
                # 손절 (보수적 접근)
                if pct_low <= -self.dna.stop_loss:
                    action = 'SL'
                    pnl = -self.dna.stop_loss
                # 익절
                elif pct_high >= self.dna.take_profit:
                    action = 'TP'
                    pnl = self.dna.take_profit
                
                if action:
                    self.balance *= (1 + pnl)
                    position = False

class GenesisV2:
    def __init__(self, data_path):
        self.data_path = data_path
        self.population = 100 # 속도를 위해 100명 정예
        self.generations = 3  # 3세대 진화
        self.agents = []
        
        print(f"📂 [Genesis] 데이터 로드 중: {os.path.basename(data_path)}")
        self.raw_data = pd.read_csv(self.data_path)
        if 'Date' in self.raw_data.columns:
            self.raw_data['Date'] = pd.to_datetime(self.raw_data['Date'])
            self.raw_data.set_index('Date', inplace=True)

    def run(self):
        self.agents = [IntegratedAgent(i) for i in range(self.population)]
        
        for g in range(1, self.generations + 1):
            print(f"\n⚔️ [Gen {g}] 검증기 통합 실전 훈련 시작...")
            
            # 병렬 처리 대신 가시성을 위해 tqdm 루프 사용
            for agent in tqdm(self.agents):
                agent.balance = 1000.0 # 자산 초기화 (공정한 경쟁)
                agent.simulate(self.raw_data)
            
            # 생존자 정렬 (수익금 순)
            self.agents.sort(key=lambda x: x.balance, reverse=True)
            top = self.agents[0]
            
            # 현황 중계
            profit_rate = (top.balance/1000 - 1)*100
            print(f"🏆 1위 수익률: {profit_rate:.2f}% ({top.trades}회 거래)")
            print(f"   🧬 DNA: {top.dna.timeframe} | TP:{top.dna.take_profit} | SL:{top.dna.stop_loss}")
            
            # 진화 (하위 50% 도태 및 교체)
            if g < self.generations:
                survivors = self.agents[:50]
                for i in range(50, 100):
                    parent = random.choice(survivors)
                    child = copy.deepcopy(parent)
                    child.dna.mutate() # 돌연변이
                    self.agents[i] = child
                
        # 최종 DNA 저장
        self.save_dna(self.agents[0].dna)

    def save_dna(self, dna):
        # config 폴더 확인
        config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config")
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
            
        save_path = os.path.join(config_dir, "dna.json")
        
        with open(save_path, "w") as f:
            json.dump(dna.__dict__, f, indent=4)
        print(f"\n💾 [Complete] 실전 최적화 DNA 저장 완료: {save_path}")
        print("   -> 이제 'ActiveBot'이 이 DNA를 장착하고 출격합니다.")

if __name__ == "__main__":
    # 데이터 파일 경로 (예시)
    target = "data/KR/BTC-KRW.csv"
    if os.path.exists(target):
        sim = GenesisV2(target)
        sim.run()
    else:
        print(f"❌ 데이터 파일이 없습니다: {target}")
        print("   (utils/mass_data_miner.py를 실행하거나 data/KR 폴더에 CSV를 넣어주세요)")
