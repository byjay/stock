import asyncio
import random
import datetime
import os
import json
import logging
import pandas as pd
from collections import deque
from .sector_mapper import get_sector_map
from .kis_websocket_aggregator import KISWebSocketAggregator
from .kis_api_bridge import kis_bridge

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s')
logger = logging.getLogger("HybridSwarmHQ")

class GlobalSignalBus:
    """
    The Communication Hub: Allows 800 agents to share 'Sector Intelligence' 
    and 'Expert Sentiment' (Qualitative).
    """
    def __init__(self, sector_map):
        self.active_signals = [] 
        self.expert_signals = {} # Symbol -> Sentiment Data
        self.sector_map = sector_map

    def publish_signal(self, sender_symbol, signal_type, data):
        """Called by Workers or CafeMiner."""
        if signal_type == "EXPERT_SENTIMENT":
            self.expert_signals[sender_symbol] = {
                "timestamp": datetime.datetime.now(),
                "data": data
            }
            logger.info(f"💡 BUS: Expert Sentiment Logged for {sender_symbol}")
            return

        entry = {
            "timestamp": datetime.datetime.now(),
            "symbol": sender_symbol,
            "sector": self.sector_map.get(sender_symbol, "UNKNOWN"),
            "type": signal_type,
            "data": data
        }
        self.active_signals.append(entry)
        # Keep only the last 5 minutes of swarm signals
        cutoff = datetime.datetime.now() - datetime.timedelta(minutes=5)
        self.active_signals = [s for s in self.active_signals if s["timestamp"] > cutoff]

    def get_related_signals(self, target_symbol):
        """Returns signals (Swarm + Expert) that might impact this target."""
        target_sector = self.sector_map.get(target_symbol, "UNKNOWN")
        sector_signals = [s for s in self.active_signals if s["sector"] == target_sector]
        
        # Expert Sentiment Check (Qualitative)
        expert_data = self.expert_signals.get(target_symbol)
        if expert_data:
            # If expert sentiment is fresh (< 24 hours), it's a permanent booster
            if (datetime.datetime.now() - expert_data["timestamp"]).total_seconds() < 86400:
                # We return a synthetic signal for the worker to react
                sector_signals.append({
                    "type": "EXPERT_BOOSTER",
                    "data": expert_data["data"]
                })
        
        return sector_signals

class DataAggregator:
    """
    MASTER NODE: High-speed data distributor.
    """
    def __init__(self):
        self.workers = {}
        self.is_running = False
        self.total_ticks_processed = 0

    def register_worker(self, worker):
        self.workers[worker.symbol] = worker

    async def broadcast_tick(self, symbol, price, volume):
        if symbol in self.workers:
            asyncio.create_task(self.workers[symbol].process_tick(price, volume))
            self.total_ticks_processed += 1

    async def run_data_hose(self):
        logger.info("MASTER: Aggregator Hose Starting...")
        while self.is_running:
            symbols = list(self.workers.keys())
            if not symbols: 
                await asyncio.sleep(1)
                continue
            batch = random.sample(symbols, min(50, len(symbols)))
            for s in batch:
                price = 1000 * (1 + random.uniform(-0.01, 0.01))
                volume = random.randint(10, 1000)
                await self.broadcast_tick(s, price, volume)
            await asyncio.sleep(0.01)

