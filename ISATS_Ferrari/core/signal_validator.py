import pandas as pd
import numpy as np

# ==========================================
# Signal Validator
# 역할: 기술적 매매 신호의 유효성 검증 (필터링)
# ==========================================

class SignalValidator:
    def __init__(self):
        """검증 임계값 설정"""
        self.min_volume_ratio = 2.0  # 평균 대비 최소 거래량 비율
        self.spread_limit = 0.003    # 허용 최대 호가 스프레드 (0.3%)

    def validate_entry(self, ticker, current_data, history_data, orderbook=None):
        """
        매수 진입 전 최종 검증 수행
        1. 거래량 폭증 여부 확인
        2. 상위 타임프레임(13분) 추세 일치 확인
        3. 호가 스프레드(체결성) 확인
        """
        try:
            # 1. 거래량 검증
            vol_now = current_data['Volume']
            if hasattr(history_data, 'iloc') and len(history_data) >= 20:
                vol_avg = history_data['Volume'].iloc[-20:].mean()
            else:
                vol_avg = vol_now # 데이터 부족 시 현재값 기준

            if vol_now < vol_avg * self.min_volume_ratio:
                return False, f"거래량 부족 ({vol_now / (vol_avg + 1e-8):.1f}배)"

            # 2. 상위 프레임(13분봉) 추세 확인
            if hasattr(history_data, 'resample') and len(history_data) > 60:
                df_13m = history_data.resample('13T').agg({'Close': 'last'}).dropna()
                if len(df_13m) >= 5:
                    ma5 = df_13m['Close'].rolling(5).mean().iloc[-1]
                    current_price = current_data['Close']
                    
                    if current_price < ma5:
                        return False, "상위(13분) 추세 하향 중"

            # 3. 호가 스프레드 검증
            if orderbook and 'bids' in orderbook and 'asks' in orderbook:
                best_bid = orderbook['bids'][0]['price']
                best_ask = orderbook['asks'][0]['price']
                spread = (best_ask - best_bid) / (best_bid + 1e-8)
                
                if spread > self.spread_limit:
                    return False, f"스프레드 과다 ({spread*100:.2f}%)"

            return True, "모든 검증 로직 통과"

        except Exception as e:
            return False, f"검증 프로세스 오류: {e}"
