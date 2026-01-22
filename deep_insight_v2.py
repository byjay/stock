import pandas as pd
import numpy as np
import os
import warnings
from typing import Dict, List, Tuple, Optional
from scipy.stats import pearsonr
from datetime import datetime, timedelta

warnings.filterwarnings('ignore')

try:
    import FinanceDataReader as fdr
except ImportError:
    print("⚠️ FinanceDataReader 설치 필요: pip install finance-datareader")
    fdr = None

# ==========================================
# 🕵️ DEEP INSIGHT SCANNER v2.0
# Pattern + Technical + Volume = Prediction
# ==========================================

class PatternMatcher:
    """간단한 패턴 매칭 엔진 (내장)"""
    
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.db_cache = []
        
    def load_database(self):
        """로컬 DB 로드"""
        print("📚 [PatternDB] 역사적 데이터 로딩...")
        # 실제 구현 시 CSV 파일들 로드
        # 여기서는 간단히 패스
        pass
    
    def normalize(self, series: np.ndarray) -> np.ndarray:
        """Z-Score 정규화"""
        return (series - np.mean(series)) / (np.std(series) + 1e-8)
    
    def find_similar_patterns(self, target_close: np.ndarray, 
                            window=60, top_k=5) -> List[Dict]:
        """
        유사 패턴 검색
        
        실제 구현에서는 DB에서 검색하지만,
        여기서는 간단한 시뮬레이션 결과 반환
        """
        # 실전에서는 여기에 Time Crystal의 로직 적용
        # 지금은 더미 데이터 반환
        return []


class TechnicalAnalyzer:
    """기술적 지표 계산 엔진"""
    
    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period=14) -> float:
        """RSI 계산"""
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1]
    
    @staticmethod
    def calculate_macd(df: pd.DataFrame) -> Tuple[float, float, float]:
        """MACD 계산"""
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        hist = macd - signal
        return macd.iloc[-1], signal.iloc[-1], hist.iloc[-1]
    
    @staticmethod
    def calculate_bollinger_bands(df: pd.DataFrame, period=20) -> Tuple[float, float, float]:
        """볼린저 밴드 계산"""
        sma = df['Close'].rolling(period).mean()
        std = df['Close'].rolling(period).std()
        upper = sma + (std * 2)
        lower = sma - (std * 2)
        return upper.iloc[-1], sma.iloc[-1], lower.iloc[-1]
    
    @staticmethod
    def detect_trend(df: pd.DataFrame) -> Dict:
        """추세 분석"""
        ma20 = df['Close'].rolling(20).mean().iloc[-1]
        ma60 = df['Close'].rolling(60).mean().iloc[-1]
        ma120 = df['Close'].rolling(120).mean().iloc[-1] if len(df) >= 120 else None
        
        current_price = df['Close'].iloc[-1]
        
        # 정배열 체크
        if ma120:
            is_aligned = current_price > ma20 > ma60 > ma120
        else:
            is_aligned = current_price > ma20 > ma60
        
        # 추세 강도
        if is_aligned:
            trend = "강한 상승"
        elif current_price > ma20 > ma60:
            trend = "상승"
        elif current_price < ma20 < ma60:
            trend = "하락"
        else:
            trend = "횡보"
        
        return {
            'trend': trend,
            'is_aligned': is_aligned,
            'ma20': ma20,
            'ma60': ma60,
            'current': current_price,
            'distance_from_ma20': (current_price - ma20) / ma20 * 100
        }


