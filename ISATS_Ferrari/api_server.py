import asyncio
import json
import os
import pandas as pd
import uvicorn
import redis.asyncio as redis
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# ==========================================
# ISATS WebSocket API Server
# 역할: Redis Pub/Sub 데이터를 WebSocket 클라이언트로 중계
# ==========================================

app = FastAPI(title="ISATS API Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

class ConnectionManager:
    """WebSocket 연결 관리 및 메시지 브로드캐스트 담당"""
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        # 연결된 모든 클라이언트에 메시지 전송
        for connection in self.active_connections[:]:
            try:
                await connection.send_text(message)
            except Exception:
                self.disconnect(connection)

manager = ConnectionManager()

@app.on_event("startup")
async def startup_event():
    # 백그라운드에서 Redis 리스너 실행
    asyncio.create_task(redis_listener())

async def redis_listener():
    """Redis 'isats_stream' 채널 구독 및 메시지 브로드캐스팅"""
    try:
        r = redis.from_url(REDIS_URL, decode_responses=True)
        pubsub = r.pubsub()
        await pubsub.subscribe("isats_stream")
        print("[API] Redis Connected. Listening for messages...")
        
        async for message in pubsub.listen():
            if message["type"] == "message":
                await manager.broadcast(message["data"])
    except Exception as e:
        print(f"[API Error] Redis Connection Failed: {e}")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 엔드포인트: 실시간 데이터 전송 채널"""
    await manager.connect(websocket)
    try:
        # 초기 접속 시 타겟 리스트 전송 (daily_target_list.csv 존재 시)
        target_path = "daily_target_list.csv"
        if os.path.exists(target_path):
            try:
                df = pd.read_csv(target_path)
                # 상위 20개 종목 정보 전송
                targets = df.head(20).to_dict(orient='records')
                await websocket.send_text(json.dumps({"type": "target_list", "data": targets}))
            except Exception as e:
                print(f"[API] Target list load error: {e}")

        # 연결 유지 루프 (클라이언트 메시지 수신 대기)
        while True:
            await websocket.receive_text()
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    # 윈도우 환경 대응 및 서버 기동
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="error")
