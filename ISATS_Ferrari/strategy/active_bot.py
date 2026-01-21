import os
import sys

# 경로 보정: ISATS_Ferrari 폴더를 path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.append(project_root)

import torch
import pandas as pd
import numpy as np
from datetime import datetime
from brain.models import HybridCNN_LSTM
from brain.elastic_time_machine import ElasticTimeMachine
from utils.notifier import TelegramBot

# ==========================================
# 🧬 SELF-EVOLVING ACTIVE BOT (자가 진화형 엔진)
# ==========================================

class ActiveBot:
    def __init__(self, ticker="005930.KS"):
        self.ticker = ticker
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = HybridCNN_LSTM().to(self.device)
        self.etm = ElasticTimeMachine()
        self.notifier = TelegramBot()
        
        # 상태 변수
        self.current_lens = 13      # 현재 적용 중인 시간봉 (기본: 13분)
        self.memory_buffer = []     # 오늘 수집한 실시간 1분봉 데이터
        self.positions = 0
        self.is_market_open = True
        
        # 모델 로드
        self.load_model()

    def load_model(self):
        """학습된 가중치 로드"""
        path = f"brain/weights/deep_eyes_{self.ticker.split('.')[0]}_latest.pth"
        if os.path.exists(path):
            self.model.load_state_dict(torch.load(path, map_address=self.device))
            print(f"✅ [ActiveBot] 최신 두뇌 로드 완료: {path}")
        else:
            print("⚠️ [ActiveBot] 학습된 가중치가 없습니다. 기본 모델로 시작합니다.")

    def on_tick(self, tick_data):
        """
        실시간 1분봉 유입 시 호출
        tick_data: {'Date', 'Open', 'High', 'Low', 'Close', 'Volume'}
        """
        self.memory_buffer.append(tick_data)
        
        # 현재 렌즈(n분) 주기에 도달했는지 확인
        if len(self.memory_buffer) % self.current_lens == 0:
            self.analyze_and_execute()

    def analyze_and_execute(self):
        """현재 렌즈를 기준으로 패턴 분석 및 매매 실행"""
        # 1. 시뮬레이션용 리샘플링
        df_1m = pd.DataFrame(self.memory_buffer)
        df_resampled = self.etm.resample_custom(df_1m, self.current_lens)
        
        if len(df_resampled) < 60: return # 최소 데이터 확보 전까지 대기
        
        # 2. 입력을 텐서로 변환 (최근 60개 봉)
        cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        recent_data = df_resampled[cols].tail(60)
        # Normalization
        norm_data = (recent_data - recent_data.min()) / (recent_data.max() - recent_data.min() + 1e-8)
        input_tensor = torch.FloatTensor(norm_data.values).unsqueeze(0).to(self.device)
        
        # 3. AI 판단 (CNN-LSTM)
        self.model.eval()
        with torch.no_grad():
            prediction = self.model(input_tensor).item()
        
        # 4. 매매 로직 (Reflex)
        current_price = df_1m.iloc[-1]['Close']
        if prediction > 0.65: # 강력 매수 신호
            self.execute_trade("BUY", current_price)
        elif prediction < 0.35: # 강력 매도 신호
            self.execute_trade("SELL", current_price)

    def execute_trade(self, action, price):
        """주문 집행 및 알림"""
        print(f"🚀 [Trade] {action} @ {price} (Lens: {self.current_lens}T)")
        asyncio.run(self.notifier.send(f"전략 집행: {action} / 가격: {price:,}원 / 렌즈: {self.current_lens}분봉"))
        # 실제 주문 API 호출 연동 필요 (kis_api_bridge 등)

    def train_overnight(self):
        """
        [야간 세션] 주경야독 로직
        오늘 수집한 데이터를 학습하고, 내일의 최적 렌즈 선정
        """
        print(f"\n🌙 [Night Session] {self.ticker} 자가 학습 및 진화 개시")
        
        if len(self.memory_buffer) < 100:
            print("⚠️ 데이터가 부족하여 오늘 학습은 생략합니다.")
            return

        # 1. 오늘 데이터 저장
        today_str = datetime.now().strftime("%Y%m%d")
        df_today = pd.DataFrame(self.memory_buffer)
        save_path = f"data/KR/{self.ticker}_{today_str}_1m.csv"
        df_today.to_csv(save_path, index=False)
        
        # 2. 렌즈 최적화 (Morphing)
        # 모든 소수 렌즈(4, 7, 13, 17) 중 오늘 가장 수익률 좋았을 법한 렌즈 수색
        best_lens = self.current_lens
        best_score = -1
        
        for lens in [4, 7, 13, 17]:
            score = self.simulate_lens(df_today, lens)
            if score > best_score:
                best_score = score
                best_lens = lens
        
        self.current_lens = best_lens
        print(f"🧬 [Evolution] 내일의 최적 렌즈 확정: {self.current_lens}분봉")
        
        # 3. AI 모델 미세 조정 (Fine-tuning)
        # (brain/trainer.py 의 로직을 활용하여 self.memory_buffer로 훈련)
        self.fine_tune_with_today_data()
        
        asyncio.run(self.notifier.send(f"자가 진화 완료. 내일은 {self.current_lens}분봉으로 시장을 공략합니다."))

    def simulate_lens(self, df, lens):
        """특정 렌즈의 성과 시뮬레이션 (간략화)"""
        # ... 시뮬레이션 로직 ...
        return np.random.random() # 예시

    def fine_tune_with_today_data(self):
        """오늘 데이터를 뇌에 각인"""
        # ... trainer.py 와 연동되는 학습 로직 ...
        pass

if __name__ == "__main__":
    import asyncio
    bot = ActiveBot()
    # 임시 실행 루프 테스트
    asyncio.run(bot.notifier.send("자가 진화형 ActiveBot 엔진 점화 완료."))
