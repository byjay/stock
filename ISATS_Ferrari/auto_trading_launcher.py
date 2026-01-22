# -*- coding: utf-8 -*-
"""
================================================================================
🚀 ISATS 자동매매 실행기 (Auto Trading Launcher)
================================================================================
KIS Open API 완전 통합 버전

실행 모드:
1. VIRTUAL (모의투자) - 기본값, 안전한 테스트
2. REAL (실전투자) - 실제 자금 투입

실행 방법:
    python auto_trading_launcher.py --mode virtual
    python auto_trading_launcher.py --mode real
================================================================================
"""

import os
import sys
import asyncio
import argparse
import logging
from datetime import datetime, time
from typing import Dict, List, Optional

# 프로젝트 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import pandas as pd

# ISATS 모듈 임포트
from core.kis_official_api import KISUnifiedClient
from strategy.active_bot import ActiveBot

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            os.path.join(current_dir, "logs", f"trading_{datetime.now().strftime('%Y%m%d')}.log"),
            encoding="utf-8"
        )
    ]
)
logger = logging.getLogger(__name__)


# ================================================================================
# 📊 시장 상태 체커
# ================================================================================

class MarketStatusChecker:
    """거래 시간 및 시장 상태 확인"""
    
    # 한국 주식 시장 시간 (KST)
    KR_MARKET_OPEN = time(9, 0)
    KR_MARKET_CLOSE = time(15, 30)
    KR_PRE_MARKET = time(8, 30)
    KR_AFTER_MARKET = time(18, 0)
    
    # 미국 주식 시장 시간 (EST -> KST 변환)
    # 서머타임: 22:30 ~ 05:00 (KST)
    # 겨울: 23:30 ~ 06:00 (KST)
    
    @classmethod
    def is_kr_market_open(cls) -> bool:
        """한국 시장 개장 여부"""
        now = datetime.now().time()
        weekday = datetime.now().weekday()
        
        # 주말 제외
        if weekday >= 5:
            return False
        
        return cls.KR_MARKET_OPEN <= now <= cls.KR_MARKET_CLOSE
    
    @classmethod
    def is_us_market_open(cls) -> bool:
        """미국 시장 개장 여부 (대략적)"""
        now = datetime.now()
        hour = now.hour
        weekday = now.weekday()
        
        # 주말 제외
        if weekday >= 5:
            return False
        
        # 서머타임 기준 (22:30 ~ 05:00 KST)
        return (hour >= 22) or (hour < 5)
    
    @classmethod
    def get_tradable_markets(cls) -> List[str]:
        """현재 거래 가능한 시장 목록"""
        markets = []
        
        if cls.is_kr_market_open():
            markets.append("KR")
        
        if cls.is_us_market_open():
            markets.append("US")
        
        return markets


# ================================================================================
# 🎯 타겟 종목 관리자
# ================================================================================

class TargetManager:
    """감시 대상 종목 관리"""
    
    def __init__(self, target_file: str = None):
        self.target_file = target_file or os.path.join(current_dir, "daily_target_list.csv")
        self.targets = {
            "S": [],  # S급 (초정밀 저격)
            "A": [],  # A급 (후보 발굴)
            "B": [],  # B급 (순찰)
        }
    
    def load_targets(self) -> bool:
        """타겟 리스트 로드"""
        try:
            if not os.path.exists(self.target_file):
                logger.warning(f"타겟 파일 없음: {self.target_file}")
                self._set_default_targets()
                return True
            
            df = pd.read_csv(self.target_file)
            
            # 등급별 분배 (상위 3: S, 4~10: A, 11~20: B)
            if "Ticker" in df.columns:
                self.targets["S"] = df.iloc[:3]["Ticker"].tolist()
                self.targets["A"] = df.iloc[3:10]["Ticker"].tolist()
                self.targets["B"] = df.iloc[10:20]["Ticker"].tolist()
            elif "ticker" in df.columns:
                self.targets["S"] = df.iloc[:3]["ticker"].tolist()
                self.targets["A"] = df.iloc[3:10]["ticker"].tolist()
                self.targets["B"] = df.iloc[10:20]["ticker"].tolist()
            else:
                # 첫 번째 컬럼 사용
                col = df.columns[0]
                self.targets["S"] = df.iloc[:3][col].tolist()
                self.targets["A"] = df.iloc[3:10][col].tolist()
                self.targets["B"] = df.iloc[10:20][col].tolist()
            
            total = sum(len(v) for v in self.targets.values())
            logger.info(f"✅ 타겟 로드 완료: 총 {total}종목 (S: {len(self.targets['S'])}, A: {len(self.targets['A'])}, B: {len(self.targets['B'])})")
            return True
            
        except Exception as e:
            logger.error(f"타겟 로드 실패: {e}")
            self._set_default_targets()
            return True
    
    def _set_default_targets(self):
        """기본 관찰 종목 설정"""
        self.targets = {
            "S": ["005930", "000660", "035420"],  # 삼성전자, SK하이닉스, NAVER
            "A": ["035720", "051910", "006400", "068270"],  # 카카오, LG화학, 삼성SDI, 셀트리온
            "B": ["003550", "017670", "105560", "028260"],  # LG, SK텔레콤, KB금융, 삼성물산
        }
        logger.info("📋 기본 타겟 리스트 적용")
    
    def get_all_tickers(self) -> List[str]:
        """모든 감시 종목 반환"""
        return self.targets["S"] + self.targets["A"] + self.targets["B"]