class VolumeAnalyzer:
    """거래량 & 체결 분석 엔진"""
    
    @staticmethod
    def analyze_volume_profile(df: pd.DataFrame, period=20) -> Dict:
        """거래량 프로파일 분석"""
        recent = df.tail(period)
        avg_volume = df['Volume'].mean()
        recent_avg = recent['Volume'].mean()
        
        # 거래량 비율
        volume_ratio = recent_avg / avg_volume
        
        # 상승봉 vs 하락봉 거래량
        up_candles = recent[recent['Close'] >= recent['Open']]
        down_candles = recent[recent['Close'] < recent['Open']]
        
        buy_volume = up_candles['Volume'].sum()
        sell_volume = down_candles['Volume'].sum()
        
        # 체결강도 (일봉 기준 근사치)
        if sell_volume > 0:
            strength_ratio = buy_volume / sell_volume
        else:
            strength_ratio = 5.0  # 매도 거의 없음
        
        return {
            'volume_ratio': volume_ratio,
            'strength_ratio': strength_ratio,
            'buy_volume': buy_volume,
            'sell_volume': sell_volume,
            'avg_volume': avg_volume,
            'recent_avg_volume': recent_avg
        }
    
    @staticmethod
    def detect_accumulation(df: pd.DataFrame) -> Dict:
        """매집/분산 패턴 탐지"""
        recent = df.tail(10)
        
        # 1. 긴 아래꼬리 양봉 (하락 매수)
        lower_shadow = recent.apply(
            lambda x: (min(x['Open'], x['Close']) - x['Low']) / 
                     (x['High'] - x['Low'] + 1e-8), axis=1
        )
        
        # 2. 대량 거래
        volume_surge = recent['Volume'] > df['Volume'].mean() * 1.5
        
        # 3. 가격 상승
        price_up = recent['Close'] > recent['Open']
        
        # 매집봉 점수
        accumulation_score = (
            (lower_shadow > 0.5).sum() +
            volume_surge.sum() +
            price_up.sum()
        ) / 3
        
        # 분산봉 체크 (윗꼬리 긴 음봉 + 대량)
        upper_shadow = recent.apply(
            lambda x: (x['High'] - max(x['Open'], x['Close'])) / 
                     (x['High'] - x['Low'] + 1e-8), axis=1
        )
        
        distribution_score = (
            (upper_shadow > 0.5).sum() +
            volume_surge.sum() +
            (~price_up).sum()
        ) / 3
        
        return {
            'accumulation_score': accumulation_score,
            'distribution_score': distribution_score,
            'signal': 'BUY' if accumulation_score > distribution_score else 'SELL'
        }


