# -*- coding: utf-8 -*-
"""
================================================================================
🧠 ISATS 딥러닝 트레이딩 학습 시스템
================================================================================
가상매매의 모든 거래 내역을 학습하여 최적의 매매 전략을 찾습니다.

학습 데이터:
- 매수/매도 시점
- 가격 변동 패턴
- 수익률
- 시장 상황

모델:
- LSTM (시계열 예측)
- Transformer (패턴 인식)
- Reinforcement Learning (강화학습)
================================================================================
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

import pandas as pd
import numpy as np

# 딥러닝 라이브러리 (선택적)
try:
    import torch
    import torch.nn as nn
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    logging.warning("PyTorch 미설치. 딥러닝 기능 제한됨")

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ================================================================================
# 📊 거래 데이터 분석기
# ================================================================================

class TradeAnalyzer:
    """거래 내역 분석 및 학습 데이터 생성"""
    
    def __init__(self, wallet_file: str = None):
        if wallet_file is None:
            wallet_file = os.path.join(current_dir, "data", "virtual_wallet.json")
        
        self.wallet_file = wallet_file
        self.trades = []
        self.features = []
        self.labels = []
    
    def load_trades(self) -> List[Dict]:
        """거래 내역 로드"""
        if not os.path.exists(self.wallet_file):
            logger.warning("거래 내역 없음")
            return []
        
        with open(self.wallet_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.trades = data.get("trade_history", [])
        
        logger.info(f"📊 거래 내역 로드: {len(self.trades)}건")
        return self.trades
    
    def analyze_performance(self) -> Dict:
        """성과 분석"""
        if not self.trades:
            self.load_trades()
        
        if not self.trades:
            return {}
        
        df = pd.DataFrame(self.trades)
        
        # 매수/매도 분리
        buys = df[df['action'] == 'BUY']
        sells = df[df['action'] == 'SELL']
        
        # 통계
        stats = {
            "total_trades": len(self.trades),
            "buy_count": len(buys),
            "sell_count": len(sells),
            "total_profit": sells['profit'].sum() if 'profit' in sells.columns else 0,
            "avg_profit_rate": sells['profit_rate'].mean() if 'profit_rate' in sells.columns else 0,
            "win_rate": (sells['profit'] > 0).sum() / len(sells) * 100 if len(sells) > 0 else 0,
        }
        
        logger.info(f"📈 성과 분석:")
        logger.info(f"  총 거래: {stats['total_trades']}건")
        logger.info(f"  매수: {stats['buy_count']}건, 매도: {stats['sell_count']}건")
        logger.info(f"  총 손익: {stats['total_profit']:+,.0f}원")
        logger.info(f"  평균 수익률: {stats['avg_profit_rate']:+.2f}%")
        logger.info(f"  승률: {stats['win_rate']:.1f}%")
        
        return stats
    
    def prepare_training_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """학습 데이터 준비"""
        if not self.trades:
            self.load_trades()
        
        # 매도 거래만 (결과가 있는 거래)
        df = pd.DataFrame(self.trades)
        sells = df[df['action'] == 'SELL'].copy()
        
        if len(sells) < 10:
            logger.warning("학습 데이터 부족 (최소 10건 필요)")
            return np.array([]), np.array([])
        
        # 특징 추출
        features = []
        labels = []
        
        for _, trade in sells.iterrows():
            # 특징: [가격, 수량, 시간대, 요일]
            time = pd.to_datetime(trade['time'])
            feature = [
                trade['price'],
                trade['quantity'],
                time.hour,
                time.weekday(),
            ]
            features.append(feature)
            
            # 레이블: 수익률 (양수면 1, 음수면 0)
            label = 1 if trade.get('profit', 0) > 0 else 0
            labels.append(label)
        
        self.features = np.array(features)
        self.labels = np.array(labels)
        
        logger.info(f"🧠 학습 데이터 준비: {len(self.features)}개 샘플")
        return self.features, self.labels
    
    def get_best_trading_times(self) -> Dict:
        """최적 거래 시간대 분석"""
        if not self.trades:
            self.load_trades()
        
        df = pd.DataFrame(self.trades)
        sells = df[df['action'] == 'SELL'].copy()
        
        if sells.empty:
            return {}
        
        sells['time'] = pd.to_datetime(sells['time'])
        sells['hour'] = sells['time'].dt.hour
        sells['weekday'] = sells['time'].dt.weekday
        
        # 시간대별 평균 수익률
        hourly_profit = sells.groupby('hour')['profit_rate'].mean().to_dict()
        
        # 요일별 평균 수익률
        daily_profit = sells.groupby('weekday')['profit_rate'].mean().to_dict()
        
        best_hour = max(hourly_profit, key=hourly_profit.get) if hourly_profit else None
        best_day = max(daily_profit, key=daily_profit.get) if daily_profit else None
        
        result = {
            "best_hour": best_hour,
            "best_day": best_day,
            "hourly_profit": hourly_profit,
            "daily_profit": daily_profit,
        }
        
        logger.info(f"⏰ 최적 거래 시간: {best_hour}시")
        logger.info(f"📅 최적 거래 요일: {['월','화','수','목','금','토','일'][best_day] if best_day is not None else 'N/A'}")
        
        return result


# ================================================================================
# 🧠 딥러닝 모델 (LSTM)
# ================================================================================

if HAS_TORCH:
    class TradingLSTM(nn.Module):
        """거래 예측 LSTM 모델"""
        
        def __init__(self, input_size=4, hidden_size=64, num_layers=2, output_size=2):
            super(TradingLSTM, self).__init__()
            
            self.hidden_size = hidden_size
            self.num_layers = num_layers
            
            self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
            self.fc = nn.Linear(hidden_size, output_size)
            self.softmax = nn.Softmax(dim=1)
        
        def forward(self, x):
            # LSTM
            h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size)
            c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size)
            
            out, _ = self.lstm(x, (h0, c0))
            out = self.fc(out[:, -1, :])
            out = self.softmax(out)
            
            return out


# ================================================================================
# 🎓 트레이너
# ================================================================================

class TradingTrainer:
    """딥러닝 모델 학습"""
    
    def __init__(self):
        self.analyzer = TradeAnalyzer()
        self.model = None
        
        if HAS_TORCH:
            self.model = TradingLSTM()
            logger.info("🧠 LSTM 모델 초기화 완료")
    
    def train(self, epochs: int = 100):
        """모델 학습"""
        if not HAS_TORCH:
            logger.warning("PyTorch 미설치. 학습 불가")
            return
        
        # 데이터 준비
        features, labels = self.analyzer.prepare_training_data()
        
        if len(features) == 0:
            logger.warning("학습 데이터 없음")
            return
        
        # 텐서 변환
        X = torch.FloatTensor(features).unsqueeze(1)  # (batch, seq_len, features)
        y = torch.LongTensor(labels)
        
        # 학습 설정
        criterion = nn.CrossEntropyLoss()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
        
        # 학습
        logger.info(f"🎓 학습 시작 ({epochs} epochs)...")
        
        for epoch in range(epochs):
            self.model.train()
            
            # Forward
            outputs = self.model(X)
            loss = criterion(outputs, y)
            
            # Backward
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            if (epoch + 1) % 20 == 0:
                logger.info(f"Epoch [{epoch+1}/{epochs}], Loss: {loss.item():.4f}")
        
        logger.info("✅ 학습 완료!")
        
        # 정확도 평가
        self.model.eval()
        with torch.no_grad():
            outputs = self.model(X)
            _, predicted = torch.max(outputs.data, 1)
            accuracy = (predicted == y).sum().item() / len(y) * 100
            logger.info(f"📊 정확도: {accuracy:.2f}%")
    
    def predict(self, features: List[float]) -> int:
        """예측"""
        if not HAS_TORCH or self.model is None:
            return 0
        
        self.model.eval()
        with torch.no_grad():
            X = torch.FloatTensor([features]).unsqueeze(1)
            output = self.model(X)
            _, predicted = torch.max(output.data, 1)
            return predicted.item()
    
    def save_model(self, path: str = None):
        """모델 저장"""
        if not HAS_TORCH or self.model is None:
            return
        
        if path is None:
            path = os.path.join(current_dir, "data", "trading_model.pth")
        
        torch.save(self.model.state_dict(), path)
        logger.info(f"💾 모델 저장: {path}")
    
    def load_model(self, path: str = None):
        """모델 로드"""
        if not HAS_TORCH:
            return
        
        if path is None:
            path = os.path.join(current_dir, "data", "trading_model.pth")
        
        if not os.path.exists(path):
            logger.warning("저장된 모델 없음")
            return
        
        self.model = TradingLSTM()
        self.model.load_state_dict(torch.load(path))
        self.model.eval()
        logger.info(f"📂 모델 로드: {path}")


# ================================================================================
# 🎬 메인
# ================================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("🧠 ISATS 딥러닝 트레이딩 학습 시스템")
    print("=" * 70)
    
    # 분석기
    analyzer = TradeAnalyzer()
    analyzer.load_trades()
    analyzer.analyze_performance()
    analyzer.get_best_trading_times()
    
    # 트레이너
    if HAS_TORCH:
        print("\n🎓 딥러닝 모델 학습 시작...")
        trainer = TradingTrainer()
        trainer.train(epochs=100)
        trainer.save_model()
    else:
        print("\n⚠️ PyTorch 미설치. 딥러닝 기능을 사용하려면:")
        print("   pip install torch")
    
    print("\n✅ 완료!")
