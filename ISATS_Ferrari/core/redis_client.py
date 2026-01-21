import redis.asyncio as redis
import os

class RedisClient:
    """
    [ISATS Ferrari Nervous System] 고속 신경망 클라이언트
    - 역할: Redis와 데이터를 주고받아 대시보드와 엔진을 연결
    """
    def __init__(self, host='localhost', port=6379, db=0):
        self.host = host
        self.port = port
        self.db = db
        self.client = None

    async def connect(self):
        if not self.client:
            self.client = redis.Redis(
                host=self.host, 
                port=self.port, 
                db=self.db, 
                decode_responses=True
            )
        return self.client

    async def ping(self):
        client = await self.connect()
        return await client.ping()

    async def get(self, key):
        client = await self.connect()
        return await client.get(key)

    async def set(self, key, value):
        client = await self.connect()
        await client.set(key, value)
