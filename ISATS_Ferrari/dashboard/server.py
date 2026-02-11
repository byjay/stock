# -*- coding: utf-8 -*-
"""
ISATS Dashboard Server - Heavy Duty Edition (v94-B)
Industrial Brutalist Intelligence Matrix
"""

import sys
import os
import asyncio
import json
import logging
import pandas as pd
from aiohttp import web
from pathlib import Path
from datetime import datetime
import redis.asyncio as redis

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from core.kis_official_api import KISUnifiedClient
from virtual_trading_engine import VirtualWallet
from core.macro_sentinel import MacroSentinel
from core.ultra_intelligence_engine import UltraIntelligenceEngine

class DashboardServer:
    def __init__(self, port=9053):
        self.port = port
        self.app = web.Application()
        self.kis_virtual = KISUnifiedClient(mode="virtual")
        self.wallet = VirtualWallet()
        self.macro = MacroSentinel()
        self.engine = UltraIntelligenceEngine()
        self.redis = None
        self.intelligence_cache = {} # Ticker -> Last Analysis
        
        self.setup_routes()
        
    def setup_routes(self):
        self.app.router.add_get('/', self.serve_dashboard)
        self.app.router.add_get('/api/status', self.get_system_status)
        self.app.router.add_get('/api/balance', self.get_all_balances)
        self.app.router.add_get('/api/macro', self.get_macro_status)
        self.app.router.add_get('/api/virtual/wallet', self.get_virtual_wallet)
        self.app.router.add_get('/api/logs', self.get_trading_logs)
        self.app.router.add_get('/api/market/radar', self.get_market_radar)
        self.app.router.add_get('/api/intelligence/{ticker}', self.get_ticker_intelligence)
        self.app.router.add_get('/api/chart/{market}/{ticker}', self.get_chart_data)
        self.app.router.add_get('/api/system/telemetry', self.get_system_telemetry)
        self.app.router.add_get('/api/system/health', self.get_system_health)

    async def serve_dashboard(self, request):
        path = Path(__file__).parent / "mts_supreme_v4_ultimate.html"
        with open(path, 'r', encoding='utf-8') as f:
            return web.Response(text=f.read(), content_type='text/html')

    async def get_chart_data(self, request):
        market = request.match_info['market']
        ticker = request.match_info['ticker']
        # 차트 데이터 반환 (구현 필요)
        return web.json_response({"ticker": ticker, "market": market, "data": []})

    async def get_system_telemetry(self, request):
        return web.json_response({"cpu": 0, "memory": 0, "uptime": "0s"})

    async def get_system_health(self, request):
        return web.json_response({"status": "healthy", "services": {"scanner": "active", "trader": "active"}})

    async def get_system_status(self, request):
        return web.json_response({"status": "HEAVY_DUTY_ONLINE", "time": datetime.now().isoformat()})

    async def get_all_balances(self, request):
        self.wallet._load_state()
        return web.json_response({"virtual": {"total": self.wallet.get_total_value({}), "cash": self.wallet.cash}})

    async def get_macro_status(self, request):
        await self.macro.scan_global_market()
        return web.json_response({"score": self.macro.risk_score, "status": self.macro.market_status, "indicators": self.macro.indicators})

    async def get_virtual_wallet(self, request):
        self.wallet._load_state()
        enriched = {}
        for t, p in self.wallet.positions.items():
            try:
                price_info = self.kis_virtual.get_price(t, market=p.get("market", "KR"))
                p["current_price"] = float(price_info.get("stck_prpr", price_info.get("last", p["avg_price"])))
                p["profit_pct"] = round(((p["current_price"] / p["avg_price"]) - 1) * 100, 2)
            except:
                p["current_price"] = p["avg_price"]; p["profit_pct"] = 0
            enriched[t] = p
        return web.json_response({"positions": enriched, "cash": self.wallet.cash})

    async def get_trading_logs(self, request):
        log_file = Path(ROOT_DIR) / "logs" / f"trading_{datetime.now().strftime('%Y%m%d')}.log"
        if not log_file.exists(): return web.json_response({"logs": []})
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            return web.json_response({"logs": lines[-40:]})

    async def get_ticker_intelligence(self, request):
        ticker = request.match_info['ticker']
        analysis = await self.engine.analyze(ticker, ticker)
        return web.json_response(analysis)

    async def get_market_radar(self, request):
        target_file = Path(ROOT_DIR) / "daily_target_list.csv"
        if not target_file.exists(): return web.json_response([])
        df = pd.read_csv(target_file)
        return web.json_response(df.to_dict(orient="records"))

    async def redis_listener(self):
        """Subscribes to intelligence broadcasts from the launcher"""
        try:
            self.redis = await redis.from_url("redis://localhost", decode_responses=True)
            pubsub = self.redis.pubsub()
            await pubsub.subscribe("isats_intelligence")
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    data = json.loads(message['data'])
                    self.intelligence_cache[data['ticker']] = data
        except: pass

    async def keep_alive_task(self):
        """Ping KBJ2 Orchestrator every 14 minutes to prevent sleep."""
        url = "https://kbj2-orchestrator.onrender.com"
        print(f"⏰ Keep-Alive System Activated: Pinging {url} every 14 mins")
        import aiohttp
        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    async with session.get(url) as resp:
                        print(f"💓 Ping sent to KBJ2. Status: {resp.status}")
                except Exception as e:
                    print(f"⚠️ Keep-Alive Ping Failed: {e}")
                await asyncio.sleep(14 * 60)

    async def start(self):
        asyncio.create_task(self.redis_listener())
        asyncio.create_task(self.keep_alive_task()) # Start Keep-Alive
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        # Render/Cloud environment support: bind to 0.0.0.0 and use PORT env var
        host = '0.0.0.0'
        port = int(os.environ.get('PORT', self.port))
        
        site = web.TCPSite(runner, host, port)
        await site.start()
        print(f"🚀 Scuderia Terminal active at: http://{host}:{port}")
        while True: await asyncio.sleep(3600)

if __name__ == "__main__":
    if os.name == 'nt': asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    server = DashboardServer()
    asyncio.run(server.start())
