import pandas as pd
import numpy as np
import FinanceDataReader as fdr

# ==========================================
# Market Risk Manager
# 역할: 시장 변동성 및 추세를 분석하여 매매 모드 결정 (Turbulence Index 활용)
# ==========================================

class RiskManager:
    def __init__(self, market="KR"):
        """분석 시장 및 임계값 설정"""
        self.index_ticker = "KS11" if market == "KR" else "IXIC" # KOSPI or NASDAQ
        self.vol_threshold = 2.0  # 변동성 임계값 (평균 대비 배수)
        self.trend_window = 60    # 추세 판단 기간 (일)

    def analyze_market_status(self):
        """
        시장 상태 분석
        Return: (Status_Label, Detail_Message)
        상태값: 'NORMAL', 'HIGH_VOLATILITY', 'CRASH', 'BULL_MARKET', 'BEAR_MARKET'
        """
        try:
            # 최근 120일 데이터 조회
            df = fdr.DataReader(self.index_ticker)
            if len(df) < 120:
                return "NORMAL", "데이터 부족"

            current_price = df['Close'].iloc[-1]
            ma60 = df['Close'].rolling(self.trend_window).mean().iloc[-1]
            
            # 최근 변동성과 장기 변동성 비교 (Turbulence Ratio)
            returns = df['Close'].pct_change()
            recent_vol = returns.tail(5).std()
            long_vol = returns.tail(60).std()
            turbulence_ratio = recent_vol / (long_vol + 1e-8)
            
            is_uptrend = current_price > ma60
            
            # 리스크 및 추세 판단 로직
            if turbulence_ratio > self.vol_threshold:
                if not is_uptrend:
                    return "CRASH", f"시장 급락 경보 (변동성 {turbulence_ratio:.1f}배)"
                else:
                    return "HIGH_VOLATILITY", f"변동성 확대 (상승장)"
            
            if is_uptrend:
                return "BULL_MARKET", "안정적 상승세"
            else:
                return "BEAR_MARKET", "약세장 지속"

        except Exception as e:
            return "NORMAL", f"분석 오류: {e}"