class ShadowWorker:
    """
    SLAVE NODE: Hybrid Intelligence Analyst.
    """
    def __init__(self, symbol, hq, timeframe_min=30):
        self.symbol = symbol
        self.hq = hq 
        self.tf = timeframe_min
        self.candles = deque(maxlen=300)
        self.current_candle = {"open": 0, "high": 0, "low": 0, "close": 0, "vol": 0, "start": None}
        self.status = "IDLE"
        self.prediction = None
        self.resonance_weight = 1.0

    async def process_tick(self, price, volume):
        now = datetime.datetime.now()
        if not self.current_candle["start"]:
            self.current_candle.update({"open": price, "high": price, "low": price, "start": now})
        self.current_candle["high"] = max(self.current_candle["high"], price)
        self.current_candle["low"] = min(self.current_candle["low"], price)
        self.current_candle["vol"] += volume
        self.current_candle["close"] = price
        if (now - self.current_candle["start"]).total_seconds() / 60 >= self.tf:
            self.candles.append(self.current_candle.copy())
            self.current_candle = {"open": price, "high": price, "low": price, "vol": 0, "start": now}
            await self.analyze_and_predict()

    async def analyze_and_predict(self):
        if len(self.candles) < 20: return
        closes = [c['close'] for c in self.candles]
        last_close = closes[-1]
        ma20 = sum(closes[-20:]) / 20
        
        # Fast RSI
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        gains = [d if d > 0 else 0 for d in deltas[-14:]]
        losses = [-d if d < 0 else 0 for d in deltas[-14:]]
        avg_gain = sum(gains)/14; avg_loss = sum(losses)/14 if sum(losses)>0 else 0.0001
        rsi = 100 - (100 / (1 + avg_gain/avg_loss))

        # --- HYBRID TRIGGER LOGIC ---
        signals = self.hq.bus.get_related_signals(self.symbol)
        
        # 1. Quant Swarm Resonance
        swarm_boost = min(len([s for s in signals if s.get("type") == "GOLDEN_TEMPLATE"]), 5) * 0.1
        
        # 2. Expert Sentiment Booster (Qualitative)
        expert_boost = 0.5 if any(s.get("type") == "EXPERT_BOOSTER" for s in signals) else 0.0
        
        self.resonance_weight = 1.0 + swarm_boost + expert_boost
        gene_rsi = self.hq.best_gene.get("rsi_entry", 30) * self.resonance_weight

        if rsi < gene_rsi and last_close > ma20:
            if self.status != "MONITORING":
                self.status = "MONITORING"
                self.prediction = {
                    "entry_price": last_close, "target": last_close*1.03, "stop": last_close*0.98,
                    "reason": "EXPERT_QUANT_HYBRID" if expert_boost > 0 else "SWARM_RESURGENCE",
                    "resonance": self.resonance_weight
                }
                self.hq.bus.publish_signal(self.symbol, "GOLDEN_TEMPLATE", {"rsi": rsi})
                logger.info(f"🚀 [{self.symbol}] HYBRID TRIGGER (Resonance: {self.resonance_weight:.2f}, Expert: {'YES' if expert_boost>0 else 'NO'})")

        if self.status == "MONITORING" and self.prediction:
            if last_close >= self.prediction["target"]:
                logger.info(f"✅ [{self.symbol}] Target Hit. Logic Validated.")
                self.log_result("SUCCESS", last_close)
                self.status = "IDLE"
            elif last_close <= self.prediction["stop"]:
                logger.warning(f"❌ [{self.symbol}] Stop Loss. Initiating Failure Analysis.")
                self.log_result("FAILURE", last_close)
                self.status = "IDLE"

    def log_result(self, result, exit_price):
        log_dir = os.path.join("data", "shadow_history")
        if not os.path.exists(log_dir): os.makedirs(log_dir)
        log_path = os.path.join(log_dir, f"{self.symbol}_results.json")
        try:
            entry_data = {
                "timestamp": str(datetime.datetime.now()),
                "symbol": self.symbol,
                "tf": self.tf,
                "entry": self.prediction["entry_price"],
                "exit": exit_price,
                "pnl_pct": ((exit_price - self.prediction["entry_price"]) / self.prediction["entry_price"]) * 100,
                "result": result,
                "reason": self.prediction["reason"],
                "resonance": self.prediction.get("resonance", 1.0)
            }
            logs = []
            if os.path.exists(log_path):
                with open(log_path, 'r') as f:
                    try: logs = json.load(f)
                    except: logs = []
            logs.append(entry_data)
            with open(log_path, 'w') as f:
                json.dump(logs, f, indent=4)
        except Exception as e:
            logger.error(f"Error logging shadow result for {self.symbol}: {e}")