class DeepInsightV2:
    """통합 분석 엔진"""
    
    def __init__(self):
        print("🧠 [DeepInsight v2] 초기화 중...")
        self.pattern_matcher = PatternMatcher()
        self.tech_analyzer = TechnicalAnalyzer()
        self.vol_analyzer = VolumeAnalyzer()
        
        if fdr:
            print("   ✅ FinanceDataReader 준비 완료")
        else:
            print("   ⚠️ FinanceDataReader 미설치 (데이터 조회 제한)")
    
    def get_live_data(self, ticker: str, days=365) -> Optional[pd.DataFrame]:
        """실시간 데이터 조회"""
        if not fdr:
            print("❌ FinanceDataReader가 설치되지 않았습니다.")
            return None
        
        try:
            # 티커 정리
            ticker = ticker.upper().strip()
            
            # 종료일 = 오늘, 시작일 = days일 전
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            print(f"   📡 데이터 조회 중: {ticker} ({start_date.date()} ~ {end_date.date()})")
            df = fdr.DataReader(ticker, start=start_date, end=end_date)
            
            if df is None or len(df) == 0:
                print(f"   ⚠️ 데이터 없음: {ticker}")
                return None
            
            # 필수 컬럼 확인
            required = ['Open', 'High', 'Low', 'Close', 'Volume']
            if not all(col in df.columns for col in required):
                print(f"   ⚠️ 필수 컬럼 누락")
                return None
            
            return df.reset_index()
            
        except Exception as e:
            print(f"   ❌ 조회 실패: {e}")
            return None
    
    def calculate_score(self, analysis: Dict) -> Tuple[int, str]:
        """
        종합 점수 계산
        
        점수 체계 (0~10점):
        - 기술적 지표: 4점
        - 거래량: 3점
        - 패턴: 3점
        """
        score = 0
        reasons = []
        
        # 1. 기술적 지표 (4점)
        tech = analysis['technical']
        
        # RSI (과매도/과매수)
        if 30 < tech['rsi'] < 70:
            score += 1
            reasons.append("RSI 정상권")
        elif tech['rsi'] < 30:
            score += 2
            reasons.append("RSI 과매도 (반등 가능)")
        
        # 추세
        if tech['trend']['is_aligned']:
            score += 2
            reasons.append("정배열 (강한 추세)")
        elif tech['trend']['trend'] == "상승":
            score += 1
            reasons.append("상승 추세")
        
        # MACD
        if tech['macd']['hist'] > 0:
            score += 1
            reasons.append("MACD 골든크로스")
        
        # 2. 거래량 (3점)
        vol = analysis['volume']
        
        if vol['strength_ratio'] > 1.5:
            score += 2
            reasons.append("강한 매수세")
        elif vol['strength_ratio'] > 1.0:
            score += 1
            reasons.append("매수 우위")
        
        if vol['volume_ratio'] > 1.5:
            score += 1
            reasons.append("거래량 급증")
        
        # 매집/분산
        if vol['accumulation']['signal'] == 'BUY':
            score += 1
            reasons.append("매집 신호")
        
        # 3. 패턴 매칭 (3점) - 실제 구현 시
        # if analysis['pattern']['win_rate'] > 70:
        #     score += 3
        
        return min(score, 10), reasons
    
    def scan(self, ticker: str) -> Optional[Dict]:
        """
        종목 정밀 스캔
        
        Returns:
            분석 결과 딕셔너리 또는 None (실패 시)
        """
        print(f"\n{'='*60}")
        print(f"🔬 [DEEP SCAN] {ticker}")
        print(f"{'='*60}")
        
        # 1. 데이터 로드
        df = self.get_live_data(ticker)
        if df is None or len(df) < 60:
            print("❌ 데이터 부족 (최소 60일 필요)")
            return None
        
        current_price = df['Close'].iloc[-1]
        prev_close = df['Close'].iloc[-2]
        change_pct = (current_price - prev_close) / prev_close * 100
        
        print(f"\n💰 현재가: {current_price:,.2f} ({change_pct:+.2f}%)")
        print(f"📅 데이터: {len(df)}일 ({df.iloc[0]['Date']} ~ {df.iloc[-1]['Date']})")
        
        # 2. 기술적 분석
        print(f"\n{'─'*60}")
        print("📊 [기술적 분석]")
        print(f"{'─'*60}")
        
        rsi = self.tech_analyzer.calculate_rsi(df)
        macd, signal, hist = self.tech_analyzer.calculate_macd(df)
        upper, middle, lower = self.tech_analyzer.calculate_bollinger_bands(df)
        trend_info = self.tech_analyzer.detect_trend(df)
        
        print(f"   🎯 RSI(14): {rsi:.1f}", end=" ")
        if rsi < 30:
            print("(과매도 ⚠️)")
        elif rsi > 70:
            print("(과매수 🔥)")
        else:
            print("(정상권)")
        
        print(f"   📈 MACD: {macd:.2f} / Signal: {signal:.2f} / Hist: {hist:.2f}")
        if hist > 0:
            print("      → 골든크로스 ✅")
        else:
            print("      → 데드크로스 ⚠️")
        
        print(f"   📉 볼린저밴드:")
        print(f"      Upper: {upper:,.2f}")
        print(f"      Middle: {middle:,.2f}")
        print(f"      Lower: {lower:,.2f}")
        
        bb_position = (current_price - lower) / (upper - lower) * 100
        print(f"      현재 위치: {bb_position:.1f}% ", end="")
        if bb_position < 20:
            print("(하단 근접 - 반등 가능)")
        elif bb_position > 80:
            print("(상단 근접 - 조정 가능)")
        else:
            print()
        
        print(f"\n   🌊 추세: {trend_info['trend']}")
        print(f"      MA20 대비: {trend_info['distance_from_ma20']:+.2f}%")
        
        # 3. 거래량 분석
        print(f"\n{'─'*60}")
        print("📦 [거래량 분석]")
        print(f"{'─'*60}")
        
        vol_profile = self.vol_analyzer.analyze_volume_profile(df)
        accumulation = self.vol_analyzer.detect_accumulation(df)
        
        print(f"   📊 거래량 비율: {vol_profile['volume_ratio']:.2f}x ", end="")
        if vol_profile['volume_ratio'] > 2:
            print("(폭발적 증가 🔥)")
        elif vol_profile['volume_ratio'] > 1.5:
            print("(급증)")
        else:
            print()
        
        print(f"   ⚡ 체결강도: {vol_profile['strength_ratio']:.2f} ", end="")
        if vol_profile['strength_ratio'] > 1.5:
            print("(강한 매수세 💪)")
        elif vol_profile['strength_ratio'] > 1.0:
            print("(매수 우위)")
        else:
            print("(매도 우위 ⚠️)")
        
        print(f"\n   🎣 세력 동향:")
        print(f"      매집 점수: {accumulation['accumulation_score']:.2f}")
        print(f"      분산 점수: {accumulation['distribution_score']:.2f}")
        print(f"      → {accumulation['signal']} 신호")
        
        # 4. 종합 점수
        analysis = {
            'ticker': ticker,
            'current_price': current_price,
            'change_pct': change_pct,
            'technical': {
                'rsi': rsi,
                'macd': {'macd': macd, 'signal': signal, 'hist': hist},
                'bollinger': {'upper': upper, 'middle': middle, 'lower': lower},
                'trend': trend_info
            },
            'volume': {
                'strength_ratio': vol_profile['strength_ratio'],
                'volume_ratio': vol_profile['volume_ratio'],
                'accumulation': accumulation
            }
        }
        
        score, reasons = self.calculate_score(analysis)
        
        print(f"\n{'='*60}")
        print("🎯 [최종 판단]")
        print(f"{'='*60}")
        print(f"   종합 점수: {score}/10")
        print(f"\n   주요 근거:")
        for i, reason in enumerate(reasons, 1):
            print(f"   {i}. {reason}")
        
        print(f"\n   💡 추천:")
        if score >= 8:
            recommendation = "🚀 STRONG BUY - 강력 매수 구간"
        elif score >= 6:
            recommendation = "✅ BUY - 분할 매수 고려"
        elif score >= 4:
            recommendation = "⏸️ HOLD - 관망"
        else:
            recommendation = "⚠️ SELL - 매도/회피 권장"
        
        print(f"   {recommendation}")
        print(f"\n{'='*60}\n")
        
        # 결과 반환 (ISATS 통합용)
        analysis['score'] = score
        analysis['reasons'] = reasons
        analysis['recommendation'] = recommendation
        
        return analysis


# ==========================================
# 실행부
# ==========================================
def main():
    scanner = DeepInsightV2()
    
    print("\n" + "="*60)
    print("🕵️ Deep Insight Scanner v2.0")
    print("="*60)
    
    # 사용 예시
    examples = [
        "005930.KS  # 삼성전자",
        "AAPL       # 애플",
        "TQQQ       # 테크 3배 레버리지",
        "^KS11      # 코스피 지수",
    ]
    
    print("\n📌 입력 예시:")
    for ex in examples:
        print(f"   {ex}")
    
    while True:
        print("\n" + "-"*60)
        ticker = input("👉 분석할 종목 코드 (종료: q): ").strip()
        
        if ticker.lower() == 'q':
            print("\n👋 종료합니다.")
            break
        
        if not ticker:
            continue
        
        scanner.scan(ticker)


if __name__ == "__main__":
    main()
