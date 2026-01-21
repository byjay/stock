import redis.asyncio as redis
import json
import asyncio
from datetime import datetime

class DataBroker:
    """
    [ISATS Core] In-Memory Data Broker
    역할: 수집된 데이터를 메모리(Redis)에 즉시 전송하고, 필요한 곳으로 배달(Pub/Sub)합니다.
    """
    def __init__(self, host='localhost', port=6379, db=0):
        self.redis_url = f"redis://{host}:{port}/{db}"
        self.redis = None
        self.pubsub = None

    async def connect(self):
        """Redis 서버 접속"""
        if not self.redis:
            self.redis = redis.from_url(self.redis_url, decode_responses=True)
            try:
                await self.redis.ping()
                print(f"⚡ [Broker] Redis 연결 성공: {self.redis_url}")
            except Exception as e:
                print(f"💀 [Broker] Redis 연결 실패: {e}")
                raise e

    async def publish_tick(self, symbol: str, data: dict):
        """
        주식 체결 데이터를 'market:tick' 채널로 송출
        """
        if not self.redis:
            await self.connect()
        
        # 데이터에 타임스탬프 추가
        data['broker_time'] = datetime.now().isoformat()
        message = json.dumps(data)
        
        # 1. Pub/Sub 채널로 쏘기 (실시간 감시용)
        await self.redis.publish(f"tick:{symbol}", message)
        
        # 2. Stream에 저장 (DB 저장 대기열 역할)
        # maxlen=10000: 메모리 보호를 위해 종목당 최신 1만 개만 유지
        await self.redis.xadd(f"stream:{symbol}", data, maxlen=10000)

    async def get_subscriber(self, channel_pattern: str):
        """특정 채널을 구독하는 리스너 반환"""
        if not self.redis:
            await self.connect()
        self.pubsub = self.redis.pubsub()
        await self.pubsub.psubscribe(channel_pattern)
        return self.pubsub

    async def close(self):
        if self.redis:
            await self.redis.close()
            print("💤 [Broker] Redis 연결 종료")
