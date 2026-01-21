import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
import numpy as np
import os
import sys
from tqdm import tqdm

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from brain.models import HybridCNN_LSTM

# ==========================================
# 🕰️ OPERATION: TIME MACHINE (타임머신 훈련)
# ==========================================

class TimeMachineTrainer:
    def __init__(self, ticker="005930.KS", market="KR"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.ticker = ticker
        self.market = market
        # 데이터 경로 설정 (프로젝트 루트 기준)
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_path = os.path.join(project_root, "data", market, f"{ticker}.csv")
        
        # 하이퍼파라미터
        self.seq_length = 60
        self.balance = 10_000_000  # 초기 자본금 1,000만원
        self.shares = 0
        self.history = []
        
        # AI 모델 초기화
        self.model = HybridCNN_LSTM().to(self.device)
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.001)
        self.criterion = nn.BCELoss()

    def load_and_prepare_data(self):
        """데이터를 로드하고 전처리"""
        if not os.path.exists(self.data_path):
            print(f"❌ [Error] 데이터 파일이 없습니다: {self.data_path}")
            return None

        df = pd.read_csv(self.data_path)
        # 날짜 정렬 확인
        df = df.sort_values('Date').reset_index(drop=True)
        
        # 필요한 컬럼만 추출 및 정규화
        cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        self.raw_df = df # 원본 보존 (가격 계산용)
        
        # MinMax Scaling
        self.df_norm = (df[cols] - df[cols].min()) / (df[cols].max() - df[cols].min() + 1e-8)
        return len(df)

    def run_simulation(self, start_idx_offset=500):
        """
        start_idx_offset: 뒤에서부터 며칠 전으로 돌아갈지 (예: 500일 전)
        """
        total_len = self.load_and_prepare_data()
        if not total_len: return

        # 1. 타임머신 가동 시점 설정 (예: 전체 길이 - 500일 전)
        start_idx = total_len - start_idx_offset
        if start_idx < self.seq_length:
            start_idx = self.seq_length + 1

        print(f"\n🕰️ [Time Machine] {self.ticker}의 {start_idx_offset}일 전 과거로 이동합니다...")
        print(f"   -> 시작일: {self.raw_df.iloc[start_idx]['Date']}")
        print(f"   -> 초기 자본: {self.balance:,}원")
        print("="*60)

        # 2. 초기 학습 (과거 데이터만으로 베이스 모델 생성)
        print("🧠 [Brain] 과거 기억 주입 중 (Base Training)...")
        self._train_base_model(end_idx=start_idx)

        # 3. 하루하루 살아가기 (Walk-Forward)
        win = 0
        loss_cnt = 0
        
        # 진행바 생성
        pbar = tqdm(range(start_idx, total_len - 1), desc="Daily Trading", unit="day")
        
        for t in pbar:
            # --- (1) 아침: 어제까지의 데이터로 학습 ---
            self._finetune_model(current_idx=t)
            
            # --- (2) 오후: 내일 예측 ---
            input_seq = self.df_norm.iloc[t-self.seq_length : t].values
            input_tensor = torch.FloatTensor(input_seq).unsqueeze(0).to(self.device)
            
            self.model.eval()
            with torch.no_grad():
                pred = self.model(input_tensor).item()
            
            # --- (3) 매매 결정 ---
            current_price = self.raw_df.iloc[t]['Close']
            next_real_price = self.raw_df.iloc[t+1]['Close']
            date = self.raw_df.iloc[t]['Date']
            
            action = "HOLD"
            # AI가 60% 이상 확신하면 매수
            if pred > 0.6 and self.balance > 0:
                buy_amt = int(self.balance // current_price)
                if buy_amt > 0:
                    self.shares = buy_amt
                    self.balance -= buy_amt * current_price
                    action = "BUY"
            
            # AI가 40% 이하로 비관하면 매도
            elif pred < 0.4 and self.shares > 0:
                self.balance += self.shares * current_price
                self.shares = 0
                action = "SELL"
            
            # --- (4) 결과 확인 (내일이 됨) ---
            asset_value = self.balance + (self.shares * next_real_price)
            profit = (asset_value - 10_000_000) / 10_000_000 * 100
            
            is_correct = (pred > 0.5 and next_real_price > current_price) or \
                         (pred <= 0.5 and next_real_price <= current_price)
            if is_correct: win += 1
            else: loss_cnt += 1
            
            pbar.set_postfix({
                'Profit': f"{profit:.1f}%", 
                'Acc': f"{win/(win+loss_cnt)*100:.1f}%",
                'Action': action
            })
            
            self.history.append({
                'Date': date, 'Price': current_price, 'Action': action, 
                'Asset': asset_value, 'AI_Score': pred
            })

        print("\n" + "="*60)
        final_profit = self.history[-1]['Asset']
        roi = (final_profit - 10_000_000) / 10_000_000 * 100
        print(f"🎉 [Simulation End] 미래 도달 완료.")
        print(f"   💰 최종 자산: {int(final_profit):,}원 (수익률: {roi:.2f}%)")
        print(f"   🎯 AI 예측 적중률: {win/(win+loss_cnt)*100:.2f}%")
        
        # 결과 저장
        pd.DataFrame(self.history).to_csv(f"time_machine_result_{self.ticker}.csv", index=False)
        print(f"   💾 상세 기록 저장됨: time_machine_result_{self.ticker}.csv")

    def _train_base_model(self, end_idx):
        """시뮬레이션 시작 전 기본 학습"""
        X, y = [], []
        data = self.df_norm.values
        start_train = max(0, end_idx - 365)
        
        for i in range(start_train + self.seq_length, end_idx - 1):
            X.append(data[i-self.seq_length : i])
            if data[i+1][3] > data[i][3]:
                y.append(1.0)
            else:
                y.append(0.0)
                
        if not X: return

        X_tensor = torch.FloatTensor(np.array(X)).to(self.device)
        y_tensor = torch.FloatTensor(np.array(y)).unsqueeze(1).to(self.device)
        
        self.model.train()
        for _ in range(10):
            self.optimizer.zero_grad()
            out = self.model(X_tensor)
            loss = self.criterion(out, y_tensor)
            loss.backward()
            self.optimizer.step()

    def _finetune_model(self, current_idx):
        """매일매일 실시간 재학습"""
        if current_idx < self.seq_length + 1: return
        
        data = self.df_norm.values
        prev_idx = current_idx - 1
        
        X = data[prev_idx-self.seq_length : prev_idx]
        target = 1.0 if data[current_idx][3] > data[prev_idx][3] else 0.0
            
        X_tensor = torch.FloatTensor(X).unsqueeze(0).to(self.device)
        y_tensor = torch.FloatTensor([[target]]).to(self.device)
        
        self.model.train()
        self.optimizer.zero_grad()
        out = self.model(X_tensor)
        loss = self.criterion(out, y_tensor)
        loss.backward()
        self.optimizer.step()