class DistributedSurveillanceHQ:
    """
    COMMAND CENTER: Orchestrates Aggregator, Bus, Synergy Engine, and Workers.
    """
    def __init__(self, n=500):
        self.aggregator = DataAggregator()
        self.ws_aggregator = KISWebSocketAggregator(kis_bridge, self.aggregator)
        from .synergy_filter_engine import SynergyFilterEngine
        self.synergy_engine = SynergyFilterEngine(self)
        self.num_workers = n
        self.best_gene = {"rsi_entry": 30}
        self.is_running = False

    def deploy_squad(self):
        logger.info(f"HQ: Deploying {self.num_workers} Parallel Analysts...")
        symbols = [f"S{i:04d}" for i in range(self.num_workers)]
        self.sector_map = get_sector_map(symbols)
        self.bus = GlobalSignalBus(self.sector_map)
        for s in symbols:
            worker = ShadowWorker(s, self, timeframe_min=random.choice([3, 10, 15, 30]))
            self.aggregator.register_worker(worker)
        logger.info("HQ: Squad Deployed & Hybrid Knowledge Bus Connected.")
        return symbols

    async def start(self):
        symbols = self.deploy_squad()
        self.is_running = True
        self.aggregator.is_running = True
        await asyncio.gather(
            self.aggregator.run_data_hose() if kis_bridge.mock_mode else self.ws_aggregator.start(symbols),
            self.monitor_performance(),
            self.poll_cafe_intelligence(),
            self.run_ultra_filter_loop() # High-Yield Selection Task
        )

    async def run_ultra_filter_loop(self):
        """[FIXED] Trade Tracking + Existing RiskManager"""
        from .trade_tracker import trade_tracker
        from .kis_api_bridge import kis_bridge
        from .risk_manager import RiskManager
        
        risk_mgr = RiskManager()
        logger.info("⚠️ Ultra Filter Loop Started with RiskManager")
        
        while self.is_running:
            await asyncio.sleep(30)
            
            # 1. 활성 거래 체크 및 손절 실행
            try:
                active_trades = trade_tracker.get_active_trades()
                if active_trades:
                    price_data = {}
                    for trade in active_trades:
                        symbol = trade['symbol']
                        data = kis_bridge.get_current_price(symbol)
                        if data and data.get('valid'):
                            current_price = data['price']
                            entry_price = trade['entry_price']
                            
                            # 손익률 계산
                            pnl_pct = ((current_price - entry_price) / entry_price) * 100
                            
                            # 손절/익절 체크 (NORMAL 모드 기준: +3%/-2%)
                            should_exit = False
                            reason = ""
                            
                            if pnl_pct <= -2.0:
                                should_exit = True
                                reason = f"STOP_LOSS ({pnl_pct:.2f}%)"
                            elif pnl_pct >= 3.0:
                                should_exit = True
                                reason = f"TAKE_PROFIT ({pnl_pct:.2f}%)"
                            
                            if should_exit:
                                logger.warning(f"❌ [AUTO-SELL] {symbol} @ ${current_price:.2f} | {reason}")
                                trade_tracker.close_trade(trade['trade_id'], current_price)
                                risk_mgr.record_exit(symbol, current_price, reason, datetime.now())
                            
                            price_data[symbol] = {'price': current_price, 'volume': 0, 'rsi': 0}
                    
                    # 스냅샷 업데이트
                    trade_tracker.update_all_snapshots(price_data)
                    
            except Exception as e:
                logger.error(f"Error in risk check: {e}")
            
            # 2. 새 매수 후보 선정
            targets = await self.synergy_engine.select_ultra_targets()
            
            # 3. 매수 실행 (제한적)
            if targets:
                current_positions = len(trade_tracker.get_active_trades())
                
                if current_positions >= 3:
                    logger.warning(f"⚠️ Max positions ({current_positions}/3). Skipping.")
                    continue
                
                for target in targets[:1]:
                    try:
                        symbol = target.get('ticker', 'UNKNOWN')
                        price = target.get('price', 0)
                        score = target.get('score', 0)
                        
                        if price > 0 and score >= 70:
                            trade_id = trade_tracker.record_buy(
                                symbol=symbol,
                                entry_price=price,
                                strategy="CONSERVATIVE",
                                strategy_score=score
                            )
                            logger.info(f"🚀 [BUY] {symbol} @ ${price} (Score: {score})")
                    except Exception as e:
                        logger.error(f"Error: {e}")

    async def poll_cafe_intelligence(self):
        """Periodically syncs signals from the Cafe Repository to the Live Bus."""
        from .cafe_repository_manager import cafe_repo
        logger.info("HQ: Cafe Intelligence Polling Started.")
        while self.is_running:
            try:
                # Get signals from the last 1 hour
                recent_signals = cafe_repo.get_recent_signals(hours=1)
                for sig in recent_signals:
                    # Translate signal to Bus format
                    self.bus.publish_signal(
                        sig["ticker"] or f"UNKNOWN_{sig['symbol_name']}", 
                        "EXPERT_SENTIMENT", 
                        {"reason": sig["reasoning"], "source": "CafeDB"}
                    )
            except Exception as e:
                logger.error(f"Error polling cafe intelligence: {e}")
            
            await asyncio.sleep(60) # Sync every minute

    async def monitor_performance(self):
        while self.is_running:
            await asyncio.sleep(10)
            processed = self.aggregator.total_ticks_processed
            logger.info(f"📊 HYBRID SWARM PERFORMANCE: {processed} Ticks Across {self.num_workers} Workers.")

if __name__ == "__main__":
    hq = DistributedSurveillanceHQ(800)
    try: asyncio.run(hq.start())
    except KeyboardInterrupt: logger.info("HQ: Shutdown initiated.")
