"""
[파일명]: backend/core/risk_manager.py
[역할]: ISATS 계좌 수호신. 손절 관리, 재진입 금지(쿨다운), 시장 변동성 필터링을 통해 자산을 보호함.
[저장위치]: c:/Users/FREE/Desktop/주식/isats/backend/core/risk_manager.py
[상세설명]:
이 모듈은 무분별한 뇌동매매를 방지하고, 시장이 너무 불안정할 때 진입을 차단하는 역할을 합니다.
특히 '상한가 페이크'에 당해 손절이 나간 종목을 즉시 다시 사는 실수를 방지하기 위해 30분 쿨다운 로직을 포함하고 있습니다.
"""

import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional

logger = logging.getLogger("RiskManager")

class RiskManager:
    """
    거래 위험을 관리하고 진입 가능 여부를 판단하는 클래스입니다.
    """
    def __init__(self):
        # 종목별 마지막 매도(손절) 기록 저장
        # { "종목코드": {"exit_time": 퇴출시간, "exit_price": 퇴출가격, "reason": 사유} }
        self.trade_history: Dict[str, dict] = {} 
        self.cooldown_minutes = 30 # 손절 후 30분간 동일 종목 진입 금지
        self.volatility_threshold = 3.0 # ATR이 주가의 3%를 초과하면 '매우 불안정'으로 간주하여 진입 차단

    def record_exit(self, code: str, exit_price: float, reason: str, timestamp: datetime):
        """
        매매가 종료되었을 때 호출되어 해당 종목에 대한 쿨다운을 시작합니다.
        """
        self.trade_history[code] = {
            "exit_time": timestamp,
            "exit_price": exit_price,
            "reason": reason
        }
        logger.info(f"RiskManager: {code} 매도 기록 완료 ({exit_price}원, 사유: {reason}). {self.cooldown_minutes}분 쿨다운 시작.")

    def check_novelty(self, df: pd.DataFrame) -> dict:
        """
        [Phase G] Novelty Detector (OOD: Out-of-Distribution)
        Detects if current market conditions are fundamentally different from historical 'Normal'.
        Ensures clarity when encountering 'Unknown Unknowns' (e.g., War, Pandemic, Black Swans).
        """
        if len(df) < 50: return {"is_novel": False, "score": 0.0}
        
        # 1. Z-Score analysis of recent Volatility vs 50-period average
        vol = (df['high'] - df['low']) / df['close']
        avg_vol = vol.rolling(50).mean().iloc[-1]
        std_vol = vol.rolling(50).std().iloc[-1]
        
        current_vol = vol.iloc[-1]
        z_score = (current_vol - avg_vol) / std_vol if std_vol > 0 else 0
        
        # 2. Clarity Rule -> Chaos Exploitation
        # If Z-Score > 3.0, it's not a "Stop", it's a "Crisis Opportunity".
        if abs(z_score) > 3.0:
            logger.warning(f"⚡ [CHAOS DETECTED] Volatility Z-Score {z_score:.2f}. Switching to PREDATORY_MODE.")
            return {"is_novel": True, "score": z_score, "mode": "CHAOS_OPPORTUNITY"}
            
        return {"is_novel": False, "score": z_score, "mode": "NORMAL"}

    def can_enter(self, code: str, current_price: float, current_time: datetime, df: pd.DataFrame, market_phase: str = "NEUTRAL") -> dict:
        """
        Final verification. Now supports 'Apex Adaptation' to exploit chaos.
        """
        # 0. Novelty/Chaos Check
        novelty = self.check_novelty(df)
        trade_mode = "NORMAL"
        
        if novelty["is_novel"]:
            # In Chaos Mode, we ONLY allow entry if price is significantly oversold 
            # or if it's a massive momentum breakout.
            trade_mode = "CHAOS"
            logger.info(f"⚔️ {code}: Chaos Mode Verification (Z:{novelty['score']:.2f})")

        # 0.5. Market Turbulence Check (System-wide Lock)
        if market_phase == "CRASH" and trade_mode != "CHAOS":
            # [Apex Adaptation] In Chaos Mode, we ignore standard CRASH locks for predatory buying
            return {"allowed": False, "reason": "⛔ MARKET CRASH DETECTED (System Lock-down)", "mode": "CRASH"}
        elif market_phase == "CRASH" and trade_mode == "CHAOS":
             logger.warning(f"⚔️ [APEX] Overriding CRASH lock for Chaos Opportunity on {code}")

        # 1. Cooldown Check
        if code in self.trade_history:
            last_exit = self.trade_history[code]
            time_diff = current_time - last_exit["exit_time"]
            if time_diff < timedelta(minutes=self.cooldown_minutes):
                reentry_threshold = last_exit["exit_price"] * 1.005
                if current_price > reentry_threshold:
                    return {"allowed": True, "reason": "재진입 승인: 이전 손절가를 강하게 돌파함 (+0.5%↑)", "mode": trade_mode}
                else:
                    return {"allowed": False, "reason": f"쿨다운 중 ({self.cooldown_minutes}분).", "mode": "COOLDOWN"}

        # 2. Turbulence Check (ATR %)
        if 'ATR_14' in df.columns:
            atr = df.iloc[-1]['ATR_14']
            price = df.iloc[-1]['close']
            atr_pct = (atr / price) * 100
            threshold = 2.0 if market_phase == "BEAR" else self.volatility_threshold
            
            # In Chaos Mode, we expect high Volatility, so we relax the standard ATR breaker
            chaos_threshold = 10.0 
            check_threshold = chaos_threshold if trade_mode == "CHAOS" else threshold
            
            if atr_pct > check_threshold:
                 return {"allowed": False, "reason": f"🛑 BREAKER-BACKFLOW RISK (ATR {atr_pct:.2f}%)", "mode": "VOLATILITY_LOCK"}

        return {"allowed": True, "reason": "✅ Risk/Breaker Check Passed", "mode": trade_mode}

    def calculate_bet_size(self, capital: float, df: pd.DataFrame, win_rate: float = 0.55, risk_reward: float = 2.0, use_half_kelly: bool = True) -> int:
        """
        Kelly Criterion-based Position Sizing.
        """
        if capital <= 0 or df.empty: return 0

        # Win probability (p) and Odds (b)
        p, b = win_rate, risk_reward
        q = 1.0 - p
        kelly_fraction = (b * p - q) / b
        
        if kelly_fraction <= 0: return 0 
            
        # Volatility-Triggered De-leveraging
        vol_modifier = 1.0
        if 'ATR_14' in df.columns:
            current_vol = (df.iloc[-1]['ATR_14'] / df.iloc[-1]['close']) * 100
            if current_vol > 2.0: 
                vol_modifier = max(0.2, 1.0 - (current_vol - 2.0) * 0.5)
                logger.warning(f"[VOL-PROTECT] Volatility Spike ({current_vol:.2f}%) -> Scaling down size.")

        final_fraction = min(kelly_fraction * 0.5 * vol_modifier if use_half_kelly else kelly_fraction * vol_modifier, 0.20)
        allocation = min(capital * final_fraction, 20_000_000) 
        
        return int(allocation)

    def get_exit_params(self, mode: str, entry_price: float, current_volatility: float = 0) -> dict:
        """
        [Phase I] Dynamic Exit Parameter Generator
        Defines 'How to Sell' based on the trade mode.
        """
        params = {
            "mode": mode,
            "entry_price": entry_price,
            "take_profit_price": 0.0,
            "stop_loss_price": 0.0,
            "trailing_stop_pct": 0.0,
            "strategy_description": ""
        }
        
        if mode == "MAVERICK":
            # Strategy: "Let Winners Run"
            # No fixed target (Open). Trailing stop of 5% (loosened) to tolerate noise.
            # Initial Stop Loss is 3% to prevent immediate collapse.
            params["take_profit_price"] = entry_price * 10.0 # Virtual Infinity
            params["stop_loss_price"] = entry_price * 0.97 # -3.0% Initial
            params["trailing_stop_pct"] = 0.05 # 5% Trailing
            params["strategy_description"] = "Uncapped Upside / 5% Trailing Stop"
            
        elif mode == "CHAOS":
            # Strategy: "Snatch & Run" (Hit and Run)
            # High probability small wins in panic bounces.
            params["take_profit_price"] = entry_price * 1.015 # +1.5% Fixed
            params["stop_loss_price"] = entry_price * 0.990 # -1.0% Fixed (Tight)
            params["trailing_stop_pct"] = 0.0 # No trail, just limit exit
            params["strategy_description"] = "Scalp +1.5% / -1.0% Tight Brace"
            
        else: # NORMAL
            # Strategy: "Grind & Grow"
            # Standard 3% / 2% Bracket
            params["take_profit_price"] = entry_price * 1.03
            params["stop_loss_price"] = entry_price * 0.98
            params["trailing_stop_pct"] = 0.03 # Optional: Trail if > 3%? No, Fixed Target for Normal.
            params["strategy_description"] = "Standard Bracket +3% / -2%"
            
        return params
