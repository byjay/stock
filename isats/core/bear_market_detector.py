"""
[NEW] BEAR Market Detector - 1-Day Early Detection System
Detects bear market onset within 1 day using multi-signal analysis.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List

logger = logging.getLogger("BearMarketDetector")

class BearMarketDetector:
    """
    BEAR Market Early Detection System
    Detects market crash within 1 day using 5 key signals.
    """
    def __init__(self):
        self.bear_threshold = 3  # Minimum signals to confirm BEAR
        self.detection_history = []
        
    def detect_bear_onset(self, market_data: Dict) -> Dict:
        """
        Analyze market data and detect BEAR market onset.
        
        Returns:
            {
                "is_bear": bool,
                "confidence": float (0-1),
                "signals": List[str],
                "recommended_action": str
            }
        """
        signals = []
        
        # Signal 1: Index Crash (KOSPI -3% or more)
        kospi_change = market_data.get("kospi_change_pct", 0)
        if kospi_change <= -3.0:
            signals.append("INDEX_CRASH")
            logger.warning(f"🚨 Signal 1: Index Crash {kospi_change:.2f}%")
        
        # Signal 2: VIX Spike (Volatility +30% or more)
        vix_change = market_data.get("vix_change_pct", 0)
        if vix_change >= 30.0:
            signals.append("VIX_SPIKE")
            logger.warning(f"🚨 Signal 2: VIX Spike +{vix_change:.2f}%")
        
        # Signal 3: Foreign & Institution Selling
        foreign_net = market_data.get("foreign_net_buy", 0)
        inst_net = market_data.get("institution_net_buy", 0)
        
        if foreign_net < -500_000_000_000 and inst_net < -300_000_000_000:
            signals.append("MASSIVE_SELLING")
            logger.warning(f"🚨 Signal 3: Massive Selling (F: {foreign_net/1e9:.1f}B, I: {inst_net/1e9:.1f}B)")
        
        # Signal 4: Advance/Decline Ratio Collapse
        advancing = market_data.get("advancing_stocks", 0)
        total = market_data.get("total_stocks", 1)
        ad_ratio = advancing / total if total > 0 else 0
        
        if ad_ratio < 0.2:
            signals.append("AD_COLLAPSE")
            logger.warning(f"🚨 Signal 4: A/D Ratio Collapse {ad_ratio:.1%}")
        
        # Signal 5: Volume Surge (Panic Selling)
        trading_value = market_data.get("trading_value", 0)
        avg_30d = market_data.get("avg_trading_value_30d", 1)
        
        if trading_value > avg_30d * 2.0:
            signals.append("VOLUME_SURGE")
            logger.warning(f"🚨 Signal 5: Volume Surge {trading_value/avg_30d:.1f}x")
        
        # Determine BEAR status
        is_bear = len(signals) >= self.bear_threshold
        confidence = len(signals) / 5.0
        
        result = {
            "is_bear": is_bear,
            "confidence": confidence,
            "signals": signals,
            "signal_count": len(signals),
            "timestamp": datetime.now().isoformat()
        }
        
        if is_bear:
            result["recommended_action"] = "ACTIVATE_PUT_STRATEGY"
            logger.critical(f"🔴 BEAR MARKET DETECTED! Confidence: {confidence:.0%}, Signals: {signals}")
        else:
            result["recommended_action"] = "MONITOR"
        
        self.detection_history.append(result)
        return result
    
    def get_bear_intensity(self, market_data: Dict) -> str:
        """
        Classify BEAR market intensity.
        Returns: "MILD", "MODERATE", "SEVERE"
        """
        kospi_change = market_data.get("kospi_change_pct", 0)
        
        if kospi_change <= -7.0:
            return "SEVERE"
        elif kospi_change <= -5.0:
            return "MODERATE"
        elif kospi_change <= -3.0:
            return "MILD"
        else:
            return "NONE"
    
    def select_best_put_option(self, market_data: Dict) -> Dict:
        """
        Select optimal PUT option ETF based on market condition.
        
        Returns:
            {
                "etf_code": str,
                "etf_name": str,
                "leverage": int (1 or 2),
                "reason": str
            }
        """
        kospi_change = market_data.get("kospi_change_pct", 0)
        kosdaq_change = market_data.get("kosdaq_change_pct", 0)
        intensity = self.get_bear_intensity(market_data)
        
        # Severe Crash: Use 2x Leverage Inverse
        if intensity == "SEVERE":
            return {
                "etf_code": "251340",
                "etf_name": "KODEX 레버리지인버스",
                "leverage": 2,
                "reason": f"Severe crash {kospi_change:.1f}% - Maximum profit with 2x leverage"
            }
        
        # KOSDAQ weaker than KOSPI: Use KOSDAQ Inverse
        if kosdaq_change < kospi_change - 2.0:
            return {
                "etf_code": "251350",
                "etf_name": "KODEX 코스닥150 인버스",
                "leverage": 1,
                "reason": f"KOSDAQ underperforming ({kosdaq_change:.1f}% vs {kospi_change:.1f}%)"
            }
        
        # Moderate/Mild: Use Standard Inverse
        return {
            "etf_code": "114800",
            "etf_name": "KODEX 인버스",
            "leverage": 1,
            "reason": f"Standard inverse for {intensity.lower()} crash {kospi_change:.1f}%"
        }
    
    def calculate_put_position_size(self, total_capital: float, current_price: float) -> Dict:
        """
        Calculate PUT option position size with strict constraints.
        
        🔴 ABSOLUTE RULES:
        1. Single order: 1,000 ~ 5,000 KRW only
        2. Total PUT exposure: MAX 30% of total capital
        
        Args:
            total_capital: Total account balance
            current_price: Current PUT ETF price
        
        Returns:
            {
                "order_value": float,
                "shares": int,
                "capital_ratio": float,
                "is_allowed": bool,
                "reason": str
            }
        """
        # Rule 1: Single order constraint (1,000 ~ 5,000 KRW)
        MIN_ORDER = 1_000
        MAX_ORDER = 5_000
        
        # Rule 2: Total PUT exposure constraint (30% max)
        MAX_PUT_RATIO = 0.30
        max_put_capital = total_capital * MAX_PUT_RATIO
        
        # Calculate order value (default: 3,000 KRW for moderate approach)
        order_value = 3_000
        
        # Adjust based on total capital
        if total_capital < 1_000_000:  # Less than 1M
            order_value = MIN_ORDER  # Minimum
        elif total_capital > 100_000_000:  # More than 100M
            order_value = MAX_ORDER  # Maximum
        
        # Calculate shares
        shares = int(order_value / current_price)
        actual_order_value = shares * current_price
        
        # Check if within 30% limit
        capital_ratio = actual_order_value / total_capital
        is_allowed = capital_ratio <= MAX_PUT_RATIO
        
        result = {
            "order_value": actual_order_value,
            "shares": shares,
            "capital_ratio": capital_ratio,
            "is_allowed": is_allowed,
            "max_allowed": max_put_capital
        }
        
        if not is_allowed:
            result["reason"] = f"Exceeds 30% limit ({capital_ratio:.1%} > 30%)"
        elif actual_order_value < MIN_ORDER or actual_order_value > MAX_ORDER:
            result["is_allowed"] = False
            result["reason"] = f"Order value {actual_order_value:,.0f} outside 1,000~5,000 range"
        else:
            result["reason"] = f"Valid PUT order: {actual_order_value:,.0f} KRW ({capital_ratio:.1%} of capital)"
        
        return result

