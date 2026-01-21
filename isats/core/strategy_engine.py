"""
[파일명]: backend/core/strategy_engine.py
[역할]: ISATS 시스템의 핵심 지휘소(Control Center). 모든 매매 전략을 통합 실행하고 최종 BUY/SELL 신호를 확정함.
[저장위치]: c:/Users/FREE/Desktop/주식/isats/backend/core/strategy_engine.py
[상세설명]:
이 소스코드는 주식 시장의 실시간/과거 데이터를 입력받아 등록된 다양한 전략(트리플 컨퍼메이션, N패턴, 스파이크 스캘핑 등)에 
전달하고, 발생한 신호를 RiskManager(위험 관리)와 GeminiAdvisor(AI 판단)를 통해 최종적으로 정제하는 핵심 오케스트레이터입니다.
이 파일은 어떤 외부 인프라와 연결되어도 신호를 일관되게 생성할 수 있도록 추상화되어 설계되었습니다.
"""

from typing import List, Dict
import pandas as pd
import logging

# 전략 및 엔진에 필요한 모듈들 임포트
from backend.strategies.base import BaseStrategy
from backend.strategies.triple_confirmation import TripleConfirmationStrategy
from backend.core.ta_lib_wrapper import TAWrapper
from backend.ai.gemini_advisor import GeminiAdvisor
from backend.strategies.n_pattern import NPatternStrategy
from backend.strategies.spike_scalping import SpikeScalpingStrategy
from backend.strategies.inverse_strategy import InverseScalpingStrategy
from backend.strategies.jongga_betting import JonggaBettingStrategy
from backend.strategies.rubber_band import RubberBandStrategy # [NEW]
from backend.strategies.put_option_strategy import PutOptionStrategy # [NEW - BEAR]
from backend.strategies.call_option_strategy import CallOptionStrategy # [NEW - BULL]
from backend.core.risk_manager import RiskManager
from backend.core.regime_detector import RegimeDetector # [NEW]
from backend.core.watchdog import SystemWatchdog       # [NEW]
from backend.core.universe_manager import UniverseManager # [Phase J]
from backend.core.parameter_manager import ParameterManager # [Consolidation NEW]

logger = logging.getLogger("StrategyEngine")

MAX_DAILY_TRADES = 10
TARGET_PROFIT = 0.03
STOP_LOSS = 0.02

