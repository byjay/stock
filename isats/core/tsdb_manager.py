import asyncpg
import asyncio
from datetime import datetime
import os

class TimeTravelerDB:
    """
    [ISATS Archive] 시계열 데이터 초고속 저장소 (TimescaleDB Manager)
    - 역할: Asyncpg를 사용하여 대량의 틱 데이터를 'Hypertable'에 고속 적재(Bulk Insert)
    """
    def __init__(self):
        # 환경 변수 또는 하드코딩된 접속 정보
        self.dsn = "postgres://postgres:isats_secret_password@localhost:5432/isats_market_data"
        self.pool = None

    async def connect(self):
        """Connection Pool 생성 및 초기화"""
        if not self.pool:
            try:
                self.pool = await asyncpg.create_pool(self.dsn)
                print("📚 [DB] TimescaleDB 연결 성공 (Pool Created)")
                await self.init_db_schema()
            except Exception as e:
                print(f"❌ [DB] 연결 실패 (Docker 확인 필요): {e}")
                raise e

    async def init_db_schema(self):
        """테이블 및 하이퍼테이블 자동 생성 (Idempotent)"""
        async with self.pool.acquire() as conn:
            # 1. 기본 테이블 생성
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS market_ticks (
                    time TIMESTAMPTZ NOT NULL,
                    code TEXT NOT NULL,
                    price DOUBLE PRECISION,
                    volume INTEGER,
                    change_rate DOUBLE PRECISION
                );
            """)
            
            # 2. TimescaleDB 하이퍼테이블 변환 (성능 핵심)
            # 이미 변환된 경우 에러가 날 수 있으므로 예외 처리
            try:
                await conn.execute("SELECT create_hypertable('market_ticks', 'time', if_not_exists => TRUE);")
                # 인덱스 추가 (조회 속도 향상)
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_code_time ON market_ticks (code, time DESC);")
                print("⚡ [DB] Hypertable 및 인덱스 설정 완료")
            except Exception as e:
                print(f"⚠️ [DB] 스키마 설정 중 알림: {e}")

    async def insert_bulk_ticks(self, ticks_data):
        """
        [핵심 기술] 대량 데이터 고속 삽입 (Bulk Insert)
        Args:
            ticks_data: list of tuples [(time, code, price, vol, change), ...]
        """
        if not self.pool:
            await self.connect()
            
        async with self.pool.acquire() as conn:
            try:
                # copy_records_to_table은 일반 insert보다 10배 이상 빠름
                await conn.copy_records_to_table(
                    'market_ticks',
                    records=ticks_data,
                    columns=['time', 'code', 'price', 'volume', 'change_rate']
                )
                print(f"💾 [DB] {len(ticks_data)}개 틱 데이터 저장 완료")
            except Exception as e:
                print(f"❌ [DB] 저장 실패: {e}")

    async def close(self):
        if self.pool:
            await self.pool.close()
            print("📕 [DB] 연결 종료")

# ==========================================
# [검증 모듈] 에이전트 자가 진단용
# ==========================================
if __name__ == "__main__":
    async def test_run():
        print("🚀 [System] DB 매니저 테스트 시작...")
        db = TimeTravelerDB()
        try:
            await db.connect()
            
            # 테스트용 더미 데이터 100개 생성
            dummy_data = []
            for i in range(100):
                dummy_data.append((
                    datetime.now(), 
                    "005930", 
                    70000 + i, 
                    10 + i, 
                    0.5
                ))
            
            # 저장 테스트
            await db.insert_bulk_ticks(dummy_data)
            print("✅ [Success] DB 연결 및 데이터 저장 성공.")
            
        except Exception as e:
            print(f"❌ [Fail] 테스트 실패: {e}")
        finally:
            await db.close()

    asyncio.run(test_run())
