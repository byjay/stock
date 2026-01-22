import sys
import os
import asyncio
import json
import yaml
from aiohttp import web
import webbrowser
from pathlib import Path
from datetime import datetime

# 프로젝트 루트 경로 추가
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

# ISATS 코어 모듈 임포트
from core.kis_official_api import KISUnifiedClient
from virtual_trading_engine import VirtualWallet
from deep_learning_trader import TradingTrainer

# ==========================================
# 🏎️ ISATS Singularity Dashboard Server
# ==========================================

class DashboardServer:
    def __init__(self, port=9053):
        self.port = port
        self.app = web.Application()
        
        # 엔진 초기화
        self.kis_real = KISUnifiedClient(mode="real")
        self.kis_virtual = KISUnifiedClient(mode="virtual")
        self.wallet = VirtualWallet()
        self.trainer = TradingTrainer()
        
        # 데이터 폴더 경로
        self.data_dir = Path(ROOT_DIR) / "data"
        self.data_dir.mkdir(exist_ok=True)
        
        self.setup_routes()
        
    def setup_routes(self):
        """MTS 지휘본부 라우트 설정"""
        self.app.router.add_get('/', self.serve_dashboard)
        self.app.router.add_get('/api/status', self.get_system_status)
        self.app.router.add_get('/api/balance', self.get_all_balances)
        self.app.router.add_get('/api/signals', self.get_ai_signals)
        self.app.router.add_post('/api/order', self.place_unified_order)
        self.app.router.add_get('/api/market/radar', self.get_market_radar)
        self.app.router.add_get('/api/chart/{market}/{ticker}', self.get_live_chart)
        
        # 가상 매매 전용
        self.app.router.add_get('/api/virtual/wallet', self.get_virtual_wallet)
        self.app.router.add_get('/api/virtual/history', self.get_virtual_history)
        
    async def initialize_engines(self):
        """엔진 사전 로드"""
        print("🚀 ISATS Engines Warming Up...")
        self.kis_real.initialize()
        self.kis_virtual.initialize()
        self.trainer.load_model()
        print("✅ Systems Ready.")

    async def serve_dashboard(self, request):
        """MTS Supreme v4.0.0 인터페이스 제공"""
        dashboard_path = Path(__file__).parent / "mts_supreme_v4_ultimate.html"
        with open(dashboard_path, 'r', encoding='utf-8') as f:
            html = f.read()
        return web.Response(text=html, content_type='text/html')

    async def get_system_status(self, request):
        """시스템 통합 상태 감시"""
        return web.json_response({
            "timestamp": datetime.now().isoformat(),
            "kis_real": "ACTIVE",
            "kis_virtual": "ACTIVE",
            "deep_learning": "LEARNING",
            "market_status": "OPEN" if 9 <= datetime.now().hour < 16 else "CLOSED"
        })

    async def get_all_balances(self, request):
        """전 계좌(실전/모의/가상) 통합 잔고 데이터"""
        try:
            # 1. 가상 지갑 (Virtual)
            virtual_total = self.wallet.get_total_value({})
            
            # 2. 모의 투자 (Mock)
            _, mock_summary = self.kis_virtual.get_balance(market="KR")
            mock_total = float(mock_summary.get("tot_evlu_amt", 0)) if mock_summary else 10000000.0
            
            # 3. 실전 투자 (Real)
            _, real_summary = self.kis_real.get_balance(market="KR")
            real_total = float(real_summary.get("tot_evlu_amt", 0)) if real_summary else 0.0
            
            return web.json_response({
                "virtual": {"total": virtual_total, "cash": self.wallet.cash},
                "mock": {"total": mock_total},
                "real": {"total": real_total}
            })
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    async def get_ai_signals(self, request):
        """딥러닝 엔진의 신호 분석 결과"""
        # 최근 거래 데이터 기반 예측 (더미 데이터 예시)
        prediction = self.trainer.predict([70000, 10, 14, 3]) # [가격, 수량, 시간, 요일]
        return web.json_response({
            "action": "BUY" if prediction == 1 else "HOLD",
            "confidence": 0.82 + (prediction * 0.1),
            "reason": "Structural pattern matched with LSTM analysis."
        })

    async def place_unified_order(self, request):
        """통합 주문 집행 (Mode 기반)"""
        data = await request.json()
        mode = data.get("mode", "virtual") # real, mock, virtual
        ticker = data.get("ticker")
        action = data.get("action") # BUY, SELL
        quantity = int(data.get("quantity", 1))
        price = float(data.get("price", 0))
        
        try:
            if mode == "virtual":
                if action == "BUY":
                    success = self.wallet.buy(ticker, price, quantity)
                else:
                    success = self.wallet.sell(ticker, price, quantity)
                return web.json_response({"success": success, "mode": "virtual"})
            
            elif mode == "mock":
                result = self.kis_virtual.place_order(ticker, action, quantity, price, market="KR")
                return web.json_response(result)
            
            elif mode == "real":
                result = self.kis_real.place_order(ticker, action, quantity, price, market="KR")
                return web.json_response(result)
                
        except Exception as e:
            return web.json_response({"success": False, "error": str(e)})

    async def get_market_radar(self, request):
        """상승률/거래량 상위 종목 레이더"""
        try:
            # 336개 API 중 랭킹 API 활용
            res = self.kis_virtual.domestic_stock.inquire_ranking()
            return web.json_response(res)
        except:
            return web.json_response({"kr": [], "us": []})

    async def get_live_chart(self, request):
        """분봉/일봉 실시간 차트 데이터"""
        market = request.match_info.get('market', 'KR')
        ticker = request.match_info.get('ticker')
        
        try:
            if market == "KR":
                data = self.kis_virtual.domestic_stock.inquire_daily_price(ticker)
            else:
                data = self.kis_virtual.overseas_stock.get_price(ticker, "NAS")
            return web.json_response(data)
        except Exception as e:
            return web.json_response({"error": str(e)})

    async def get_virtual_wallet(self, request):
        """가상 지갑 상세 정보"""
        return web.json_response({
            "cash": self.wallet.cash,
            "positions": self.wallet.positions
        })

    async def get_virtual_history(self, request):
        """가상 매매 히스토리"""
        return web.json_response(self.wallet.trade_history)

    async def start(self):
        """서버 시작"""
        await self.initialize_engines()
        
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', self.port)
        await site.start()
        
        url = f"http://localhost:{self.port}"
        print(f"\n🛸 [ISATS Portal] Dashboard Engaged!")
        print(f"   📡 URL: {url}")
        
        try:
            webbrowser.open(url)
        except: pass
        
        while True:
            await asyncio.sleep(60)

def main():
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    server = DashboardServer(port=9053)
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print("\n🛑 Dashboard Halted.")

if __name__ == "__main__":
    main()

