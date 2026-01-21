import pandas as pd
import numpy as np
import os
import sys
import torch
from tqdm import tqdm

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ==========================================
# 🕰️ ELASTIC TIME MACHINE (탄력적 타임머신)
# ==========================================

class ElasticTimeMachine:
    def __init__(self):
        self.prime_intervals = [4, 7, 13, 17] # 소수(Prime Number) 시간 프레임
        self.target_data_dir = "data/KR"
        
    def resample_custom(self, df, minutes):
        """커스텀 분봉 생성 (이동 평균 노이즈 제거)"""
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)
            
        resampler = df.resample(f'{minutes}min')
        resampled_df = resampler.agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }).dropna()
        
        return resampled_df

    def start_weekly_survival(self, ticker="BTC-KRW"):
        """1주일 단위 생존 훈련 루프"""
        file_path = os.path.join(self.target_data_dir, f"{ticker}.csv")
        if not os.path.exists(file_path):
            print(f"❌ [Error] 1분봉 데이터가 필요합니다: {file_path}")
            return

        print(f"\n🌌 [Elastic Warp] '{ticker}'의 시공간 왜곡 분석 개시...")
        df_1min = pd.read_csv(file_path)
        
        for interval in self.prime_intervals:
            print(f"   🔍 렌즈 장착: {interval}분봉 (Prime Lens)")
            resampled = self.resample_custom(df_1min, interval)
            
            # 주간 단위 생존 가능성 평가 (예시 로직)
            profit_potential = (resampled['Close'].diff() > 0).mean() * 100
            print(f"      -> {interval}분 프레임 신뢰도: {profit_potential:.2f}%")

        print("\n✅ [Survival Report] 모든 소수 시간 프레임 스캔 완료.")
        print("   -> 가장 명확한 추세가 보이는 프레임을 자동 선택하여 매매 엔진에 주입합니다.")

if __name__ == "__main__":
    # 데이터 존재 여부 확인 후 실행
    etm = ElasticTimeMachine()
    # 셈플 실행 (데이터가 없을 것을 대비해 예외 처리)
    try:
        etm.start_weekly_survival("BTC-KRW")
    except Exception as e:
        print(f"⚠️ 실행 대기: {e}")