class StrategyEngine:
    """
    모든 알고리즘 전략의 로직 실행과 필터링을 총괄하는 메인 엔진 클래스입니다.
    """
    def __init__(self):
        self.strategies: List[BaseStrategy] = []
        self.active_signals: Dict[str, dict] = {} # {종목코드: 신호데이터}
        self.ai_advisor = GeminiAdvisor() # AI 시니어 파트너 제미나이 초기화
        self.risk_manager = RiskManager() # 손절 및 쿨다운 관리자 초기화
        self.regime_detector = RegimeDetector() # [NEW] 시장 체질 분석기
        self.watchdog = SystemWatchdog()        # [NEW] 시스템 파수꾼
        self.universe_manager = UniverseManager() # [Phase J] 유니버스 관리자
        self.param_manager = ParameterManager()   # [Consolidation NEW] 딥러닝 파라미터 관리자
        
        # [FIX] Initialize State Variables
        self.today_date = None
        self.daily_trade_count = 0
        
        # 가용한 전략들을 엔진에 등록 (여기에 새로운 전략 파일이 생기면 추가함)
        self.register_strategy(TripleConfirmationStrategy()) # 3중 확정 전략
        self.register_strategy(NPatternStrategy())           # N자 눌림목 전략
        self.register_strategy(SpikeScalpingStrategy())     # 스나이퍼 급등주 스캘핑
        self.register_strategy(InverseScalpingStrategy())   # 하락장 대비 인버스 전략
        self.register_strategy(JonggaBettingStrategy())     # 종가 배팅 전략 (오후 3시 타점)
        self.register_strategy(RubberBandStrategy())        # [NEW] 러버밴드 역추세 전략
        
        # [NEW] Option Strategies (Market Regime Based)
        self.put_strategy = PutOptionStrategy()   # BEAR 시장 풋옵션 (1천~5천원, 최대 30%)
        self.call_strategy = CallOptionStrategy() # BULL 시장 콜옵션 (최대 1천만원)

        # [Consolidation] Apply DL Parameters to Strategies
        self._apply_dl_parameters()

        self.STRICT_MODE = True # [Phase 3] Default Enable


    def _apply_dl_parameters(self):
        """[Consolidation] Injects deep learning results into registered strategies."""
        best_gene = self.param_manager.get_best_gene()
        if best_gene:
            logger.info(f"🧬 [DL-INJECTION] Applying Best Gene to Strategies: {best_gene}")
            # Target specific strategies if needed, or broadcast global settings
            # Example: Update TripleConfirmation if window matches
            for strat in self.strategies:
                if hasattr(strat, 'ma_window'):
                    strat.ma_window = best_gene['ma_window']
                if hasattr(strat, 'vol_threshold'):
                    strat.vol_threshold = best_gene['vol_threshold']

    def run_morning_routine(self):
        """
        [Phase J] 08:30 Morning Routine
        """
        initial_watchlist = self.universe_manager.run_premarket_scan()
        logger.info(f"☀️ Morning Routine Complete. Engine focused on {len(initial_watchlist)} targets.")
        return initial_watchlist
        
    def _check_strict_filters(self, df: pd.DataFrame) -> bool:
        """
        [Phase 3] Triple Confirmation Strict Filter
        1. BB: Price > Upper Band (Strong Momentum)
        2. MACD: MACD > Signal (Bullish)
        3. RSI: 50 < RSI < 70 (Healthy Trend)
        4. Volume: Vol > 20MA * 1.5 (Significant Interest)
        """
        if len(df) < 20: return False
        
        last = df.iloc[-1]
        
        # 1. BB Check
        bb_pass = last['close'] >= last.get('BB_upper', 99999999) # If usage error, fail safe
        
        # 2. MACD Check
        macd_pass = last.get('MACD', 0) > last.get('MACD_signal', 0)
        
        # 3. RSI Check (Healthy Zone)
        rsi = last.get('RSI_14', 50)
        rsi_pass = 50 <= rsi <= 75 # Slightly relaxed upper bound for crypto/volatile stocks
        
        # 4. Volume Check
        vol_ma20 = df['volume'].rolling(20).mean().iloc[-1]
        vol_pass = last['volume'] > (vol_ma20 * 1.5)
        
        logger.debug(f"[StrictCheck] BB:{bb_pass} MACD:{macd_pass} RSI:{rsi_pass}({rsi:.1f}) VOL:{vol_pass}")
        
        return bb_pass and macd_pass and rsi_pass and vol_pass

    def register_strategy(self, strategy: BaseStrategy):
        self.strategies.append(strategy)
        logger.info(f"Registered Strategy: {strategy.name}")

    def check_market_phase(self, df: pd.DataFrame) -> str:
        """
        Determines if market is BULL or BEAR based on 20MA.
        If current price > 20MA -> BULL (Aggressive)
        If current price < 20MA -> BEAR (Defensive)
        """
        if len(df) < 20: return "NEUTRAL"
        
        ma20 = df['close'].rolling(20).mean().iloc[-1]
        current_price = df['close'].iloc[-1]
        
        phase = "BULL" if current_price > ma20 else "BEAR"
        logger.debug(f"[MarketPhase] Price: {current_price:.2f}, MA20: {ma20:.2f} -> {phase}")
        return phase

    async def evaluate(self, code: str, df: pd.DataFrame, context: Dict[str, pd.DataFrame] = None) -> List[dict]:
        """Runs all strategies against the latest data for a specific stock code."""
        if context is None:
            context = {}
        if df.empty:
            return []
            
        # 0. Check Daily Trade Limit (Partner Constraint)
        current_date = df['datetime'].iloc[-1].date()
        if self.today_date != current_date:
            self.today_date = current_date
            self.daily_trade_count = 0 # Reset counter on new day
            
        if self.daily_trade_count >= MAX_DAILY_TRADES:
            logger.warning(f"⛔ [RISK] Daily Trade Limit Reached ({MAX_DAILY_TRADES}). Skipping {code}.")
            return []

        # 1. Check Global Regime & Resource Health (Anti-Fragility)
        regime = self.regime_detector.analyze_regime(df) # In production, use Index DF (KOSPI)
        if not self.regime_detector.can_trade(regime):
            logger.warning(f"🛑 [REGIME BLOCK] Market is {regime}. Skipping all BUY signals.")
            return []
            
        health = self.watchdog.check_health()
        if health == "CRITICAL_MEM":
            logger.critical("🚨 [WATCHDOG BLOCK] System Memory Critical. Halting execution.")
            return []

        # 2. Enrich Data with Standard Indicators
        df = TAWrapper.add_all_indicators(df)
        
        market_phase = self.check_market_phase(df) # Intra-stock phase
        
        signals = []
        for strategy in self.strategies:
            try:
                # [BEAR MARKET LOGIC]
                # If strategy is InverseScalpingStrategy, we pass market_phase explicitly
                if isinstance(strategy, InverseScalpingStrategy):
                    if code == strategy.target_etf: # Only evaluate on the specific ETF
                         signal = strategy.evaluate(df, market_phase)
                         if signal['action'] in ['BUY', 'SELL']:
                              # Enrich & Add
                              signal["strategy"] = strategy.name
                              signal["code"] = code
                              signal["price"] = df.iloc[-1]['close']
                              signal["timestamp"] = df.iloc[-1]['datetime']
                              signal["source"] = "ALGO"
                              signals.append(signal)
                    continue 

                # [NORMAL LOGIC]
                signal = strategy.check_entry(df)
                if signal["action"] == "BUY":

                    # Enrich signal
                    signal["strategy"] = strategy.name
                    signal["code"] = code
                    signal["price"] = df.iloc[-1]['close']
                    current_time = df.iloc[-1]['datetime']
                    signal["timestamp"] = current_time
                    signal["source"] = "ALGO"

                    # --- 1. Risk Manager Check (Whipsaw/Turbulence) ---
                    risk_check = self.risk_manager.can_enter(code, signal["price"], current_time, df, market_phase)
                    
                    # [NEW] Sniper Exception: If Strategy requests Risk Bypass (e.g., Scalping), ignore Turbulence
                    if signal.get("risk_bypass", False) and "Turbulent" in risk_check["reason"]:
                        logger.info(f"⚠️ Risk Manager Override: Allowing {strategy.name} despite Turbulence.")
                        risk_check["allowed"] = True
                        
                    if not risk_check["allowed"]:
                        logger.warning(f"[RISK BLOCKED] {code}: {risk_check['reason']}")
                        continue # Skip this trade

                    # --- [NEW] 1.5 Strict Filter (Phase 3) ---
                    # Only applies if STRICT_MODE is enabled (default: True for safety)
                    if self.STRICT_MODE and not self._check_strict_filters(df):
                        logger.warning(f"[STRICT BLOCKED] {code}: Failed Triple Confirmation (BB+MACD+RSI+Vol)")
                        continue

                    # --- 2. AI Rational Check ---
                    tech_summary = {
                        "strategy": strategy.name,
                        "conditions": signal.get("comment", ""),
                        "rsi": df.iloc[-1].get("RSI_14", "N/A"),
                        "risk_check": risk_check["reason"],
                        "strict_pass": "YES" 
                    }
                    news_summary = {"macro": "Fed Rate Decision Pending"} 
                    
                    
                    # [Phase G/H] Causal Sector Logic with Apex Adaptation
                    # A signal is only valid if it aligns with the Index/Sector narrative OR is a Maverick.
                    
                    sector_context = context.get('sector_data', pd.DataFrame())
                    index_context = context.get('index_data', pd.DataFrame())
                    
                    causal_confirmed = True
                    is_maverick = False # Initialize explicitly
                    
                    if not sector_context.empty and not index_context.empty:
                        sector_momentum = sector_context['close'].pct_change(5).iloc[-1]
                        index_momentum = index_context['close'].pct_change(5).iloc[-1]
                        
                        # [Apex Adaptation] Maverick Exception:
                        # If Stock Volume is > 300% of 20MA and Price is UP, it might be a "Maverick".
                        vol_ma = df['volume'].rolling(20).mean().iloc[-1]
                        if df['volume'].iloc[-1] > vol_ma * 3.0 and df['close'].pct_change().iloc[-1] > 0.03:
                            is_maverick = True
                            logger.info(f"🚀 [MAVERICK DETECTED] {code} is decoupling from Sector with explosive volume!")

                        # Causal Rule: Don't fight the Index/Sector unless Maverick.
                        if index_momentum < -0.02 and not is_maverick: 
                            logger.warning(f"[{code}] Causal Block: Index is crashing ({index_momentum:.2%}). Blocking.")
                            continue # Skip to next strategy/stock
                            
                        if sector_momentum < 0 and not is_maverick: 
                            logger.info(f"[{code}] Causal Block: Sector lack of momentum (and not a Maverick).")
                            causal_confirmed = False

                    if not causal_confirmed:
                        # logger.info(f"[{code}] Causal Chain Broken: Sector/Index mismatch. Blocking signal.")
                        continue # Skip signal if causal chain is broken

                    # AI Contextual Inference (Restored Tactical Command)
                    ai_verdict = await self.ai_advisor.ask_ai_confirmation(code, tech_summary, news_summary)
                        
                    if ai_verdict["decision"] == "BUY":
                        # [Phase I] Financial Calibration: Dynamic Targets via RiskManager
                        trade_mode = risk_check.get("mode", "NORMAL")
                        
                        # Maverick Override Logic integration
                        if is_maverick: 
                            trade_mode = "MAVERICK" 
                        
                        # Get Exit Parameters from Central Logic
                        exit_params = self.risk_manager.get_exit_params(trade_mode, signal["price"])
                        
                        # Apply Parameters
                        signal["take_profit"] = exit_params["take_profit_price"]
                        signal["stop_loss"] = exit_params["stop_loss_price"]
                        signal["trailing_stop_pct"] = exit_params["trailing_stop_pct"]

                        signal["strategy_desc"] = exit_params["strategy_description"]
                        
                        signal["ai_confirmation"] = "APPROVED"
                        signal["ai_reason"] = ai_verdict["reason"]
                        signal["trade_mode"] = trade_mode
                        
                        signals.append(signal)
                        self.daily_trade_count += 1 
                        
                        # Log with Strategy Context
                        logger.info(f"⚔️ [{trade_mode}] {code} BUY | {exit_params['strategy_description']} | AI: {ai_verdict['reason']}")
                else:
                    logger.warning(f"[ALGO BLOCKED] {code} - AI Rejection: {ai_verdict['reason']}")
                
                # Capture EXIT logic to update RiskManager (Simulation Only for now)
                # In real live trading, this would be triggered by OrderManager updates
                # For simulation replay, we assume we might need to know when we exited to enforce cooldown
                # But StrategyEngine doesn't manage positions statefully itself in this loop usually.
                # However, ReplayEngine monitors exits. ReplayEngine needs to tell StrategyEngine about exits?
                # BETTER: StrategyEngine just outputs signals. 
                # ReplayEngine determines PnL and calls strategy_engine.risk_manager.record_exit()
                        
            except Exception as e:
                logger.error(f"Error evaluating {strategy.name} on {code}: {e}")
                
        return signals

    def handle_condition_signal(self, code: str, condition_name: str, action: str):
        """
        Process a signal received from Kiwoom HTS Condition Search.
        action: 'INSERT' or 'DELETE'
        """
        if action == "INSERT":
            signal = {
                "action": "BUY",
                "code": code,
                "strategy": f"HTS-{condition_name}",
                "confidence": 0.8, # HTS conditions are trusted but maybe less than full Algo verification?
                "comment": f"HTS Condition Match: {condition_name}",
                "source": "HTS"
            }
            logger.info(f"[HTS SIGNAL] {code} matched {condition_name}")
            return signal
        elif action == "DELETE":
            logger.info(f"[HTS EXIT] {code} no longer matches {condition_name}")
            return None
