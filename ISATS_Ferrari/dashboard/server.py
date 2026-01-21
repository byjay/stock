import asyncio
import json
import os
from aiohttp import web
import webbrowser
from pathlib import Path

# ==========================================
# 🎨 Ferrari GUI Dashboard Server
# ==========================================

class DashboardServer:
    def __init__(self, port=8080):
        self.port = port
        self.app = web.Application()
        self.setup_routes()
        
    def setup_routes(self):
        """라우트 설정"""
        self.app.router.add_get('/', self.serve_dashboard)
        self.app.router.add_get('/api/status', self.get_status)
        self.app.router.add_get('/api/positions', self.get_positions)
        
    async def serve_dashboard(self, request):
        """메인 대시보드 HTML 제공"""
        dashboard_path = Path(__file__).parent / "sniper_dragon_dashboard.html"
        
        if not dashboard_path.exists():
            return web.Response(text="Dashboard not found", status=404)
        
        with open(dashboard_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        return web.Response(text=html_content, content_type='text/html')
    
    async def get_status(self, request):
        """시스템 상태 API"""
        # 실제로는 Redis나 공유 메모리에서 가져옴
        status = {
            "engine_status": "RUNNING",
            "total_profit": "+15.2%",
            "active_positions": 3,
            "dna_generation": 5,
            "last_update": "2026-01-21 16:56:00"
        }
        return web.json_response(status)
    
    async def get_positions(self, request):
        """현재 포지션 API"""
        positions = [
            {"code": "005930", "name": "삼성전자", "qty": 10, "profit": "+5.2%"},
            {"code": "000660", "name": "SK하이닉스", "qty": 5, "profit": "+12.8%"},
            {"code": "035720", "name": "카카오", "qty": 15, "profit": "-2.1%"}
        ]
        return web.json_response(positions)
    
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
        webbrowser.open(url)
        
        # 서버 유지
        while True:
            await asyncio.sleep(3600)

def main():
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    server = DashboardServer(port=8080)
    asyncio.run(server.start())

if __name__ == "__main__":
    main()