# ================================================================================
# 🤖 자동매매 엔진
# ================================================================================

class AutoTradingEngine:
    """
    ISATS 자동매매 핵심 엔진
    
    기능:
    - 실시간 시세 감시
    - AI 기반 매매 신호 생성
    - 자동 주문 실행
    - 포지션 관리
    - 리스크 관리
    """
    
    def __init__(self, mode: str = "virtual"):
        self.mode = mode
        self.client: Optional[KISUnifiedClient] = None
        self.bot: Optional[ActiveBot] = None
        self.target_manager = TargetManager()
        self.running = False
        
        # 거래 설정
        self.config = {
            "max_position_size": 1000000,  # 종목당 최대 100만원
            "max_positions": 5,  # 최대 동시 보유 종목 수
            "stop_loss_rate": 0.03,  # 손절 -3%
            "take_profit_rate": 0.05,  # 익절 +5%
            "scan_interval": 1.0,  # 스캔 주기 (초)
        }
        
        # 거래 상태
        self.positions = {}  # 현재 보유 포지션
        self.pending_orders = {}  # 미체결 주문
        self.trade_history = []  # 거래 내역
    
    async def initialize(self) -> bool:
        """엔진 초기화"""
        logger.info("=" * 60)
        logger.info(f"🚀 ISATS 자동매매 엔진 초기화 (모드: {self.mode.upper()})")
        logger.info("=" * 60)
        
        try:
            # 1. KIS API 클라이언트 초기화
            self.client = KISUnifiedClient(mode=self.mode)
            if not self.client.initialize():
                logger.error("❌ KIS API 초기화 실패")
                return False
            logger.info("✅ KIS API 클라이언트 초기화 완료")
            
            # 2. 전략 봇 초기화
            self.bot = ActiveBot()
            logger.info("✅ 전략 봇 초기화 완료")
            
            # 3. 타겟 종목 로드
            self.target_manager.load_targets()
            
            # 4. 현재 잔고 확인
            await self._sync_positions()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 초기화 중 오류: {e}")
            return False
    
    async def _sync_positions(self):
        """현재 보유 포지션 동기화"""
        try:
            holdings, summary = self.client.get_balance()
            
            if not holdings.empty:
                for _, row in holdings.iterrows():
                    ticker = row.get("pdno", row.get("PDNO", ""))
                    if ticker:
                        self.positions[ticker] = {
                            "quantity": int(row.get("hldg_qty", row.get("HLDG_QTY", 0))),
                            "avg_price": float(row.get("pchs_avg_pric", row.get("PCHS_AVG_PRIC", 0))),
                            "current_price": float(row.get("prpr", row.get("PRPR", 0))),
                            "profit_rate": float(row.get("evlu_pfls_rt", row.get("EVLU_PFLS_RT", 0))),
                        }
            
            total_value = summary.get("tot_evlu_amt", summary.get("TOT_EVLU_AMT", 0))
            logger.info(f"📊 현재 보유: {len(self.positions)}종목, 평가금액: {total_value:,}원")
            
        except Exception as e:
            logger.warning(f"잔고 동기화 실패: {e}")
    
    async def _analyze_ticker(self, ticker: str, rank: str) -> Dict:
        """개별 종목 분석"""
        try:
            # 1. 현재가 조회
            price_data = self.client.get_price(ticker)
            if not price_data:
                return {"signal": "HOLD", "reason": "가격 조회 실패"}
            
            current_price = int(price_data.get("stck_prpr", 0))
            change_rate = float(price_data.get("prdy_ctrt", 0))
            volume = int(price_data.get("acml_vol", 0))
            
            # 2. 일봉 데이터 조회 (AI 분석용)
            daily_df = self.client.get_daily_chart(ticker)
            
            if daily_df.empty or len(daily_df) < 20:
                return {
                    "signal": "HOLD",
                    "reason": "데이터 부족",
                    "price": current_price,
                }
            
            # 컬럼명 정리
            daily_df = daily_df.rename(columns={
                "stck_clpr": "Close",
                "stck_oprc": "Open",
                "stck_hgpr": "High",
                "stck_lwpr": "Low",
                "acml_vol": "Volume",
            })
            
            for col in ["Close", "Open", "High", "Low", "Volume"]:
                if col in daily_df.columns:
                    daily_df[col] = pd.to_numeric(daily_df[col], errors="coerce")
            
            # 3. AI 봇 분석
            signal, reason, tp_rate = await self.bot.analyze(ticker, daily_df)
            
            return {
                "ticker": ticker,
                "rank": rank,
                "signal": signal,
                "reason": reason,
                "price": current_price,
                "change_rate": change_rate,
                "volume": volume,
                "tp_rate": tp_rate,
            }
            
        except Exception as e:
            logger.error(f"[{ticker}] 분석 오류: {e}")
            return {"signal": "HOLD", "reason": str(e)}
    
    async def _execute_signal(self, analysis: Dict) -> bool:
        """매매 신호 실행"""
        signal = analysis.get("signal", "HOLD")
        ticker = analysis.get("ticker", "")
        price = analysis.get("price", 0)
        reason = analysis.get("reason", "")
        
        if signal == "HOLD":
            return False
        
        try:
            if signal == "BUY":
                # 매수 조건 검증
                if len(self.positions) >= self.config["max_positions"]:
                    logger.info(f"[{ticker}] 매수 스킵: 최대 포지션 도달 ({len(self.positions)}/{self.config['max_positions']})")
                    return False
                
                if ticker in self.positions:
                    logger.info(f"[{ticker}] 매수 스킵: 이미 보유 중")
                    return False
                
                # 주문 수량 계산
                quantity = self.config["max_position_size"] // price
                if quantity < 1:
                    logger.info(f"[{ticker}] 매수 스킵: 주문 가능 수량 0")
                    return False
                
                # 매수 주문 실행
                result = self.client.place_order(
                    ticker=ticker,
                    action="BUY",
                    quantity=quantity,
                    price=0,  # 시장가
                    market="KR"
                )
                
                if result.get("success"):
                    logger.info(f"🟢 [BUY] {ticker} {quantity}주 @ 시장가 | 사유: {reason}")
                    self.trade_history.append({
                        "time": datetime.now().isoformat(),
                        "ticker": ticker,
                        "action": "BUY",
                        "quantity": quantity,
                        "price": price,
                        "order_no": result.get("order_no"),
                    })
                    return True
                else:
                    logger.warning(f"[{ticker}] 매수 실패: {result.get('message')}")
                    return False
            
            elif signal == "SELL":
                # 매도 조건 검증
                if ticker not in self.positions:
                    logger.info(f"[{ticker}] 매도 스킵: 보유하지 않음")
                    return False
                
                position = self.positions[ticker]
                quantity = position["quantity"]
                
                # 매도 주문 실행
                result = self.client.place_order(
                    ticker=ticker,
                    action="SELL",
                    quantity=quantity,
                    price=0,  # 시장가
                    market="KR"
                )
                
                if result.get("success"):
                    profit = (price - position["avg_price"]) * quantity
                    profit_rate = (price / position["avg_price"] - 1) * 100
                    logger.info(f"🔴 [SELL] {ticker} {quantity}주 @ 시장가 | 손익: {profit:+,.0f}원 ({profit_rate:+.2f}%) | 사유: {reason}")
                    self.trade_history.append({
                        "time": datetime.now().isoformat(),
                        "ticker": ticker,
                        "action": "SELL",
                        "quantity": quantity,
                        "price": price,
                        "profit": profit,
                        "profit_rate": profit_rate,
                        "order_no": result.get("order_no"),
                    })
                    return True
                else:
                    logger.warning(f"[{ticker}] 매도 실패: {result.get('message')}")
                    return False
        
        except Exception as e:
            logger.error(f"[{ticker}] 주문 실행 오류: {e}")
            return False
        
        return False
    
    async def _check_stop_loss_take_profit(self):
        """손절/익절 체크"""
        for ticker, position in list(self.positions.items()):
            try:
                price_data = self.client.get_price(ticker)
                if not price_data:
                    continue
                
                current_price = int(price_data.get("stck_prpr", 0))
                avg_price = position["avg_price"]
                profit_rate = (current_price / avg_price - 1)
                
                # 손절 체크
                if profit_rate <= -self.config["stop_loss_rate"]:
                    logger.warning(f"⚠️ [STOP LOSS] {ticker} 손절 발동 ({profit_rate*100:.2f}%)")
                    await self._execute_signal({
                        "ticker": ticker,
                        "signal": "SELL",
                        "price": current_price,
                        "reason": f"손절 발동 ({profit_rate*100:.2f}%)",
                    })
                
                # 익절 체크
                elif profit_rate >= self.config["take_profit_rate"]:
                    logger.info(f"💰 [TAKE PROFIT] {ticker} 익절 발동 ({profit_rate*100:.2f}%)")
                    await self._execute_signal({
                        "ticker": ticker,
                        "signal": "SELL",
                        "price": current_price,
                        "reason": f"익절 발동 ({profit_rate*100:.2f}%)",
                    })
            
            except Exception as e:
                logger.error(f"[{ticker}] 손익 체크 오류: {e}")
    
    async def run(self):
        """메인 매매 루프"""
        self.running = True
        scan_count = 0
        
        logger.info("")
        logger.info("🔥 자동매매 시작! (Ctrl+C로 종료)")
        logger.info("=" * 60)
        
        while self.running:
            try:
                scan_count += 1
                
                # 시장 상태 체크
                tradable = MarketStatusChecker.get_tradable_markets()
                
                if "KR" not in tradable:
                    if scan_count % 60 == 0:  # 1분마다 로그
                        logger.info("📴 한국 시장 휴장 중... 대기")
                    await asyncio.sleep(60)
                    continue
                
                # S급 종목 분석 (최우선)
                for ticker in self.target_manager.targets["S"]:
                    analysis = await self._analyze_ticker(ticker, "S")
                    if analysis.get("signal") != "HOLD":
                        logger.info(f"🎯 [S급] {ticker}: {analysis.get('signal')} - {analysis.get('reason')}")
                        await self._execute_signal(analysis)
                    await asyncio.sleep(0.1)  # Rate limit
                
                # A급 종목 분석
                for ticker in self.target_manager.targets["A"]:
                    analysis = await self._analyze_ticker(ticker, "A")
                    if analysis.get("signal") != "HOLD":
                        logger.info(f"🔍 [A급] {ticker}: {analysis.get('signal')} - {analysis.get('reason')}")
                        await self._execute_signal(analysis)
                    await asyncio.sleep(0.1)
                
                # 손절/익절 체크
                await self._check_stop_loss_take_profit()
                
                # 잔고 동기화 (10회마다)
                if scan_count % 10 == 0:
                    await self._sync_positions()
                
                # 상태 출력 (30회마다)
                if scan_count % 30 == 0:
                    logger.info(f"📊 스캔 #{scan_count} | 보유: {len(self.positions)}종목 | 금일 거래: {len(self.trade_history)}건")
                
                await asyncio.sleep(self.config["scan_interval"])
            
            except KeyboardInterrupt:
                logger.info("\n⏹️ 중지 요청 수신...")
                break
            
            except Exception as e:
                logger.error(f"메인 루프 오류: {e}")
                await asyncio.sleep(5)
        
        await self.shutdown()
    
    async def shutdown(self):
        """엔진 종료"""
        self.running = False
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("📊 거래 요약")
        logger.info("=" * 60)
        
        if self.trade_history:
            total_profit = sum(t.get("profit", 0) for t in self.trade_history if t.get("action") == "SELL")
            logger.info(f"총 거래: {len(self.trade_history)}건")
            logger.info(f"실현 손익: {total_profit:+,.0f}원")
        else:
            logger.info("거래 없음")
        
        logger.info("")
        logger.info("✅ ISATS 자동매매 엔진 종료")


# ================================================================================
# 🎬 메인 실행
# ================================================================================

async def main():
    parser = argparse.ArgumentParser(description="ISATS 자동매매 실행기")
    parser.add_argument(
        "--mode",
        type=str,
        choices=["virtual", "real"],
        default="virtual",
        help="실행 모드 (virtual: 모의투자, real: 실전투자)"
    )
    args = parser.parse_args()
    
    # 로그 디렉토리 생성
    os.makedirs(os.path.join(current_dir, "logs"), exist_ok=True)
    
    # 실전 모드 경고
    if args.mode == "real":
        print("\n" + "=" * 60)
        print("⚠️  경고: 실전투자 모드입니다!")
        print("실제 자금이 투입됩니다.")
        print("=" * 60)
        confirm = input("계속하시겠습니까? (yes/no): ")
        if confirm.lower() != "yes":
            print("취소되었습니다.")
            return
    
    # 엔진 실행
    engine = AutoTradingEngine(mode=args.mode)
    
    if await engine.initialize():
        await engine.run()
    else:
        logger.error("❌ 엔진 초기화 실패. 종료합니다.")


if __name__ == "__main__":
    if os.name == "nt":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n프로그램이 종료되었습니다.")
