"""
📈 ISATS v6.0 - Stockformer (시계열 예측 모델)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

작전명: "Transformer + 1D-CNN 기반 주가 예측"

역할:
- Transformer 구조로 시간적 패턴 학습
- 1D-CNN으로 지역적 특징 추출
- Granger 인과관계 기반 다변량 입력
- 다음 5일 주가 예측

작성자: ISATS Neural Swarm
버전: 6.0 (Stockformer)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import sys
import numpy as np
import pandas as pd
from typing import List, Tuple, Optional
from datetime import datetime, timedelta

# 프로젝트 루트
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 선택적 임포트
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import Dataset, DataLoader
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    print("⚠️ [Warning] PyTorch not found. Installing...")
    os.system("pip install torch --quiet")
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import Dataset, DataLoader
    HAS_TORCH = True

try:
    from sklearn.preprocessing import MinMaxScaler
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    print("⚠️ [Warning] scikit-learn not found. Installing...")
    os.system("pip install scikit-learn --quiet")
    from sklearn.preprocessing import MinMaxScaler
    HAS_SKLEARN = True


# ==========================================
# 📊 데이터셋
# ==========================================

class StockDataset(Dataset):
    """주가 시계열 데이터셋"""
    
    def __init__(
        self,
        data: pd.DataFrame,
        seq_length: int = 60,
        pred_length: int = 5
    ):
        """
        Args:
            data: OHLCV 데이터프레임
            seq_length: 입력 시퀀스 길이 (60일)
            pred_length: 예측 길이 (5일)
        """
        self.seq_length = seq_length
        self.pred_length = pred_length
        
        # 정규화
        self.scaler = MinMaxScaler()
        self.data = self.scaler.fit_transform(data.values)
        
        # 시퀀스 생성
        self.sequences = []
        self.targets = []
        
        for i in range(len(self.data) - seq_length - pred_length):
            seq = self.data[i:i + seq_length]
            target = self.data[i + seq_length:i + seq_length + pred_length, 3]  # Close 가격
            
            self.sequences.append(seq)
            self.targets.append(target)
        
        self.sequences = np.array(self.sequences)
        self.targets = np.array(self.targets)
    
    def __len__(self):
        return len(self.sequences)
    
    def __getitem__(self, idx):
        return (
            torch.FloatTensor(self.sequences[idx]),
            torch.FloatTensor(self.targets[idx])
        )


# ==========================================
# 🧠 Stockformer 모델
# ==========================================

class Stockformer(nn.Module):
    """Transformer + 1D-CNN 기반 주가 예측 모델"""
    
    def __init__(
        self,
        input_dim: int = 5,  # OHLCV
        d_model: int = 128,
        nhead: int = 8,
        num_layers: int = 3,
        pred_length: int = 5
    ):
        """
        Args:
            input_dim: 입력 차원 (OHLCV = 5)
            d_model: Transformer 임베딩 차원
            nhead: Multi-head Attention 헤드 수
            num_layers: Transformer 레이어 수
            pred_length: 예측 길이
        """
        super(Stockformer, self).__init__()
        
        self.input_dim = input_dim
        self.d_model = d_model
        self.pred_length = pred_length
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 1D-CNN (지역적 특징 추출)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        self.conv1 = nn.Conv1d(input_dim, 64, kernel_size=3, padding=1)
        self.conv2 = nn.Conv1d(64, d_model, kernel_size=3, padding=1)
        self.relu = nn.ReLU()
        self.pool = nn.MaxPool1d(2)
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Transformer Encoder
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=512,
            dropout=0.1,
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 출력 레이어
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        self.fc1 = nn.Linear(d_model, 64)
        self.fc2 = nn.Linear(64, pred_length)
        self.dropout = nn.Dropout(0.1)
    
    def forward(self, x):
        """
        Args:
            x: (batch_size, seq_length, input_dim)
        
        Returns:
            (batch_size, pred_length)
        """
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 1D-CNN
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        # (batch, seq, input_dim) -> (batch, input_dim, seq)
        x = x.permute(0, 2, 1)
        
        x = self.relu(self.conv1(x))
        x = self.relu(self.conv2(x))
        
        # (batch, d_model, seq) -> (batch, seq, d_model)
        x = x.permute(0, 2, 1)
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Transformer
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        x = self.transformer(x)
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 출력 (마지막 타임스텝만 사용)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        x = x[:, -1, :]  # (batch, d_model)
        x = self.dropout(self.relu(self.fc1(x)))
        x = self.fc2(x)  # (batch, pred_length)
        
        return x


# ==========================================
# 🎓 학습 및 예측
# ==========================================

class StockformerTrainer:
    """Stockformer 학습 및 예측"""
    
    def __init__(
        self,
        model: Stockformer,
        device: str = "cpu"
    ):
        self.model = model.to(device)
        self.device = device
        self.criterion = nn.MSELoss()
        self.optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    def train(
        self,
        train_loader: DataLoader,
        epochs: int = 50,
        verbose: bool = True
    ):
        """
        모델 학습
        
        Args:
            train_loader: 학습 데이터 로더
            epochs: 에폭 수
            verbose: 로그 출력 여부
        """
        self.model.train()
        
        for epoch in range(epochs):
            total_loss = 0
            
            for batch_x, batch_y in train_loader:
                batch_x = batch_x.to(self.device)
                batch_y = batch_y.to(self.device)
                
                # Forward
                pred = self.model(batch_x)
                loss = self.criterion(pred, batch_y)
                
                # Backward
                self.optimizer.zero_grad()
                loss.backward()
                self.optimizer.step()
                
                total_loss += loss.item()
            
            if verbose and (epoch + 1) % 10 == 0:
                avg_loss = total_loss / len(train_loader)
                print(f"Epoch [{epoch+1}/{epochs}], Loss: {avg_loss:.6f}")
    
    def predict(self, x: torch.Tensor) -> np.ndarray:
        """
        예측
        
        Args:
            x: 입력 시퀀스 (seq_length, input_dim)
        
        Returns:
            예측값 (pred_length,)
        """
        self.model.eval()
        
        with torch.no_grad():
            x = x.unsqueeze(0).to(self.device)  # (1, seq_length, input_dim)
            pred = self.model(x)
            return pred.cpu().numpy()[0]
    
    def save(self, path: str):
        """모델 저장"""
        torch.save(self.model.state_dict(), path)
        print(f"✅ 모델 저장: {path}")
    
    def load(self, path: str):
        """모델 로드"""
        self.model.load_state_dict(torch.load(path))
        print(f"✅ 모델 로드: {path}")


# ==========================================
# 실행
# ==========================================

if __name__ == "__main__":
    print(f"\n{'='*80}")
    print(f"📈 Stockformer 테스트")
    print(f"{'='*80}\n")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 1. 데이터 로드
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    # 예시: 삼성전자 데이터
    data_path = "data/KR/005930.KS.csv"
    
    if os.path.exists(data_path):
        df = pd.read_csv(data_path)
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()
        
        print(f"✅ 데이터 로드: {len(df)}개 레코드")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 2. 데이터셋 생성
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        dataset = StockDataset(df, seq_length=60, pred_length=5)
        train_loader = DataLoader(dataset, batch_size=32, shuffle=True)
        
        print(f"✅ 데이터셋 생성: {len(dataset)}개 시퀀스")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 3. 모델 생성 및 학습
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        model = Stockformer(input_dim=5, d_model=128, nhead=8, num_layers=3, pred_length=5)
        trainer = StockformerTrainer(model, device="cpu")
        
        print(f"\n🎓 모델 학습 시작...\n")
        trainer.train(train_loader, epochs=50, verbose=True)
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 4. 예측
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        last_seq = torch.FloatTensor(dataset.sequences[-1])
        prediction = trainer.predict(last_seq)
        
        print(f"\n{'='*80}")
        print(f"📊 예측 결과 (다음 5일)")
        print(f"{'='*80}")
        print(f"예측값: {prediction}")
        print(f"{'='*80}\n")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 5. 모델 저장
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        trainer.save("brain/stockformer_model.pth")
    
    else:
        print(f"❌ 데이터 파일 없음: {data_path}")
        print(f"   먼저 utils/universal_data_collector.py를 실행하세요.")
