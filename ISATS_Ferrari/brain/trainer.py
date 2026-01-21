import os
import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
import numpy as np
from torch.utils.data import Dataset, DataLoader
from tqdm import tqdm
import sys

# 경로 설정
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from brain.models import HybridCNN_LSTM

# ==========================================
# 🏋️ Deep Eyes Training System
# ==========================================

# 설정
SEQ_LENGTH = 60   # 과거 60일(또는 60개 캔들)을 보고 판단
PREDICT_DAY = 1   # 다음 1일 뒤를 예측
BATCH_SIZE = 32
EPOCHS = 5
LEARNING_RATE = 0.001
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class StockDataset(Dataset):
    def __init__(self, data_dir, market="KR", limit_files=20):
        self.samples = []
        self.targets = []
        
        target_dir = os.path.join(data_dir, market)
        
        if not os.path.exists(target_dir):
            print(f"❌ [{market}] 데이터 폴더가 없습니다: {target_dir}")
            return
            
        files = [f for f in os.listdir(target_dir) if f.endswith('.csv')]
        
        if not files:
            print(f"❌ [{market}] CSV 파일이 없습니다. 먼저 채굴을 수행하세요.")
            return
        
        print(f"📚 [{market}] 데이터 로딩 중... (최대 {limit_files}개 종목 학습)")
        
        for file in tqdm(files[:limit_files]): # 너무 많으면 메모리 터지므로 제한
            path = os.path.join(target_dir, file)
            try:
                df = pd.read_csv(path)
                
                # 데이터 전처리 (정규화)
                cols = ['Open', 'High', 'Low', 'Close', 'Volume']
                if not all(c in df.columns for c in cols): 
                    continue
                
                # NaN 제거
                df = df.dropna()
                if len(df) < SEQ_LENGTH + PREDICT_DAY:
                    continue
                
                # 간단한 MinMax Scaling
                df_norm = (df[cols] - df[cols].min()) / (df[cols].max() - df[cols].min() + 1e-6)
                
                data = df_norm.values
                close_prices = df['Close'].values # 원본 종가
                
                # 시퀀스 생성
                for i in range(len(data) - SEQ_LENGTH - PREDICT_DAY):
                    x = data[i : i+SEQ_LENGTH]
                    
                    # 라벨링: 내일 종가가 오늘 종가보다 2% 이상 오르면 1
                    today_close = close_prices[i + SEQ_LENGTH - 1]
                    tomorrow_close = close_prices[i + SEQ_LENGTH]
                    
                    if tomorrow_close > today_close * 1.02:
                        y = 1.0
                    else:
                        y = 0.0
                        
                    self.samples.append(x)
                    self.targets.append(y)
            except Exception as e:
                continue
                
        if len(self.samples) > 0:
            self.samples = torch.FloatTensor(np.array(self.samples))
            self.targets = torch.FloatTensor(np.array(self.targets)).unsqueeze(1)
            print(f"✅ 데이터셋 준비 완료: 총 {len(self.samples)}개 샘플")
        else:
            print(f"❌ 유효한 샘플을 생성하지 못했습니다.")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        return self.samples[idx], self.targets[idx]

def train():
    print(f"🚀 [Training] Deep Eyes 학습 시작 (Device: {DEVICE})")
    
    # 1. 데이터 로드
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    
    # 한국 주식 데이터로 학습
    dataset = StockDataset(data_dir, market="KR", limit_files=20) 
    if len(dataset) == 0:
        print("❌ 학습할 데이터가 없습니다. 먼저 채굴(mass_data_miner)을 수행하세요.")
        return

    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)
    
    # 2. 모델 초기화
    model = HybridCNN_LSTM().to(DEVICE)
    criterion = nn.BCELoss() # 이진 분류
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    
    # 3. 학습 루프
    model.train()
    for epoch in range(EPOCHS):
        total_loss = 0
        correct = 0
        total = 0
        
        progress = tqdm(dataloader, desc=f"Epoch {epoch+1}/{EPOCHS}")
        for X, y in progress:
            X, y = X.to(DEVICE), y.to(DEVICE)
            
            optimizer.zero_grad()
            output = model(X)
            loss = criterion(output, y)
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            
            # 정확도 계산
            predicted = (output > 0.5).float()
            correct += (predicted == y).sum().item()
            total += y.size(0)
            
            progress.set_postfix({'Loss': loss.item()})
            
        avg_loss = total_loss / len(dataloader)
        acc = correct / total * 100
        print(f"   📊 Epoch {epoch+1} 결과 -> Loss: {avg_loss:.4f} | Accuracy: {acc:.2f}%")

    # 4. 모델 저장
    save_dir = os.path.join(base_dir, "brain", "weights")
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, "deep_eyes_v2_latest.pth")
    torch.save(model.state_dict(), save_path)
    
    print("\n🎉 [Complete] 학습 완료!")
    print(f"   💾 모델 저장됨: {save_path}")
    print("   -> 이제 main.py를 실행하면 이 두뇌를 사용합니다.")

if __name__ == "__main__":
    train()
