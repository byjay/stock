"""
[파일명]: backend/core/data_manager.py
[역할]: ISATS의 데이터 중앙 창고. 실시간 체결 데이터(Tick)를 수집하고 이를 차트 데이터(OHLCV)로 가공함.
[저장위치]: c:/Users/FREE/Desktop/주식/isats/backend/core/data_manager.py
[상세설명]:
이 모듈은 증권사로부터 들어오는 초당 수십 건의 체결 데이터를 메모리에 효율적으로 적재하고, 
1분/3분/5분 단위의 '캔들(Candle)' 데이터를 실시간으로 생성하여 StrategyEngine에 전달하는 중추적인 역할을 담당합니다.
메모리 최적화를 위해 특정 개수 이상의 데이터는 자동으로 정리하는 슬라이딩 윈도우 방식으로 동작합니다.
"""

import logging
import asyncio
from collections import defaultdict
import pandas as pd
from datetime import datetime
from backend.cloud.gcs_manager import GCSManager # [NEW] Persistence Link
import pandas as pd

logger = logging.getLogger("DataManager")

class DataManager:
    """
    실시간 시장 데이터의 수집, 가공 및 전파를 관리하는 클래스입니다.
    [Phase 35] Now powered by DataReactor (DuckDB) for persistence.
    """
    def __init__(self, broker=None, reactor=None):
        self.broker = broker
        # 실시간 틱(Tick) 데이터 저장소 (Memory Cache)
        self.ticks = defaultdict(list)
        # 가공된 분봉(OHLCV) 데이터 저장소
        self.ohlcv = {
            "1m": defaultdict(list),
            "3m": defaultdict(list),
            "5m": defaultdict(list)
        }
        self.gcs = GCSManager() 
        self.reactor = reactor # [Phase 35] DuckDB Engine

        # Legacy Support: TA Wrapper
        class TAWrapper:
            def __init__(self, dm):
                self.dm = dm
            def get_ohlcv(self, code, timeframe):
                return pd.DataFrame(self.dm.ohlcv.get(timeframe, {}).get(code, []))
        self.ta = TAWrapper(self)

    async def process_tick(self, tick_data: dict):
        """
        증권사 서버에서 전송된 1개의 틱(체결) 데이터를 처리합니다.
        """
        code = tick_data["code"]
        price = tick_data["price"]
        volume = tick_data["volume"]
        timestamp = tick_data["timestamp"]
        
        # 1. 원시 데이터 보관 (Memory + DB)
        self.ticks[code].append(tick_data)
        
        # [Phase 35] Push to Data Reactor (Buffered Insert)
        if self.reactor:
            self.reactor.insert_tick(code, price, volume, broker="KIS")

        # 2. 분봉 생성 및 업데이트
        if len(self.ticks[code]) % 2 == 0: 
             self._update_candle(code, price, volume)

    def _update_candle(self, code, price, volume):
        """
        수집된 틱 데이터를 기반으로 OHLCV(시/고/저/종) 캔들을 형성하고 전략 엔진을 트리거합니다.
        """
        if code not in self.ohlcv["1m"]:
            self.ohlcv["1m"][code] = []
        
        # 캔들 데이터 생성 (MVP 간소화)
        timestamp = datetime.now()
        candle = {
            "timestamp": timestamp,
            "code": code,
            "close": price,
            "open": price, 
            "high": price, 
            "low": price,  
            "volume": volume # Volume logic simplified for update
        }
        self.ohlcv["1m"][code].append(candle)
        
        # [Phase 35] Push Candle to Reactor (Persistence)
        if self.reactor:
            self.reactor.insert_candle(code, price, price, price, price, volume)

        # [Legacy] GCS for Visual Proof (Optional now that we have DB)
        # try:
        #     df = pd.DataFrame([candle])
        #     self.gcs.save_tick_data(code, df)
        # except Exception: pass
        
        # 메모리 관리: 최신 100개의 캔들만 유지 (슬라이딩 윈도우)
        if len(self.ohlcv["1m"][code]) > 100:
            self.ohlcv["1m"][code].pop(0)

    def get_latest_price(self, code: str):
        """현재가 조회"""
        if not self.ticks[code]:
            return None
        return self.ticks[code][-1]["price"]
