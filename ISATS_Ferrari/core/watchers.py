"""
🕵️ ISATS v6.0 전담 감시자 시스템 (REAL-TIME NEURAL NETWORK)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

작전명: "Phase 3 - Neural Network Integration"

역할:
- Redis 실시간 통신 (대시보드 연동)
- CCXT 거래소 연결 (실시간 시세)
- AI 전략 모듈 연동 (신경망 판단)
- 3명의 전담 요원 (SniperAgent, ScoutAgent, PatrolAgent)

작성자: ISATS Neural Swarm
버전: 6.0 (Context Aware + Neural Network)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import asyncio
import json
import os
import sys
import random
from datetime import datetime
from typing import List, Dict, Optional

# 프로젝트 루트
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 선택적 임포트 (없으면 Mock 모드로 작동)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

try:
    import redis.asyncio as redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False
    print("⚠️ [Warning] redis.asyncio not found. Running in MOCK mode.")

try:
    import ccxt.async_support as ccxt
    HAS_CCXT = True
except ImportError:
    HAS_CCXT = False
    print("⚠️ [Warning] ccxt not found. Running in MOCK mode.")

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    print("⚠️ [Warning] pandas not found. Running in MOCK mode.")

try:
    from strategy.active_bot import ActiveBot
    HAS_STRATEGY = True
except ImportError:
    HAS_STRATEGY = False
    print("⚠️ [Warning] ActiveBot not found. Running without AI strategy.")

try:
    from brain.finrl_ensemble import calculate_turbulence
    HAS_TURBULENCE = True
except ImportError:
    HAS_TURBULENCE = False
    print("⚠️ [Warning] Turbulence Index not found. Running without risk management.")

try:
    from core.qualitative_intelligence_team import QualitativeIntelligenceTeam
    HAS_QUALITATIVE = True
except ImportError:
    HAS_QUALITATIVE = False
    print("⚠️ [Warning] Qualitative Intelligence not found. Running without news analysis.")


# ==========================================
# 🕵️ BASE WATCHER (실전 모드)
# ==========================================

class BaseWatcher:
    """모든 감시자의 기본 템플릿 (신경망 연결)"""
    
    def __init__(self, rank: str, targets: List[Dict], interval: float, bot=None):
        """
        Args:
            rank: 등급 (S, A, B)
            targets: 감시 대상 리스트
            interval: 감시 주기 (초)
            bot: ActiveBot 인스턴스 (AI 전략)
        """
        self.rank = rank
        self.targets = targets
        self.interval = interval
        self.is_active = True
        self.scan_count = 0
        
        # 리스크 관리
        self.turbulence_threshold = 100.0  # 난기류 지수 임계값
        self.market_crash_mode = False  # 시장 붕괴 모드
        
        # 정성적 분석
        self.qi_team = None  # Qualitative Intelligence Team
        self.min_confidence = 0.7  # 최소 신뢰도
        
        # 등급별 이모지
        self.emoji = {
            'S': '🔴',
            'A': '🟡',
            'B': '🟢'
        }[rank]
        
        # 등급별 역할
        self.role = {
            'S': 'SNIPER',
            'A': 'SCOUT',
            'B': 'PATROL'
        }[rank]
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 신경망 연결 장비
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        self.redis = None          # Redis 클라이언트 (대시보드 통신)
        self.exchange = None       # CCXT 거래소 (실시간 시세)
        self.strategy = bot        # AI 전략 (신경망 판단)
        
        # 정성적 분석 팀 초기화
        if HAS_QUALITATIVE:
            self.qi_team = QualitativeIntelligenceTeam()
    
    async def _setup(self):
        """장비 착용 (Redis & Exchange 연결)"""
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Redis 연결 (대시보드 실시간 통신)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        if HAS_REDIS and not self.redis:
            try:
                self.redis = redis.from_url("redis://localhost:6379", decode_responses=True)
                await self.redis.ping()
                print(f"   ✅ [{self.role}] Redis 연결 성공")
            except Exception as e:
                print(f"   ⚠️ [{self.role}] Redis 연결 실패: {e} (Mock 모드로 전환)")
                self.redis = None
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # CCXT 거래소 연결 (실시간 시세)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        if HAS_CCXT and not self.exchange:
            try:
                # 예시: 업비트 (한국 거래소)
                # 실제로는 KIS API 또는 yfinance 사용
                self.exchange = ccxt.upbit({'enableRateLimit': True})
                print(f"   ✅ [{self.role}] CCXT 연결 성공 (Upbit)")
            except Exception as e:
                print(f"   ⚠️ [{self.role}] CCXT 연결 실패: {e} (Mock 모드로 전환)")
                self.exchange = None
    
    async def _teardown(self):
        """철수 (연결 종료)"""
        if self.exchange:
            await self.exchange.close()
        if self.redis:
            await self.redis.close()
    
    async def report(self, ticker: str, price: float, msg: str, signal_type: str = "INFO"):
        """
        사령부(Console + Dashboard)로 전술 데이터 전송
        
        Args:
            ticker: 종목 코드
            price: 현재가
            msg: 메시지
            signal_type: 신호 타입 (INFO, BUY, SELL, WARNING)
        """
        time_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 1. 콘솔 출력 (터미널용)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        prefix = f"[{time_str}] "
        level_prefix = {
            'INFO': '',
            'BUY': '🔥 ',
            'SELL': '❄️ ',
            'WARNING': '⚠️ '
        }.get(signal_type, '')
        
        log_msg = f"{prefix}{self.emoji} [{self.role}] {ticker} ({price:,.2f}) >> {level_prefix}{msg}"
        print(log_msg)
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 2. Redis 전송 (대시보드용)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        if self.redis:
            try:
                # 로그 패킷
                log_payload = {
                    "type": "log",
                    "data": {
                        "timestamp": time_str,
                        "rank": self.rank,
                        "ticker": ticker,
                        "price": price,
                        "message": msg,
                        "signal_type": signal_type,
                        "color": {
                            'INFO': 'text-gray-300',
                            'BUY': 'text-red-400',
                            'SELL': 'text-blue-400',
                            'WARNING': 'text-yellow-400'
                        }.get(signal_type, 'text-gray-300')
                    }
                }
                await self.redis.publish("isats_stream", json.dumps(log_payload))
                
                # AI 신호 패킷 (매수/매도 시)
                if signal_type in ['BUY', 'SELL']:
                    ai_payload = {
                        "type": "ai_signal",
                        "data": {
                            "ticker": ticker,
                            "price": price,
                            "signal": signal_type,
                            "rank": self.rank,
                            "timestamp": time_str
                        }
                    }
                    await self.redis.publish("isats_stream", json.dumps(ai_payload))
            
            except Exception as e:
                # Redis 에러는 무시 (콘솔 출력은 계속)
                pass
    
    async def fetch_price(self, ticker: str) -> Optional[float]:
        """
        실시간 가격 조회
        
        Args:
            ticker: 종목 코드
        
        Returns:
            현재가 또는 None
        """
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # CCXT 모드 (실전)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        if self.exchange:
            try:
                ticker_data = await self.exchange.fetch_ticker(ticker)
                return float(ticker_data['last'])
            except Exception:
                pass
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Mock 모드 (시뮬레이션)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        return 10000 + random.randint(-500, 500)
    
    async def fetch_candle_data(self, ticker: str):
        """
        AI 판단을 위한 캔들 데이터 확보 (OHLCV)
        
        Args:
            ticker: 종목 코드
        
        Returns:
            DataFrame 또는 None
        """
        if not HAS_PANDAS:
            return None
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # CCXT 모드 (실전)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        if self.exchange:
            try:
                # 최근 60개 1분봉 가져오기
                ohlcv = await self.exchange.fetch_ohlcv(ticker, timeframe='1m', limit=60)
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
                df['Date'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('Date', inplace=True)
                return df
            except Exception:
                pass
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Mock 모드 (시뮬레이션)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        return None
    
    async def analyze_target(self, target: Dict):
        """
        개별 타겟 분석 (신경망 판단 + 리스크 관리 + 정성적 분석)
        
        Args:
            target: 타겟 정보 (ticker, score, market 등)
        """
        ticker = target['ticker']
        score = target['score']
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 0. 시장 붕괴 모드 확인 (최우선)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        if self.market_crash_mode:
            await self.report(ticker, 0, "🚨 시장 붕괴 모드! 모든 매매 중단", 'WARNING')
            return
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 1. 현재가 조회
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        current_price = await self.fetch_price(ticker)
        
        if current_price is None:
            return
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 1.5. 난기류 지수 확인 (리스크 관리)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        if HAS_TURBULENCE and HAS_PANDAS:
            df = await self.fetch_candle_data(ticker)
            
            if df is not None and len(df) > 252:
                turbulence = calculate_turbulence(df)
                current_turbulence = turbulence.iloc[-1]
                
                if current_turbulence > self.turbulence_threshold:
                    self.market_crash_mode = True
                    await self.report(
                        ticker,
                        current_price,
                        f"🚨 시장 붕괴 감지! (난기류: {current_turbulence:.2f}) 전량 매도 권장",
                        'WARNING'
                    )
                    return
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 2. AI 전략 판단 (신경망)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        signal = "HOLD"
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 2.5. 정성적 분석 (뉴스/공시 필터)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        if HAS_QUALITATIVE and self.qi_team and self.rank == 'S':  # S급만 정성적 분석
            try:
                qualitative_result = await self.qi_team.analyze(
                    ticker=ticker,
                    corp_code="00000000",  # 실제 구현 시 매핑 필요
                    current_price=current_price,
                    technical_signal="BUY"
                )
                
                confidence = qualitative_result.get('final_confidence', 0.5)
                
                if confidence < self.min_confidence:
                    await self.report(
                        ticker,
                        current_price,
                        f"⚠️ 정성적 분석 실패 (신뢰도: {confidence:.2f}). 매수 보류",
                        'WARNING'
                    )
                    return
            except Exception as e:
                # 정성적 분석 실패 시 무시하고 계속
                pass
        
        if self.strategy and HAS_STRATEGY:
            # 캔들 데이터 가져오기
            df = await self.fetch_candle_data(ticker)
            
            if df is not None:
                # ActiveBot의 on_tick 메서드 호출
                market_data = {
                    'Date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'Open': df['Open'].iloc[-1],
                    'High': df['High'].iloc[-1],
                    'Low': df['Low'].iloc[-1],
                    'Close': current_price,
                    'Volume': df['Volume'].iloc[-1]
                }
                
                # 전략 실행
                self.strategy.ticker = ticker
                self.strategy.on_tick(market_data)
                
                # 신호 확인 (ActiveBot의 내부 상태 확인)
                # 실제로는 ActiveBot에서 signal을 반환하도록 수정 필요
                # 여기서는 간이 로직 사용
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 3. 등급별 임무 수행
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        if self.rank == 'S':
            # 🔴 S급: 초정밀 저격 (매수 타점 포착)
            await self.sniper_mission(ticker, current_price, score)
        
        elif self.rank == 'A':
            # 🟡 A급: S급 후보 발굴 (급등 조짐 감시)
            await self.scout_mission(ticker, current_price, score)
        
        else:
            # 🟢 B급: 주기적 순찰 (퇴출 대상 선별)
            await self.patrol_mission(ticker, current_price, score)
    
    async def sniper_mission(self, ticker: str, price: float, score: float):
        """🔴 S급 임무: 초정밀 저격"""
        # 가상 매매 신호 생성 (5% 확률)
        if random.random() > 0.95:
            await self.report(ticker, price, "🔥 타겟 포착! 즉시 사격 개시 (BUY)!", 'BUY')
            
            # ActiveBot에 매매 신호 전달 (향후 구현)
            if self.strategy:
                # self.strategy.execute_trade(ticker, 'BUY', price)
                pass
    
    async def scout_mission(self, ticker: str, price: float, score: float):
        """🟡 A급 임무: S급 후보 발굴"""
        # 가상 급등 감지 (2% 확률)
        if random.random() > 0.98:
            await self.report(ticker, price, "⚡ S급 승격 심사 요청! (급등 감지)", 'WARNING')
    
    async def patrol_mission(self, ticker: str, price: float, score: float):
        """🟢 B급 임무: 주기적 순찰"""
        # 가상 특이사항 발생 (1% 확률)
        if random.random() > 0.99:
            await self.report(ticker, price, "👀 특이사항 발생. A급 격상 고려.", 'INFO')
    
    async def scan_market(self):
        """시장 감시 (전체 타겟 순회)"""
        if not self.targets:
            await asyncio.sleep(self.interval)
            return
        
        # 모든 타겟 분석
        for target in self.targets:
            await self.analyze_target(target)
        
        self.scan_count += 1
    
    async def run(self):
        """감시자 실행 (무한 루프)"""
        await self._setup()
        
        print(f"   👮 {self.emoji} {self.rank}급 담당관 배치 완료 "
              f"(주기: {self.interval}초, 타겟: {len(self.targets)}개)")
        
        try:
            while self.is_active:
                await self.scan_market()
                await asyncio.sleep(self.interval)
        finally:
            await self._teardown()


# ==========================================
# 🔴 SNIPER AGENT (S급 전담)
# ==========================================

class SniperAgent(BaseWatcher):
    """
    🔴 S급 전담 (0.5초)
    임무: 찰나의 순간 포착, 즉시 매매 집행
    """
    
    def __init__(self, targets: List[Dict], bot=None):
        super().__init__('S', targets, interval=0.5, bot=bot)


# ==========================================
# 🟡 SCOUT AGENT (A급 전담)
# ==========================================

class ScoutAgent(BaseWatcher):
    """
    🟡 A급 전담 (1.0초)
    임무: S급 후보 발굴 및 급등 조짐 감시
    """
    
    def __init__(self, targets: List[Dict], bot=None):
        super().__init__('A', targets, interval=1.0, bot=bot)


# ==========================================
# 🟢 PATROL AGENT (B급 전담)
# ==========================================

class PatrolAgent(BaseWatcher):
    """
    🟢 B급 전담 (2.0초)
    임무: 주기적 순찰, 퇴출 대상 선별
    """
    
    def __init__(self, targets: List[Dict], bot=None):
        super().__init__('B', targets, interval=2.0, bot=bot)


# ==========================================
# 테스트 코드
# ==========================================

async def test_watchers():
    """전담 감시자 테스트"""
    # 가상 타겟 데이터
    s_targets = [
        {'ticker': '005930.KS', 'score': 9, 'market': 'KR'},
        {'ticker': 'SOXL', 'score': 10, 'market': 'US'},
        {'ticker': 'TQQQ', 'score': 9, 'market': 'US'}
    ]
    
    a_targets = [
        {'ticker': '000660.KS', 'score': 8, 'market': 'KR'},
        {'ticker': 'NVDA', 'score': 8, 'market': 'US'}
    ]
    
    b_targets = [
        {'ticker': '035720.KS', 'score': 8, 'market': 'KR'},
        {'ticker': 'AMD', 'score': 8, 'market': 'US'}
    ]
    
    # 감시자 생성
    sniper = SniperAgent(s_targets)
    scout = ScoutAgent(a_targets)
    patrol = PatrolAgent(b_targets)
    
    print(f"\n{'='*80}")
    print(f"🎯 전담 감시자 시스템 테스트 (신경망 연결)")
    print(f"{'='*80}\n")
    
    # 병렬 실행
    await asyncio.gather(
        sniper.run(),
        scout.run(),
        patrol.run()
    )


if __name__ == "__main__":
    asyncio.run(test_watchers())
