# -*- coding: utf-8 -*-
"""
================================================================================
🇺🇸 ISATS 미국주식 자동매매 실행기 (US Stock Auto Trading)
================================================================================
KIS Open API 해외주식 모듈 통합

지원 거래소:
- NYSE (뉴욕증권거래소)
- NASDAQ (나스닥)
- AMEX (아메리카 증권거래소)

실행 방법:
    python us_trading_launcher.py --mode virtual
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

# 로깅 설정
os.makedirs(os.path.join(current_dir, "logs"), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            os.path.join(current_dir, "logs", f"us_trading_{datetime.now().strftime('%Y%m%d')}.log"),
            encoding="utf-8"
        )
    ]
)
logger = logging.getLogger(__name__)


# ================================================================================
# 🇺🇸 미국 시장 타겟 종목
# ================================================================================

US_TARGETS = {
    "S": [  # S급 - 핵심 대형주
        {"ticker": "AAPL", "name": "Apple", "exchange": "NAS"},
        {"ticker": "MSFT", "name": "Microsoft", "exchange": "NAS"},
        {"ticker": "NVDA", "name": "NVIDIA", "exchange": "NAS"},
    ],
    "A": [  # A급 - 성장주
        {"ticker": "GOOGL", "name": "Alphabet", "exchange": "NAS"},
        {"ticker": "AMZN", "name": "Amazon", "exchange": "NAS"},
        {"ticker": "META", "name": "Meta", "exchange": "NAS"},
        {"ticker": "TSLA", "name": "Tesla", "exchange": "NAS"},
    ],
    "B": [  # B급 - ETF 및 기타
        {"ticker": "SPY", "name": "S&P 500 ETF", "exchange": "NYS"},
        {"ticker": "QQQ", "name": "NASDAQ 100 ETF", "exchange": "NAS"},
        {"ticker": "VOO", "name": "Vanguard S&P 500", "exchange": "NYS"},
    ],
}


# ================================================================================
# 🕐 미국 시장 시간 체커
# ================================================================================

class USMarketChecker:
    """미국 시장 거래 시간 확인 (KST 기준)"""
    
    @classmethod
    def is_market_open(cls) -> bool:
        """미국 장 개장 여부 (KST 기준)"""
        now = datetime.now()
        hour = now.hour
        weekday = now.weekday()
        
        # 주말 제외
        if weekday >= 5:
            return False
        
        # 서머타임 기준 (22:30 ~ 05:00 KST)
        # 겨울 기준 (23:30 ~ 06:00 KST)
        # 현재: 겨울 시간으로 가정
        if hour >= 23 or hour < 6:
            return True
        
        return False
    
    @classmethod
    def get_status(cls) -> str:
        """시장 상태 문자열"""
        if cls.is_market_open():
            return "🟢 OPEN (정규장)"
        
        now = datetime.now()
        hour = now.hour
        
        # 프리마켓 (18:00~23:30 KST)
        if 18 <= hour < 23:
            return "🟡 PRE-MARKET"
        
        # 애프터마켓 (06:00~10:00 KST)
        if 6 <= hour < 10:
            return "🟡 AFTER-HOURS"
        
        return "🔴 CLOSED"


# ================================================================================
# 🤖 미국주식 자동매매 엔진
# ================================================================================

class USAutoTradingEngine:
    """미국주식 자동매매 엔진"""
    
    def __init__(self, mode: str = "virtual"):
        self.mode = mode
        self.client: Optional[KISUnifiedClient] = None
        self.running = False
        
        # 거래 설정
        self.config = {
            "max_position_size": 1000,  # $1000 per stock
            "max_positions": 5,
            "stop_loss_rate": 0.03,
            "take_profit_rate": 0.05,
            "scan_interval": 2.0,  # 미국장은 더 느리게
        }
        
        self.positions = {}
        self.trade_history = []
    
    async def initialize(self) -> bool:
        """엔진 초기화"""
        logger.info("=" * 60)
        logger.info(f"🇺🇸 미국주식 자동매매 엔진 초기화 (모드: {self.mode.upper()})")
        logger.info("=" * 60)
        
        try:
            self.client = KISUnifiedClient(mode=self.mode)
            if not self.client.initialize():
                logger.error("❌ KIS API 초기화 실패")
                return False
            
            logger.info("✅ KIS API 클라이언트 초기화 완료")
            logger.info(f"📊 시장 상태: {USMarketChecker.get_status()}")
            
            # 타겟 종목 수
            total = sum(len(v) for v in US_TARGETS.values())
            logger.info(f"🎯 감시 대상: {total}종목")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 초기화 오류: {e}")
            return False
    
    async def analyze_stock(self, stock: Dict) -> Dict:
        """개별 종목 분석"""
        ticker = stock["ticker"]
        exchange = stock["exchange"]
        name = stock["name"]
        
        try:
            # 현재가 조회
            price_data = self.client.overseas_stock.get_price(ticker, exchange)
            
            if not price_data:
                return {"signal": "HOLD", "reason": "가격 조회 실패"}
            
            current_price = float(price_data.get("last", price_data.get("stck_prpr", 0)))
            change_rate = float(price_data.get("rate", price_data.get("prdy_ctrt", 0)))
            
            # 단순 신호 로직 (RSI/MA 없이)
            signal = "HOLD"
            reason = "관망"
            
            # 급등 감지 (3% 이상)
            if change_rate >= 3.0:
                signal = "BUY"
                reason = f"급등 감지 (+{change_rate:.2f}%)"
            
            # 급락 감지 (-3% 이하) - 손절
            elif change_rate <= -3.0:
                if ticker in self.positions:
                    signal = "SELL"
                    reason = f"급락 손절 ({change_rate:.2f}%)"
            
            return {
                "ticker": ticker,
                "name": name,
                "exchange": exchange,
                "signal": signal,
                "reason": reason,
                "price": current_price,
                "change_rate": change_rate,
            }
            
        except Exception as e:
            logger.error(f"[{ticker}] 분석 오류: {e}")
            return {"signal": "HOLD", "reason": str(e)}
    
    async def execute_signal(self, analysis: Dict) -> bool:
        """매매 신호 실행"""
        signal = analysis.get("signal", "HOLD")
        ticker = analysis.get("ticker", "")
        exchange = analysis.get("exchange", "NAS")
        price = analysis.get("price", 0)
        name = analysis.get("name", "")
        
        if signal == "HOLD":
            return False
        
        try:
            if signal == "BUY":
                if len(self.positions) >= self.config["max_positions"]:
                    logger.info(f"[{ticker}] 매수 스킵: 최대 포지션 도달")
                    return False
                
                if ticker in self.positions:
                    return False
                
                # 주문 수량 계산 (USD 기준)
                quantity = int(self.config["max_position_size"] / price)
                if quantity < 1:
                    return False
                
                # 해외주식 매수
                result = self.client.overseas_stock.place_order(
                    ticker=ticker,
                    exchange=exchange,
                    order_type="BUY",
                    quantity=quantity,
                    price=price
                )
                
                if result.get("success"):
                    logger.info(f"🟢 [BUY] {name}({ticker}) {quantity}주 @ ${price:.2f}")
                    self.positions[ticker] = {
                        "quantity": quantity,
                        "avg_price": price,
                        "name": name,
                    }
                    return True
            
            elif signal == "SELL":
                if ticker not in self.positions:
                    return False
                
                position = self.positions[ticker]
                quantity = position["quantity"]
                
                result = self.client.overseas_stock.place_order(
                    ticker=ticker,
                    exchange=exchange,
                    order_type="SELL",
                    quantity=quantity,
                    price=price
                )
                
                if result.get("success"):
                    profit = (price - position["avg_price"]) * quantity
                    logger.info(f"🔴 [SELL] {name}({ticker}) {quantity}주 @ ${price:.2f} | 손익: ${profit:+.2f}")
                    del self.positions[ticker]
                    return True
        
        except Exception as e:
            logger.error(f"[{ticker}] 주문 오류: {e}")
        
        return False
    
    async def run(self):
        """메인 매매 루프"""
        self.running = True
        scan_count = 0
        
        logger.info("")
        logger.info("🔥 미국주식 자동매매 시작! (Ctrl+C로 종료)")
        logger.info("=" * 60)
        
        while self.running:
            try:
                scan_count += 1
                
                # 시장 상태 표시
                if scan_count % 30 == 1:
                    logger.info(f"📊 시장 상태: {USMarketChecker.get_status()}")
                
                # S급 종목 분석
                for stock in US_TARGETS["S"]:
                    analysis = await self.analyze_stock(stock)
                    if analysis.get("signal") != "HOLD":
                        logger.info(f"🎯 [S급] {stock['name']}: {analysis.get('signal')} - {analysis.get('reason')}")
                        await self.execute_signal(analysis)
                    await asyncio.sleep(0.5)
                
                # A급 종목 분석
                for stock in US_TARGETS["A"]:
                    analysis = await self.analyze_stock(stock)
                    if analysis.get("signal") != "HOLD":
                        logger.info(f"🔍 [A급] {stock['name']}: {analysis.get('signal')}")
                        await self.execute_signal(analysis)
                    await asyncio.sleep(0.5)
                
                # B급 (ETF)
                for stock in US_TARGETS["B"]:
                    analysis = await self.analyze_stock(stock)
                    await asyncio.sleep(0.5)
                
                # 상태 출력
                if scan_count % 30 == 0:
                    logger.info(f"📊 스캔 #{scan_count} | 보유: {len(self.positions)}종목")
                
                await asyncio.sleep(self.config["scan_interval"])
            
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"루프 오류: {e}")
                await asyncio.sleep(5)
        
        await self.shutdown()
    
    async def shutdown(self):
        """종료"""
        self.running = False
        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ 미국주식 자동매매 종료")


# ================================================================================
# 🎬 메인
# ================================================================================

async def main():
    parser = argparse.ArgumentParser(description="ISATS 미국주식 자동매매")
    parser.add_argument("--mode", type=str, choices=["virtual", "real"], default="virtual")
    args = parser.parse_args()
    
    engine = USAutoTradingEngine(mode=args.mode)
    
    if await engine.initialize():
        await engine.run()
    else:
        logger.error("❌ 초기화 실패")


if __name__ == "__main__":
    if os.name == "nt":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n종료")
