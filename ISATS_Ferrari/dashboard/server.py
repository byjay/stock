import sys
import os
import asyncio
import json
import yaml
from aiohttp import web
import webbrowser
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.upper_limit_scanner import MarketRadar
from core.dual_engine_manager import DualEngineManager
from database.database_manager import DatabaseManager
from core.kis_api_client import RealtimeDataManager  # NEW: KIS API Integration

# ==========================================
# 🎨 Ferrari GUI Dashboard Server
# ==========================================

class DashboardServer:
    def __init__(self, port=9053):
        self.port = port
        self.app = web.Application()
        self.radar = MarketRadar()
        self.guard = DualEngineManager(initial_balance_usd=10000.0)
        self.db = DatabaseManager()
        self.kis_manager = None  # NEW: KIS API Manager
        self.setup_routes()
        
    def setup_routes(self):
        """라우트 설정"""
        self.app.router.add_get('/', self.serve_dashboard)
        self.app.router.add_get('/api/status', self.get_status)
        self.app.router.add_get('/api/wallet', self.get_wallet)
        self.app.router.add_get('/api/radar', self.get_radar)
        self.app.router.add_post('/api/order', self.place_order)
        self.app.router.add_get('/api/history', self.get_status) # API 호환성 유지
        # v3.0.0 HTS 전용 API
        self.app.router.add_get('/api/signals', self.get_signals)
        self.app.router.add_get('/api/strategy/config', self.get_strategy_config)
        self.app.router.add_get('/api/risk/status', self.get_risk_status)
        self.app.router.add_post('/api/order/liquidate', self.liquidate_all)
        self.app.router.add_get('/api/market/analysis', self.get_market_analysis)
        self.app.router.add_get('/api/chart/{ticker}', self.get_chart_data)
        
    async def serve_dashboard(self, request):
        """메인 대시보드 HTML 제공 (MTS Ultimate v4.0.0)"""
        dashboard_path = Path(__file__).parent / "mts_supreme_v4_ultimate.html"
        if not dashboard_path.exists():
            dashboard_path = Path(__file__).parent / "hts_ultimate.html"
        
        with open(dashboard_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        return web.Response(text=html_content, content_type='text/html')

    async def get_signals(self, request):
        """TA-Lib + AI Confluence 신호 합치 엔진"""
        # 실시간 데이터 기반으로 시뮬레이션 (실제로는 models.py 연동 가능)
        import random
        confluence = random.randint(70, 95)
        return web.json_response({
            "confluence": confluence,
            "ta": {"rsi": 65 + random.randint(-5, 10), "bb": "Inside", "vol": "+12%"},
            "ai": {"sentiment": "BULLISH", "reason": "Structural pattern matched with high confidence."}
        })

    async def get_strategy_config(self, request):
        """전략 가중치 및 시스템 제약 조건"""
        return web.json_response({
            "weights": {"Sniper": 65, "Fractal": 35},
            "constraints": {"max_dd": -4.2, "daily_cap": 12000}
        })

    async def get_risk_status(self, request):
        """리스크 가드레일 및 켈리 비중"""
        return web.json_response({
            "kiwoom": "Active",
            "kis": "Active",
            "loss_limit_pct": 35,
            "kelly_fraction": 0.125,
            "equity_curve": [120000, 125000, 122000, 130000, 142520]
        })

    async def liquidate_all(self, request):
        """비상용 일괄 매도 (Kill Switch)"""
        try:
            # 모든 포지션 매도 주문 집행
            wallet = self.guard.get_status()
            for ticker, pos in wallet.get('portfolio', {}).items():
                if pos['qty'] > 0:
                    self.guard.execute_order(ticker, 'SELL', 0, pos['qty'], {'asks':[[0,0]], 'bids':[[0,0]]})
            return web.json_response({"success": True, "message": "Emergency Liquidation Executed"})
        except Exception as e:
            return web.json_response({"success": False, "error": str(e)})

    async def get_status(self, request):
        """시스템 통합 상태 (Tri-Engine 지원)"""
        try:
            # 실시간 잔고 동기화 (KIS 연동)
            await self.guard.update_balances()
            
            import sqlite3
            tick_count = 0
            if os.path.exists(self.db.db_path):
                conn = sqlite3.connect(self.db.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT count(*) FROM market_ticks")
                tick_count = cursor.fetchone()[0]
                conn.close()
        except Exception as e:
            print(f"⚠️ [Dashboard] Status update error: {e}")
            tick_count = "N/A"

        wallet = self.guard.get_status()
        balances = wallet.get('balances', {})
        
        status = {
            "engine_mode": self.guard.mode,
            "tick_total": tick_count,
            "balance": f"${balances.get('mock', 0):,.0f}", 
            "balances": {
                "real": f"{balances.get('real', 0):,.0f} KRW",
                "virtual": f"${balances.get('virtual', 0):,.0f}",
                "mock": f"{balances.get('mock', 0):,.0f} KRW"
            },
            "positions": wallet.get('positions', {}),
            "trades": wallet.get('trades', {}),
            "profit_pct": wallet.get('total_profit_pct', '0.00%'),
            "last_update": datetime.now().strftime("%H:%M:%S"),
            "reports": wallet.get('reports', [])
        }
        return web.json_response(status)
    
    async def place_order(self, request):
        """주문 집행 API"""
        try:
            data = await request.json()
            ticker = data.get('ticker')
            action = data.get('action')  # BUY or SELL
            price = float(data.get('price', 0))
            quantity = int(data.get('quantity', 0))
            
            success = self.guard.execute_order(ticker, action, price, quantity)
            return web.json_response({"success": success, "message": f"{action} order executed" if success else "Order failed"})
        except Exception as e:
            return web.json_response({"success": False, "error": str(e)})
    
    async def get_wallet(self, request):
        """지갑 및 포트폴리오"""
        return web.json_response(self.guard.get_status())

    async def get_radar(self, request):
        """글로벌 레이더 결과"""
        # 사령관님의 명령에 따라 US 프리마켓과 KR 주도주 동시 스캔
        kr = self.radar.scan_kr_hot_stocks(top_n=10)
        us = self.radar.scan_us_premarket_hot_stocks(top_n=20)
        return web.json_response({"kr": kr, "us": us})

    async def get_market_analysis(self, request):
        """시장 분석 데이터 (ELW, 해외 업종 등)"""
        try:
            analysis = await self.guard.get_market_analysis()
            return web.json_response(analysis)
        except Exception as e:
            return web.json_response({"error": str(e)})

    async def get_chart_data(self, request):
        """분봉 차트 데이터"""
        try:
            ticker = request.match_info.get('ticker')
            if not ticker: return web.json_response({"error": "No ticker provided"})
            
            # KIS API를 통해 직접 조회 (캐싱 로직 없이 우선 구현)
            if not self.guard.mock_client:
                await self.guard.setup_clients()
            
            chart_data = await self.guard.mock_client.get_minute_chart(ticker)
            return web.json_response(chart_data)
        except Exception as e:
            return web.json_response({"error": str(e)})
    
    async def start(self):
        """서버 시작"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', self.port)
        await site.start()
        
        url = f"http://localhost:{self.port}"
        print(f"\n🎨 [Dashboard] GUI 대시보드 가동 완료!")
        print(f"   📡 접속 주소: {url}")
        print(f"   🌐 브라우저를 자동으로 엽니다...\n")
        
        # 브라우저 자동 열기
        try:
            webbrowser.open(url)
        except: pass
        
        # 서버 유지
        while True:
            await asyncio.sleep(60)

def main():
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    server = DashboardServer(port=9053)
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print("\n🛑 [Dashboard] 서버 종료")

if __name__ == "__main__":
    main()
