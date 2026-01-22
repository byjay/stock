# -*- coding: utf-8 -*-
"""
================================================================================
🌟 ISATS 가상매매 통합 자동매매 시스템 (Virtual Trading Engine)
================================================================================
모의투자가 아닌 "가상매매" 전용 시스템

지원 상품:
- 🇰🇷 한국 주식 (KOSPI, KOSDAQ)
- 🇺🇸 미국 주식 (NYSE, NASDAQ)
- 📊 ETF (국내/해외)
- 💹 선물 (지수선물, 야간선물)
- 🎯 옵션 (지수옵션)

특징:
- 실제 자금 없이 가상으로 매매
- 모든 매매 내역 딥러닝 학습
- 실시간 성과 분석
================================================================================
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional
import json

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

import pandas as pd
import numpy as np

from core.kis_official_api import KISUnifiedClient

# 로깅 설정
os.makedirs(os.path.join(current_dir, "logs"), exist_ok=True)
os.makedirs(os.path.join(current_dir, "data", "trades"), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            os.path.join(current_dir, "logs", f"virtual_trading_{datetime.now().strftime('%Y%m%d')}.log"),
            encoding="utf-8"
        )
    ]
)
logger = logging.getLogger(__name__)


# ================================================================================
# 🎯 가상매매 타겟 (전 상품)
# ================================================================================

VIRTUAL_TARGETS = {
    # 한국 주식
    "KR_STOCKS": [
        {"ticker": "005930", "name": "삼성전자", "type": "STOCK"},
        {"ticker": "000660", "name": "SK하이닉스", "type": "STOCK"},
        {"ticker": "035420", "name": "NAVER", "type": "STOCK"},
        {"ticker": "035720", "name": "카카오", "type": "STOCK"},
        {"ticker": "051910", "name": "LG화학", "type": "STOCK"},
    ],
    
    # 미국 주식
    "US_STOCKS": [
        {"ticker": "AAPL", "name": "Apple", "type": "STOCK", "exchange": "NAS"},
        {"ticker": "MSFT", "name": "Microsoft", "type": "STOCK", "exchange": "NAS"},
        {"ticker": "NVDA", "name": "NVIDIA", "type": "STOCK", "exchange": "NAS"},
        {"ticker": "GOOGL", "name": "Alphabet", "type": "STOCK", "exchange": "NAS"},
        {"ticker": "TSLA", "name": "Tesla", "type": "STOCK", "exchange": "NAS"},
    ],
    
    # 국내 ETF
    "KR_ETF": [
        {"ticker": "069500", "name": "KODEX 200", "type": "ETF"},
        {"ticker": "102110", "name": "TIGER 200", "type": "ETF"},
        {"ticker": "233740", "name": "KODEX 코스닥150레버리지", "type": "ETF"},
    ],
    
    # 미국 ETF
    "US_ETF": [
        {"ticker": "SPY", "name": "S&P 500 ETF", "type": "ETF", "exchange": "NYS"},
        {"ticker": "QQQ", "name": "NASDAQ 100 ETF", "type": "ETF", "exchange": "NAS"},
        {"ticker": "IWM", "name": "Russell 2000 ETF", "type": "ETF", "exchange": "NYS"},
    ],
    
    # 선물 (가상)
    "FUTURES": [
        {"ticker": "101", "name": "KOSPI200 선물", "type": "FUTURE"},
        {"ticker": "106", "name": "미니 KOSPI200 선물", "type": "FUTURE"},
    ],
}


# ================================================================================
# 💰 가상 지갑 (Virtual Wallet)
# ================================================================================

class VirtualWallet:
    """가상 자금 관리"""
    
    def __init__(self, initial_capital: float = 100_000_000):
        """
        Args:
            initial_capital: 초기 자본금 (기본 1억원)
        """
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions = {}  # {ticker: {quantity, avg_price, type, market}}
        self.trade_history = []
        self.daily_pnl = []
        
        self._load_state()
    
    def _get_state_file(self) -> str:
        return os.path.join(current_dir, "data", "virtual_wallet.json")
    
    def _load_state(self):
        """저장된 상태 로드"""
        state_file = self._get_state_file()
        if os.path.exists(state_file):
            try:
                with open(state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    self.cash = state.get("cash", self.initial_capital)
                    self.positions = state.get("positions", {})
                    self.trade_history = state.get("trade_history", [])
                    logger.info(f"💾 가상 지갑 로드: 현금 {self.cash:,.0f}원, 보유 {len(self.positions)}종목")
            except Exception as e:
                logger.warning(f"지갑 로드 실패: {e}")
    
    def _save_state(self):
        """상태 저장"""
        state = {
            "cash": self.cash,
            "positions": self.positions,
            "trade_history": self.trade_history[-1000:],  # 최근 1000건만
            "last_updated": datetime.now().isoformat(),
        }
        
        with open(self._get_state_file(), 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    
    def buy(self, ticker: str, price: float, quantity: int, 
            market: str = "KR", product_type: str = "STOCK") -> bool:
        """가상 매수"""
        total_cost = price * quantity
        
        if self.cash < total_cost:
            logger.warning(f"[{ticker}] 매수 실패: 자금 부족 (필요: {total_cost:,.0f}, 보유: {self.cash:,.0f})")
            return False
        
        # 현금 차감
        self.cash -= total_cost
        
        # 포지션 추가/업데이트
        if ticker in self.positions:
            pos = self.positions[ticker]
            total_qty = pos["quantity"] + quantity
            avg_price = (pos["avg_price"] * pos["quantity"] + price * quantity) / total_qty
            pos["quantity"] = total_qty
            pos["avg_price"] = avg_price
        else:
            self.positions[ticker] = {
                "quantity": quantity,
                "avg_price": price,
                "type": product_type,
                "market": market,
            }
        
        # 거래 기록
        trade = {
            "time": datetime.now().isoformat(),
            "ticker": ticker,
            "action": "BUY",
            "price": price,
            "quantity": quantity,
            "total": total_cost,
            "market": market,
            "type": product_type,
        }
        self.trade_history.append(trade)
        self._save_state()
        
        logger.info(f"💰 [BUY] {ticker} {quantity}주 @ {price:,.0f} = {total_cost:,.0f} | 잔액: {self.cash:,.0f}")
        return True
    
    def sell(self, ticker: str, price: float, quantity: int) -> bool:
        """가상 매도"""
        if ticker not in self.positions:
            logger.warning(f"[{ticker}] 매도 실패: 보유하지 않음")
            return False
        
        pos = self.positions[ticker]
        if pos["quantity"] < quantity:
            logger.warning(f"[{ticker}] 매도 실패: 수량 부족 (보유: {pos['quantity']}, 요청: {quantity})")
            return False
        
        # 현금 증가
        total_revenue = price * quantity
        self.cash += total_revenue
        
        # 손익 계산
        profit = (price - pos["avg_price"]) * quantity
        profit_rate = (price / pos["avg_price"] - 1) * 100
        
        # 포지션 업데이트
        pos["quantity"] -= quantity
        if pos["quantity"] == 0:
            del self.positions[ticker]
        
        # 거래 기록
        trade = {
            "time": datetime.now().isoformat(),
            "ticker": ticker,
            "action": "SELL",
            "price": price,
            "quantity": quantity,
            "total": total_revenue,
            "profit": profit,
            "profit_rate": profit_rate,
            "market": pos.get("market", "KR"),
            "type": pos.get("type", "STOCK"),
        }
        self.trade_history.append(trade)
        self._save_state()
        
        logger.info(f"💸 [SELL] {ticker} {quantity}주 @ {price:,.0f} = {total_revenue:,.0f} | 손익: {profit:+,.0f} ({profit_rate:+.2f}%) | 잔액: {self.cash:,.0f}")
        return True
    
    def get_total_value(self, current_prices: Dict[str, float]) -> float:
        """총 자산 평가"""
        position_value = sum(
            current_prices.get(ticker, pos["avg_price"]) * pos["quantity"]
            for ticker, pos in self.positions.items()
        )
        return self.cash + position_value
    
    def get_summary(self) -> Dict:
        """요약 정보"""
        return {
            "cash": self.cash,
            "positions_count": len(self.positions),
            "total_trades": len(self.trade_history),
            "initial_capital": self.initial_capital,
        }


# ================================================================================
# 🤖 가상매매 자동 엔진
# ================================================================================

class VirtualTradingEngine:
    """가상매매 통합 자동 엔진"""
    
    def __init__(self):
        self.wallet = VirtualWallet(initial_capital=100_000_000)  # 1억원
        self.client: Optional[KISUnifiedClient] = None
        self.running = False
        
        # 설정
        self.config = {
            "max_position_per_stock": 5_000_000,  # 종목당 최대 500만원
            "max_positions": 20,  # 최대 20종목
            "stop_loss_rate": 0.05,  # 손절 -5%
            "take_profit_rate": 0.10,  # 익절 +10%
            "scan_interval": 3.0,  # 스캔 주기
        }
    
    async def initialize(self) -> bool:
        """초기화"""
        logger.info("=" * 70)
        logger.info("🌟 가상매매 통합 자동매매 시스템 초기화")
        logger.info("=" * 70)
        
        try:
            # KIS API 클라이언트 (모의투자 모드)
            self.client = KISUnifiedClient(mode="virtual")
            self.client.initialize()
            
            logger.info("✅ KIS API 초기화 완료")
            
            # 지갑 상태
            summary = self.wallet.get_summary()
            logger.info(f"💰 가상 자본금: {summary['initial_capital']:,.0f}원")
            logger.info(f"💵 현재 현금: {summary['cash']:,.0f}원")
            logger.info(f"📊 보유 종목: {summary['positions_count']}개")
            logger.info(f"📝 총 거래: {summary['total_trades']}건")
            
            # 타겟 종목 수
            total_targets = sum(len(v) for v in VIRTUAL_TARGETS.values())
            logger.info(f"🎯 감시 대상: {total_targets}종목 (주식/ETF/선물)")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 초기화 실패: {e}")
            return False
    
    async def analyze_and_trade(self, target: Dict) -> bool:
        """종목 분석 및 매매"""
        ticker = target["ticker"]
        name = target["name"]
        product_type = target["type"]
        market = "US" if target.get("exchange") else "KR"
        
        try:
            # 현재가 조회
            if market == "KR":
                price_data = self.client.get_price(ticker, market="KR")
                current_price = int(price_data.get("stck_prpr", 0))
                change_rate = float(price_data.get("prdy_ctrt", 0))
            else:
                exchange = target.get("exchange", "NAS")
                price_data = self.client.overseas_stock.get_price(ticker, exchange)
                current_price = float(price_data.get("last", price_data.get("stck_prpr", 0)))
                change_rate = float(price_data.get("rate", price_data.get("prdy_ctrt", 0)))
            
            if current_price == 0:
                return False
            
            # 단순 전략: 급등 매수, 급락 매도
            signal = None
            
            # 보유 중인지 확인
            is_holding = ticker in self.wallet.positions
            
            if not is_holding:
                # 매수 신호: 2% 이상 상승
                if change_rate >= 2.0:
                    signal = "BUY"
                    quantity = int(self.config["max_position_per_stock"] / current_price)
                    
                    if quantity >= 1 and len(self.wallet.positions) < self.config["max_positions"]:
                        success = self.wallet.buy(ticker, current_price, quantity, market, product_type)
                        if success:
                            logger.info(f"🟢 [{product_type}] {name}({ticker}) 매수 완료 - 급등 {change_rate:+.2f}%")
                            return True
            else:
                # 매도 신호: 손절 또는 익절
                pos = self.wallet.positions[ticker]
                profit_rate = (current_price / pos["avg_price"] - 1)
                
                if profit_rate <= -self.config["stop_loss_rate"]:
                    # 손절
                    success = self.wallet.sell(ticker, current_price, pos["quantity"])
                    if success:
                        logger.warning(f"🔴 [{product_type}] {name}({ticker}) 손절 매도 ({profit_rate*100:.2f}%)")
                        return True
                
                elif profit_rate >= self.config["take_profit_rate"]:
                    # 익절
                    success = self.wallet.sell(ticker, current_price, pos["quantity"])
                    if success:
                        logger.info(f"💚 [{product_type}] {name}({ticker}) 익절 매도 (+{profit_rate*100:.2f}%)")
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"[{ticker}] 오류: {e}")
            return False
    
    async def run(self):
        """메인 루프"""
        self.running = True
        scan_count = 0
        
        logger.info("")
        logger.info("🔥 가상매매 시작! (Ctrl+C로 종료)")
        logger.info("=" * 70)
        
        while self.running:
            try:
                scan_count += 1
                
                # 모든 카테고리 순회
                for category, targets in VIRTUAL_TARGETS.items():
                    for target in targets:
                        await self.analyze_and_trade(target)
                        await asyncio.sleep(0.3)  # Rate limit
                
                # 상태 출력
                if scan_count % 20 == 0:
                    summary = self.wallet.get_summary()
                    logger.info(f"📊 스캔 #{scan_count} | 현금: {summary['cash']:,.0f} | 보유: {summary['positions_count']}종목 | 거래: {summary['total_trades']}건")
                
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
        logger.info("=" * 70)
        logger.info("📊 가상매매 최종 결과")
        logger.info("=" * 70)
        
        summary = self.wallet.get_summary()
        logger.info(f"💰 초기 자본: {summary['initial_capital']:,.0f}원")
        logger.info(f"💵 최종 현금: {summary['cash']:,.0f}원")
        logger.info(f"📊 보유 종목: {summary['positions_count']}개")
        logger.info(f"📝 총 거래: {summary['total_trades']}건")
        
        # 수익률 계산 (현재 시세 필요)
        logger.info("")
        logger.info("✅ 가상매매 종료")


# ================================================================================
# 🎬 메인
# ================================================================================

async def main():
    engine = VirtualTradingEngine()
    
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
