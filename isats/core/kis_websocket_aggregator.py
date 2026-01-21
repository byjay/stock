import asyncio
import json
import logging
import websockets
import datetime
from .kis_api_bridge import KisApiBridge

logger = logging.getLogger("KISAggregator")

class KISWebSocketAggregator:
    """
    High-Performance Data Collector.
    Spawns multiple WebSocket sessions to monitor 800+ stocks (40 per socket).
    """
    def __init__(self, bridge: KisApiBridge, master_aggregator):
        self.bridge = bridge
        self.master = master_aggregator
        self.approval_key = None
        self.ws_uri = "ws://ops.koreainvestment.com:21000" if not bridge.mock_mode else "ws://localhost:8001/ws/mock"
        self.is_running = False
        self.active_sessions = []
        self.symbol_batches = []

    async def prepare_batches(self, symbols, batch_size=40):
        """Splits 800 symbols into 20 batches of 40."""
        self.symbol_batches = [symbols[i:i + batch_size] for i in range(0, len(symbols), batch_size)]
        logger.info(f"Aggregator: Split {len(symbols)} symbols into {len(self.symbol_batches)} WebSocket batches.")

    async def start(self, symbols):
        self.is_running = True
        await self.prepare_batches(symbols)
        
        # If real mode, get approval key
        if not self.bridge.mock_mode:
            # Note: This requires real app_key/secret in the bridge
            # self.approval_key = self.bridge.get_approval_key()
            self.approval_key = "MOCK_APPROVAL_KEY" 
        
        tasks = []
        for i, batch in enumerate(self.symbol_batches):
            tasks.append(self.run_socket_session(i, batch))
        
        await asyncio.gather(*tasks)

    async def run_socket_session(self, session_id, symbols):
        """Manages a single WebSocket connection for a batch of symbols."""
        logger.info(f"Session {session_id}: Connecting for {len(symbols)} symbols...")
        
        retry_count = 0
        while self.is_running:
            try:
                async with websockets.connect(self.ws_uri, ping_interval=None) as ws:
                    # 1. Subscribe to each symbol in the batch
                    for sym in symbols:
                        subscribe_pkt = {
                            "header": {
                                "approval_key": self.approval_key,
                                "custtype": "P",
                                "tr_type": "1",
                                "content-type": "utf-8"
                            },
                            "body": {
                                "input": {
                                    "tr_id": "H0STCNT0", # Real-time execution price
                                    "tr_key": sym
                                }
                            }
                        }
                        await ws.send(json.dumps(subscribe_pkt))
                        await asyncio.sleep(0.1) # Handshake delay
                    
                    logger.info(f"Session {session_id}: Subscribed to all {len(symbols)} symbols.")

                    # 2. Main Receive Loop
                    while self.is_running:
                        data = await ws.recv()
                        
                        # Handle PING-PONG
                        if "PINGPONG" in data:
                            await ws.pong(data)
                            continue

                        # Handle Data (Format: 0|H0STCNT0|001|SYMBOL^TIME^PRICE^...)
                        if data.startswith("0"):
                            parts = data.split('|')
                            if len(parts) >= 4:
                                tick_data = parts[3].split('^')
                                symbol = tick_data[0]
                                price = float(tick_data[2])
                                volume = int(tick_data[12])
                                
                                # Push to Master Aggregator
                                await self.master.broadcast_tick(symbol, price, volume)

            except Exception as e:
                logger.error(f"Session {session_id} Error: {e}. Retrying in 5s...")
                await asyncio.sleep(5)
                retry_count += 1
                if retry_count > 10: break

    def stop(self):
        self.is_running = False
