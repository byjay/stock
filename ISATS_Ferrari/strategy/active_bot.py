import pandas as pd
import numpy as np
import sys
import os

# 프로젝트 루트 경로 추가 (필요시)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from core.signal_validator import SignalValidator
from core.risk_manager import RiskManager

# ==========================================
# Active Trading Bot
# 역할: 지표 분석 및 매매 신호 생성 (Strategy Pattern)
# ==========================================

class ActiveBot:
    def __init__(self):
        self.name = "Standard Strategy Bot"
        self.validator = SignalValidator()
        self.risk_manager = RiskManager()
        
        # 전략 파라미터 (표준값)
        self.params = {
            'ma_short': 5,
            'ma_long': 20,
            'rsi_period': 14,
            'rsi_buy': 30,
            'rsi_sell': 70,
            'tp_rate': 0.05,
            'sl_rate': 0.02
        }

    def calculate_indicators(self, df):
        """보조 지표(MA, RSI) 산출"""
        df = df.copy()
        # Moving Average
        df['MA_S'] = df['Close'].rolling(self.params['ma_short']).mean()
        df['MA_L'] = df['Close'].rolling(self.params['ma_long']).mean()
        
        # Relative Strength Index (RSI)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(self.params['rsi_period']).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(self.params['rsi_period']).mean()
        rs = gain / (loss + 1e-8)
        df['RSI'] = 100 - (100 / (1 + rs))
        
        return df

    async def analyze(self, ticker, raw_df):
        """
        대상 종목에 대한 매매 신호 분석 실행
        Return: (Signal, Message, TargetProfitPercentage)
        """
        # 1. 시장 전체 리스크 판단
        status, msg = self.risk_manager.analyze_market_status()
        if status == "CRASH":
            return "HOLD", f"시장 리스크 감지: {msg}", 0

        if len(raw_df) < self.params['ma_long'] + 5:
            return "HOLD", "데이터 샘플 부족", 0

        # 2. 기술적 지표 계산
        df = self.calculate_indicators(raw_df)
        curr = df.iloc[-1]
        prev = df.iloc[-2]

        # 3. 매입 신호 알고리즘: (Golden Cross) 혹은 (RSI 과매도 구간 탈출)
        signal_gc = (curr['MA_S'] > curr['MA_L']) and (prev['MA_S'] <= prev['MA_L'])
        signal_rsi_buy = (prev['RSI'] < self.params['rsi_buy']) and (curr['RSI'] > self.params['rsi_buy'])
        
        if signal_gc or signal_rsi_buy:
            # 4. 신호 검증기 필터링 시행
            is_valid, reason = self.validator.validate_entry(ticker, curr, df)
            
            if is_valid:
                return "BUY", "모든 매수 조건 충족", self.params['tp_rate']
            else:
                return "HOLD", f"신호 기각: {reason}", 0

        # 5. 매도 신호 판별: (RSI 과열 구간 진입)
        if curr['RSI'] > self.params['rsi_sell']:
            return "SELL", "RSI 지표 과열 상태", 0

        return "HOLD", "신호 없음. 관망 유지", 0
