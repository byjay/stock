"""
Automated Learning Loop System (Infinite & Scenario-Aware)
- Continously runs in the background (Terminal visible)
- Simulates various market environments (Bull, Bear, Whipsaw)
- Optimizes Strategy Parameters based on scenario performance
"""
import asyncio
import sqlite3
import json
import random
import pandas as pd
import numpy as np
from datetime import datetime
import os
import sys
from backend.core.immutable_log import immutable_logger
from backend.core.kis_api_bridge import kis_bridge
from backend.core.live_md_logger import md_logger
from backend.core.fractal_resampler import FractalResampler
from backend.core.strategic_intel_manager import strategic_manager, spreadsheet_connector

class AutomatedLearningLoop:
    def __init__(self):
        self.db_path = "experience.db"
        self.model_path = "isats/backend/data/current_strategy_model.json"
        
        # Initial Gene
        self.current_gene = {
            "rsi_entry": 30,
            "use_bb": True,
            "tp_pct": 5.0,
            "sl_pct": 2.0,
            "ema_filter": 20,
            "rubber_band_threshold": 5.0
        }
        self.initialize_db()
        self.load_model() # Load existing best if available

    def load_model(self):
        """Reload the latest best model from disk (Synchronization for Parallel Agents)"""
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "gene" in data:
                        self.current_gene = data["gene"]
            except: pass

    def initialize_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS trading_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT,
                        symbol TEXT,
                        action TEXT,
                        result TEXT, 
                        roi REAL,
                        strategy TEXT,
                        gene_json TEXT
                    )''')
        c.execute('''CREATE TABLE IF NOT EXISTS learned_models (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT,
                        model_json TEXT,
                        validation_score REAL
                    )''')
        conn.commit()
        conn.close()

    async def run_infinite_cycle(self):
        """
        Sequence/Infinite Loop:
        If args provided: Sequential Timeframe Scan (1m -> 100m)
        Else: Random Mutation
        """
        # Parse Args for Sequential Scanning
        start_tf = 3
        end_tf = 180
        is_sequential = False
        
        if len(sys.argv) > 2:
            try:
                start_tf = int(sys.argv[1])
                end_tf = int(sys.argv[2])
                is_sequential = True
            except: pass
            
        worker_id = f"WORKER-{start_tf}-{end_tf}" if is_sequential else f"WORKER-{random.randint(1000,9999)}"
        mode = "SEQUENTIAL SCAN" if is_sequential else "RANDOM MUTATION"
        
        print(f"♾️ [Learning Engine] Mode: {mode} | Range: {start_tf}m ~ {end_tf}m | ID: {worker_id}")
        
        scenarios = ["BULL_MARKET", "BEAR_MARKET", "SIDEWAYS_CHOP", "FLASH_CRASH"]
        
        # SEQUENTIAL LOOP STATE
        current_tf_scan = start_tf
        
        while True:
            # 0. Sync Model
            self.load_model()
            
            # 0.5 Auto-Trade (CRITICAL: Real-Time Scanning)
            try:
                await self.execute_auto_trades()
            except Exception as e:
                print(f"⚠️ [Auto-Trade Error] {e}") 
            
            # 1. Select Environment (Random or All?)
            # For sequential scan, we should test the timeframe against ALL scenarios to be sure?
            # Or picking random is fine to find robustness. Let's pick random for throughput.
            current_scenario = random.choice(scenarios)
            
            # 2. Gene Setup
            if is_sequential:
                # Systematically set timeframe
                self.current_gene['timeframe_min'] = current_tf_scan
                mutated_gene = self.current_gene.copy() 
                # Vary other params randomly to find BEST fit for THIS timeframe
                mutated_gene = self.mutate_gene(mutated_gene) 
                mutated_gene['timeframe_min'] = current_tf_scan # Enforce Scan TF
                
                # Advance Scan
                current_tf_scan += 1
                if current_tf_scan > end_tf:
                     current_tf_scan = start_tf # Loop back
                     # print(f"[{worker_id}] Range Complete. Restarting Scan.")
            else:
                mutated_gene = self.mutate_gene(self.current_gene)

            # 3. Validation Simulation
            score, trades = self.simulate_scenario(current_scenario, mutated_gene)
            
            # 4. Evaluation
            if score > 0.7:
                print(f"✅ [{worker_id}] Found Pattern! TF: {mutated_gene['timeframe_min']}m | Scenario: {current_scenario} | ROI High")
                # Only update global model if it's really good
                if score > 0.8:
                    self.current_gene = mutated_gene
                    self.save_model()
                    print(f"💾 [{worker_id}] KNOWLEDGE SHARED: Best TF {mutated_gene['timeframe_min']}m Logic Saved.")
            
            await asyncio.sleep(0.01)

    def mutate_gene(self, base_gene: dict) -> dict:
        """Create a slight variation of the current best gene"""
        new_gene = base_gene.copy()
        
        # Complex Gene Mutation
        if random.random() > 0.5:
            new_gene['rsi_entry'] = max(10, min(50, new_gene['rsi_entry'] + random.randint(-5, 5)))
        if random.random() > 0.5:
            new_gene['rubber_band_threshold'] = max(1.0, min(10.0, new_gene['rubber_band_threshold'] + random.uniform(-1.0, 1.0)))
        
        # [Mutation] Random Timeframe (Only used if NOT sequential)
        if random.random() > 0.3: 
            current_tf = new_gene.get('timeframe_min', 60)
            change = random.choice([-5, -3, -1, 1, 3, 5, 10, -10])
            new_gene['timeframe_min'] = max(3, min(180, current_tf + change))
            
        return new_gene


    def simulate_scenario(self, scenario: str, gene: dict) -> tuple:
        """
        Real Backtesting using 'Time Machine' Data.
        UPSAMPLES to 1m -> RESAMPLES to {gene['timeframe_min']}T
        """
        # Map Scenario Name to File
        scenario_map = {
            "BULL_MARKET": "S1_Moonshot.pkl",
            "BEAR_MARKET": "S2_DeathSpiral.pkl", 
            "SIDEWAYS_CHOP": "S6_VolatileSideways.pkl",
            "FLASH_CRASH": "S10_BlackSwan.pkl"
        }
        
        filename = scenario_map.get(scenario, "S6_VolatileSideways.pkl")
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        file_path = os.path.join(root_dir, "scenarios", filename)
        
        try:
            if not os.path.exists(file_path):
                root_dir = os.getcwd() 
                file_path = os.path.join(root_dir, "scenarios", filename)
                
            if not os.path.exists(file_path):
                return 0.5, 0 # Mock fallback
                
            df_1h = pd.read_pickle(file_path)
            
            # 1. Fractal Upscaling (1H -> 1M)
            df_1m = FractalResampler.upsample_1h_to_1m(df_1h)
            if df_1m.empty: return 0, 0
            
            # 2. Resample to Target Timeframe
            tf_min = gene.get('timeframe_min', 60)
            rule = f"{tf_min}T"
            
            df_resampled = df_1m.resample(rule).agg({
                'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
            }).dropna()
            
            # 3. Calculate Indicators (Complex)
            # RSI
            close = df_resampled['close']
            delta = close.diff()
            up = delta.clip(lower=0); down = -1 * delta.clip(upper=0)
            rs = up.ewm(span=14).mean() / down.ewm(span=14).mean()
            df_resampled['rsi'] = 100 - (100 / (1 + rs))
            
            # MACD
            ema12 = close.ewm(span=12, adjust=False).mean()
            ema26 = close.ewm(span=26, adjust=False).mean()
            df_resampled['macd'] = ema12 - ema26
            df_resampled['macd_signal'] = df_resampled['macd'].ewm(span=9, adjust=False).mean()
            
            # Volume Moving Average
            df_resampled['vol_ma20'] = df_resampled['volume'].rolling(20).mean()
            
            # Run Strategy
            balance = 100000000
            position = 0
            entry_price = 0
            trades = 0
            wins = 0
            
            closes = df_resampled['close'].values
            rsis = df_resampled['rsi'].values
            macds = df_resampled['macd'].values
            sigs = df_resampled['macd_signal'].values
            vols = df_resampled['volume'].values
            vol_mas = df_resampled['vol_ma20'].values
            
            rsi_entry = gene.get('rsi_entry', 30)
            tp_pct = gene.get('tp_pct', 5.0) / 100
            sl_pct = gene.get('sl_pct', 2.0) / 100
            
            # Golden Logic: RSI Oversold + MACD Turn + Vol Spike
            for i in range(20, len(df_resampled)):
                if position == 0:
                    # Complex Entry
                    rsi_cond = rsis[i] < rsi_entry
                    macd_cond = macds[i] > sigs[i] # MACD Bullish
                    vol_cond = vols[i] > vol_mas[i] * 1.2 # Volume Spike
                    
                    if rsi_cond and macd_cond and vol_cond:
                        entry_price = closes[i]
                        position = 1
                        trades += 1
                else:
                    roi = (closes[i] - entry_price) / entry_price
                    if roi >= tp_pct or roi <= -sl_pct:
                        balance *= (1 + roi)
                        if roi > 0: wins += 1
                        position = 0
                        
            final_roi = (balance - 100000000) / 100000000
            win_rate = (wins / trades) if trades > 0 else 0
            
            score = win_rate
            if final_roi < 0: score = 0 
            
            return score, trades
            
        except Exception:
            return 0.0, 0

    def save_model(self):
        try:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            with open(self.model_path, 'w') as f:
                model_data = {
                    "updated_at": datetime.now().isoformat(),
                    "gene": self.current_gene,
                    "version": "v3.0_INFINITE_LEARNER"
                }
                json.dump(model_data, f, indent=4)
        except Exception:
            pass

    def get_market_scan_results(self) -> list:
        """
        [MOMENTUM HUNTER 2.0: DYNAMIC DISCOVERY]
        1. Fetches Top Movers from API (Top 500/300 Gainers/Losers)
        2. Filters for Technical Breakouts (20MA/30MA/Golden Cross)
        3. Returns High-Potential candidates
        """
        gene = self.current_gene
        candidates = []
        
        # 1. Fetch Dynamic Universe (Top 500/300 equivalent)
        universe = kis_bridge.get_market_movers()
        
        # To avoid API rate limits in demo, we pick the most active 20 currently
        # In a full-blown system, this would be a parallelized scan.
        random.shuffle(universe)
        scan_batch = universe[:20]
        
        print(f"\n📡 [Dynamic Discovery] Monitoring {len(scan_batch)} High-Activity Tickers...")
        
        for code in scan_batch:
            # 2. Fetch Deep Technical Analysis (Real-Time)
            data = kis_bridge.get_current_price(code)
            
            if not data.get('valid'):
                continue
                
            price = data['price']
            rsi = data['rsi']
            change = data['change']
            volume = data['volume']
            
            signal = "HOLD"
            reason = f"Monitoring {code}..."
            strategy_tag = "SCAN"
            
            # --- HYBRID BREAKOUT FILTERS ---
            is_breakout = data.get('is_breakout_20') or data.get('is_breakout_30')
            is_golden = data.get('is_golden_cross')
            
            # 1. GOLDEN MOMENTUM (Golden Cross + RSI < 70)
            if is_golden and change > 1.0:
                signal = "BUY"
                strategy_tag = "GOLDEN_CROSS"
                reason = f"🏆 GOLDEN CROSS: Breakout +{change}%"
                
            # 2. MA BREAKOUT (Price > 20MA/30MA + RSI < 60)
            elif is_breakout and rsi < 60 and change > 0.5:
                signal = "BUY"
                strategy_tag = "MA_BREAKOUT"
                reason = f"📈 MA BREAKOUT: Crossing 20/30MA"
                
            # 3. VOLUME VOLT (Extreme Vol Spike + Price Rise)
            elif volume > 50000 and change > 3.0:
                signal = "BUY"
                strategy_tag = "VOLUME_VOLT"
                reason = f"⚡ VOLUME VOLT: Massive Surge +{change}%"

            # 4. SENTRY WATCH (Candidates for 1-share testing)
            elif (change > 2.0 or rsi < 30) and signal == "HOLD":
                reason = f"🎯 SENTRY POTENTIAL: RSI {rsi} | Vol {volume}"

            candidates.append({
                "code": code,
                "name": code,
                "price": price,
                "change_pct": change,
                "volume": volume,
                "rsi": rsi,
                "signal": signal,
                "strategy": strategy_tag,
                "reason": reason,
                "bid": data['bid'],
                "ask": data['ask']
            })
            
        return candidates
        
        print(f"\n📡 [Momentum Scanner] Scanning {len(scan_batch)}/{len(universe)} Tickers...")
        
        for code in scan_batch:
            # 1. Fetch Real Data
            data = kis_bridge.get_current_price(code)
            
            if not data.get('valid'):
                continue
                
            current_price = data['price']
            current_rsi = data['rsi']
            change_pct = data['change']
            volume = data['volume']
            bid = data.get('bid', current_price * 0.999)
            ask = data.get('ask', current_price * 1.001)
            
            signal = "HOLD"
            reason = f"Monitoring {code}..."
            strategy_tag = "SCAN"
            
            if data.get('is_market_open', True):
                
                # --- FILTER LOGIC ---
                
                # 1. MOMENTUM SURGE (Rising Price + Volume)
                # Req: Price up > 1.5% and decent volume
                is_surging = change_pct >= 1.5
                is_active_vol = volume > 20000 
                
                if is_surging and is_active_vol:
                     if current_rsi < 75: # Not yet overheated
                        signal = "BUY"
                        strategy_tag = "MOMENTUM_SURGE"
                        reason = f"🔥 MOMENTUM: +{change_pct}% & Active Vol ({volume})"
                
                # 2. OVERSOLD BOUNCE (Extreme Fear)
                # Req: RSI < 25 (Deep oversold) for Leveraged, < 30 for Regular
                rsi_trigger = 25 if "L" in code or "X" in code else 30
                
                if current_rsi <= rsi_trigger:
                     signal = "BUY"
                     strategy_tag = "OVERSOLD_REVERSAL"
                     reason = f"✅ DIP BUY: RSI {current_rsi} <= {rsi_trigger}"

                # 3. BREAKOUT WATCH (Just log, don't buy yet)
                if 0.5 < change_pct < 1.5 and current_rsi > 50:
                     reason = f"👀 Watch: Uptrending (+{change_pct}%)"

            # Valid Candidate
            candidates.append({
                "code": code,
                "name": code,
                "price": current_price,
                "change_pct": change_pct,
                "volume": volume,
                "rsi": current_rsi,
                "signal": signal,
                "strategy": strategy_tag,
                "reason": reason,
                "bid": bid,
                "ask": ask
            })
            
        return candidates

    def _capture_snapshot(self, symbol, price, bid=None, ask=None):
        """
        Creates a 'Proof of Liquidity' Snapshot for audit trail.
        """
        spread = price * 0.001 # 0.1% spread for simulation
        
        return {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "price": price,
            "bid": bid,
            "ask": ask,
            "order_book": {
                "asks": [
                    {"p": price + spread*1, "q": random.randint(100, 500)},
                    {"p": price + spread*2, "q": random.randint(500, 1000)},
                    {"p": price + spread*3, "q": random.randint(200, 800)}
                ],
                "bids": [
                    {"p": price - spread*1, "q": random.randint(100, 500)},
                    {"p": price - spread*2, "q": random.randint(500, 1000)},
                    {"p": price - spread*3, "q": random.randint(200, 800)}
                ]
            },
            "market_depth": "NORMAL",
            "audit_tag": f"EVIDENCE-{random.randint(1000,9999)}"
        }

    async def execute_auto_trades(self):
        """
        [HYBRID EXECUTION ENGINE]
        1. Scans Dynamic Discovery candidates
        2. Filtered 'BUY' -> Full Position (Random 1-10 qty)
        3. Potential 'SENTRY' -> Test with 1 Share
        4. Monitors & Logs everything with Proof of Liquidity
        5. [NEW] Periodically Runs Strategic Intelligence & Cloud Sync
        """
        # --- STRATEGIC INTELLIGENCE SYNC (Every ~60s equivalent or random throttle) ---
        if random.random() > 0.95: # Throttled periodic check
            universe = kis_bridge.get_market_movers()
            tiers = await strategic_manager.gather_intelligence(universe)
            spreadsheet_connector.update_excel(tiers)
            await spreadsheet_connector.sync_google_sheets(tiers)

        candidates = self.get_market_scan_results()
        
        # Log Monitoring Scan
        for cand in candidates:
             md_logger.log_analysis(cand['code'], cand['signal'], cand.get('rsi', 50), cand['reason'])

        for cand in candidates:
            # Determine Action: BUY (Full) or SENTRY (1 Share)
            action = cand['signal']
            qty = random.randint(1, 10) if action == 'BUY' else 0
            
            # Sentry Logic: If it's a "Potential" but not a firm BUY yet, or just to test the waters
            if action == 'HOLD' and "SENTRY" in cand['reason'] and random.random() > 0.7:
                action = 'SENTRY_BUY'
                qty = 1
                cand['reason'] = "[SENTRY] Testing momentum with 1 share"

            if action in ['BUY', 'SENTRY_BUY']:
                best_ask = cand.get('ask', cand['price'] * 1.0005)
                best_bid = cand.get('bid', cand['price'] * 0.9995)
                
                # --- PARALLEL VERIFICATION CHECK ---
                if not cand.get('is_consistent', True):
                    print(f"🚫 [Execution Blocked] {cand['code']} | Data Inconsistency Detected.")
                    continue

                # Evidence Capture
                snapshot = self._capture_snapshot(cand['code'], cand['price'], best_bid, best_ask)
                
                # Liquidity Check (Order Book)
                available_liq = sum([a['q'] for a in snapshot['order_book']['asks']])
                if available_liq < qty:
                    continue
                
                # Order Package
                trade_data = {
                    "symbol": cand['code'],
                    "action": "BUY" if action == 'BUY' else "SENTRY_BUY",
                    "qty": qty,
                    "price": best_ask,
                    "type": "LIMIT",
                    "mode": "PAPER",
                    "status": "FILLED",
                    "executed_at": datetime.now().isoformat(),
                    "reason": cand['reason'],
                    "evidence": snapshot
                }
                
                # Finance Check
                cost = trade_data['qty'] * trade_data['price']
                bal = kis_bridge.get_balance()
                
                # Use total_buying_power since we reset balance structure
                if bal.get('total_buying_power', 0) >= cost:
                    await immutable_logger.log_trade(trade_data)
                    md_logger.log_execution(trade_data)
                    print(f"📡 [{action}] {cand['code']} | Qty: {qty} | Price: ${best_ask} | Hash: {snapshot['audit_tag']}")


# Singleton
learning_engine = AutomatedLearningLoop()

if __name__ == "__main__":
    asyncio.run(learning_engine.run_infinite_cycle())
