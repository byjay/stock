import os
import yaml
import json
import asyncio
from datetime import datetime

from core.kis_api_client import KISAPIClient

# ==========================================
# 🛡️ TRI-ENGINE MANAGER (Real/Virtual/Mock)
# ==========================================

class DualEngineManager:
    def __init__(self, initial_balance_usd=10000.0):
        self.config_path = "config/dual_engine.yaml"
        self.wallet_path = "config/virtual_wallet.json"
        self.secrets_path = "config/secrets.yaml"
        self.mode = "VIRTUAL" 
        
        # Engine 1: Real Account (Monitoring Only)
        self.real_client = None
        self.real_balance = 0
        self.real_positions = []
        self.real_trades = []
        
        # Engine 2: Virtual Trading (Internal Simulation)
        self.virtual_balance = initial_balance_usd
        self.virtual_portfolio = {}
        self.virtual_trades = []
        
        # Engine 3: Mock Investment (KIS Mock API)
        self.mock_client = None
        self.mock_balance = 0
        self.mock_positions = []
        self.mock_trades = []
        
        self.market_depth = {} 
        self.report_queue = [] 
        self.load_config()
        self.load_wallet()
        
    async def setup_clients(self):
        """Async initialization required for KIS clients"""
        # Engine 1: Real
        self.real_client = KISAPIClient(account_type='real')
        await self.real_client.initialize()
        
        # Rate limit mitigation (1 token per 1 min per key)
        # If keys are same, we wait or share, for now just wait a bit
        await asyncio.sleep(2) 
        
        # Engine 3: Mock
        self.mock_client = KISAPIClient(account_type='virtual')
        await self.mock_client.initialize()

    def add_report(self, unit, rank, action, detail):
        """사령관님께 올리는 실시간 보고서 작성"""
        report = {
            "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
            "unit": unit,   # 부대 (Agent, Strategy, Guard 등)
            "rank": rank,   # 계급 (이병, 영관, 장군 등)
            "action": action, # 행동
            "detail": detail # 상세 내용
        }
        self.report_queue.append(report)
        if len(self.report_queue) > 100: self.report_queue.pop(0) # 최신 100건 유지
        print(f"📡 [Panopticon] {rank} {unit}: {action} | {detail}")

    def load_config(self):
        """설정 파일 로드"""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                self.mode = config.get('system', {}).get('primary', 'VIRTUAL').upper()
        print(f"🛡️ [Guard] 현재 엔진 모드: {self.mode}")

    def load_wallet(self):
        """가상 지갑 및 포트폴리오 상태 로드 (Engine 2)"""
        if os.path.exists(self.wallet_path):
            with open(self.wallet_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.virtual_balance = data.get('balance', self.virtual_balance)
                self.virtual_portfolio = data.get('portfolio', {})
        else:
            self.save_wallet()

    def save_wallet(self):
        """지갑 상태 영구 저장 (Engine 2)"""
        data = {
            'balance': self.virtual_balance,
            'portfolio': self.virtual_portfolio,
            'last_update': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        os.makedirs(os.path.dirname(self.wallet_path), exist_ok=True)
        with open(self.wallet_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

    def update_market_depth(self, ticker, bid_hoga, ask_hoga):
        """실시간 호가 정보 업데이트 (매수/매도 각각 10호가 등)"""
        self.market_depth[ticker] = {
            'bid': bid_hoga, # [(가격1, 잔량1), (가격2, 잔량2), ...]
            'ask': ask_hoga
        }

    async def execute_order(self, ticker, action, requested_price, requested_quantity, engine_type='virtual', fee_rate=0.00015):
        """
        초정밀 매칭 엔진 (Liquidity Matching)
        engine_type: 'virtual' or 'mock' (real is blocked)
        """
        if engine_type == 'real':
            print(f"⚠️ [CRITICAL] REAL ORDER (Implementation Blocked): {action} {ticker}")
            return False
            
        if engine_type == 'mock':
            # Engine 3: KIS Mock Investment Order
            if not self.mock_client:
                await self.setup_clients()
            
            # KIS API 주문 집행
            res = await self.mock_client.place_order(
                ticker=ticker,
                action=action,
                price=int(requested_price),
                quantity=int(requested_quantity),
                order_type="01" # 기본 시장가 주문
            )
            
            if res.get('success'):
                print(f"🚀 [Mock] KIS API 주문 성공: {action} {ticker} {requested_quantity}주")
                self.add_report("MockEngine", "Major", "ORDER_SUCCESS", f"KIS Order #{res.get('order_no')}: {action} {ticker}")
                return True
            else:
                print(f"❌ [Mock] KIS API 주문 실패: {res.get('error')}")
                self.add_report("MockEngine", "Colonel", "ORDER_FAILED", f"Error: {res.get('error')}")
                return False

        # 1. 호가 데이터 확보 확인
        depth = self.market_depth.get(ticker)
        if not depth:
            # 호가 데이터가 없으면 requested_price로 즉시 체결 (시뮬레이션)
            print(f"⚠️ [Virtual] 호가 데이터 부재 - 시장가 즉시 체결: {ticker}")
            total_filled_qty = requested_quantity
            total_filled_amount = requested_price * requested_quantity
        else:
            # 기존 호가 매칭 로직
            total_filled_qty = 0
            total_filled_amount = 0
            
            if action == "BUY":
                # 매수 시에는 '매도 호가(Ask)'에 있는 물량을 가져와야 함
                for ask_price, ask_vol in depth['ask']:
                    if ask_price > requested_price: break # 내 희망가보다 비싸면 중단
                    
                    match_vol = min(requested_quantity - total_filled_qty, ask_vol)
                    if match_vol <= 0: break
                    
                    total_filled_qty += match_vol
                    total_filled_amount += (ask_price * match_vol)
                    if total_filled_qty >= requested_quantity: break
                    
            elif action == "SELL":
                # 매도 시에는 '매수 호가(Bid)'에 있는 물량을 가져와야 함
                for bid_price, bid_vol in depth['bid']:
                    if bid_price < requested_price: break # 내 희망가보다 싸면 중단
                    
                    match_vol = min(requested_quantity - total_filled_qty, bid_vol)
                    if match_vol <= 0: break
                    
                    total_filled_qty += match_vol
                    total_filled_amount += (bid_price * match_vol)
                    if total_filled_qty >= requested_quantity: break

        # 2. 결과 처리
        if total_filled_qty == 0:
            print(f"🚫 [Virtual] 체결 실패 (유동성 부족/가격 불일치): {ticker} @ {requested_price}")
            return False

        fee = total_filled_amount * fee_rate
        avg_price = total_filled_amount / total_filled_qty

        if action == "BUY":
            if self.virtual_balance >= (total_filled_amount + fee):
                self.virtual_balance -= (total_filled_amount + fee)
                self.virtual_portfolio[ticker] = self.virtual_portfolio.get(ticker, 0) + total_filled_qty
                print(f"📉 [Virtual] BUY SUCCESS: {ticker} | {total_filled_qty}주 @ {avg_price:,.0f} KRW (체결률: {total_filled_qty/requested_quantity*100:.1f}%)")
            else:
                print(f"🚫 [Virtual] 잔고 부족: 필요 { (total_filled_amount + fee):,.0f} KRW")
                return False
        elif action == "SELL":
            if self.virtual_portfolio.get(ticker, 0) >= total_filled_qty:
                self.virtual_balance += (total_filled_amount - fee)
                self.virtual_portfolio[ticker] -= total_filled_qty
                if self.virtual_portfolio[ticker] == 0: del self.virtual_portfolio[ticker]
                print(f"📈 [Virtual] SELL SUCCESS: {ticker} | {total_filled_qty}주 @ {avg_price:,.0f} KRW (체결률: {total_filled_qty/requested_quantity*100:.1f}%)")
            else:
                return False
        
        self.save_wallet()
        
        # Record Virtual Trade
        trade_entry = {
            'timestamp': datetime.now().strftime("%H:%M:%S"),
            'ticker': ticker,
            'action': "매수" if action == "BUY" else "매도",
            'qty': total_filled_qty,
            'price': avg_price,
            'engine': 'virtual'
        }
        self.virtual_trades.append(trade_entry)
        if len(self.virtual_trades) > 50: self.virtual_trades.pop(0)

        self.add_report("Guard", "General", "ORDER_COMPLETE", f"{action} {ticker} | {total_filled_qty} shares @ {avg_price}")
        return True

    async def update_balances(self):
        """KIS API를 통한 실시간 잔고 및 거래내역 업데이트"""
        try:
            if not self.real_client or not self.mock_client:
                await self.setup_clients()
            
            # 1. Real Account Data
            real_res = await self.real_client.get_balance()
            if real_res:
                self.real_balance = real_res.get('total_value', 0)
                self.real_positions = real_res.get('positions', [])
            self.real_trades = await self.real_client.get_trade_history()
                
            # 2. Mock Account Data
            mock_res = await self.mock_client.get_balance()
            if mock_res:
                self.mock_balance = mock_res.get('total_value', 0)
                self.mock_positions = mock_res.get('positions', [])
            
            # 3. Global Expansion: Sync Overseas Data (Experimental)
            try:
                ovrs_res = await self.mock_client.get_overseas_balance()
                if ovrs_res and ovrs_res.get('positions'):
                    self.mock_positions.extend(ovrs_res['positions'])
                    self.mock_balance += ovrs_res.get('total_value', 0)
                
                ovrs_trades = await self.mock_client.get_overseas_trade_history()
                if ovrs_trades:
                    self.mock_trades.extend(ovrs_trades)
            except Exception as e:
                print(f"⚠️ [Engine] Overseas data sync skipped: {e}")

            self.mock_trades = await self.mock_client.get_trade_history()
            if len(self.mock_trades) > 50: self.mock_trades = self.mock_trades[:50]
                
            self.add_report("Engine", "System", "SYNC_COMPLETE", "Global Tri-Engine data synchronized")
        except Exception as e:
            print(f"❌ [Engine] Sync failed: {e}")

    def get_status(self):
        return {
            'mode': self.mode,
            'balances': {
                'real': self.real_balance,
                'virtual': self.virtual_balance,
                'mock': self.mock_balance
            },
            'positions': {
                'real': self.real_positions,
                'virtual': self.virtual_portfolio,
                'mock': self.mock_positions
            },
            'trades': {
                'real': self.real_trades,
                'virtual': self.virtual_trades,
                'mock': self.mock_trades
            },
            'reports': self.report_queue
        }

    async def get_market_analysis(self):
        """시장 분석 데이터 취합 (ELW, 해외 업종 등)"""
        if not self.mock_client: return {}
        
        # 병렬 요청으로 속도 최적화
        elw_task = self.mock_client.get_elw_sensitivity()
        industry_task = self.mock_client.get_overseas_industry_prices()
        
        elw, industry = await asyncio.gather(elw_task, industry_task)
        return {
            "elw_ranking": elw[:10],
            "overseas_industry": industry[:10]
        }
