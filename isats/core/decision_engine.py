from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List
import numpy as np
import logging

logger = logging.getLogger("ISATS:DecisionEngine")

class Signal(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    SELL_ALL = "SELL_ALL"  # Panic Selling / Emergency Exit

@dataclass
class DecisionContext:
    """
    [Decision Context]
    Container for all data required to make a trading decision.
    Acts as the input for the HybridDecisionEngine.
    """
    ticker: str
    current_price: float
    
    # 1. Quantitative Analysis (AI & Stats)
    stockformer_score: float       # -1.0 to 1.0 (Pred Return / Momentum)
    finrl_action: str              # "BUY", "SELL", "HOLD"
    technical_signal: str          # "BUY", "SELL", "HOLD" (Triple Confirm)
    
    # 2. Risk Metrics
    turbulence_index: float        # Market Volatility Index (VIX or Custom)
    
    # 3. Qualitative Analysis (LLM - Optional)
    llm_score: float = 0.0         # 0.0 to 1.0 (Confidence)
    has_llm_analysis: bool = False
    
    # 4. Portfolio State
    current_position_size: int = 0
    cash_available: float = 0.0
    
    # Reasoning Trace (Filled by Engine)
    reasoning_trace: List[str] = field(default_factory=list)

class HybridDecisionEngine:
    """
    [Phase 30] Hybrid Decision Engine
    The "Brain" that fuses Quant (AI/Tech) and Qual (LLM) signals with Risk Controls.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {
            'turbulence_threshold': 50.0,      # Stop buying if Market VIX/Turbulence > 50
            'min_confidence_score': 0.60,      # Minimum combined score to trigger BUY
            'weights': {
                'stockformer': 0.4,
                'finrl': 0.3,
                'technical': 0.3
            }
        }
        logger.info(f"🧠 HybridDecisionEngine Initialized: Threshold={self.config['turbulence_threshold']}")

    def make_decision(self, context: DecisionContext) -> Dict[str, Any]:
        """
        Execute the Decision Pipeline:
        1. Risk Filter (Turbulence)
        2. Signal Fusion (Weighted Scoring)
        3. Final Verdict (Buy/Sell/Hold)
        4. Position Sizing
        """
        result = {
            "action": "HOLD",
            "quantity": 0,
            "confidence": 0.0,
            "reasoning": []
        }
        
        # === Step 1: Turbulence Filter (Safety Valve) ===
        if context.turbulence_index > self.config['turbulence_threshold']:
            context.reasoning_trace.append(f"🚨 TURBULENCE DETECTED: {context.turbulence_index} > {self.config['turbulence_threshold']}")
            
            # If we hold position, maybe SELL_ALL? For now, just forced HOLD (Buy Ban)
            if context.current_position_size > 0:
                # TODO: Implement Panic Sell Logic here if needed
                result["action"] = "SELL" # Reduce exposure
                result["quantity"] = context.current_position_size # Sell All? Or Half?
                context.reasoning_trace.append("🔻 Risk Reduction (Selling due to High Turbulence)")
            else:
                result["action"] = "HOLD"
                context.reasoning_trace.append("🛡️ Buying Halted due to Market Risk")
            
            result["reasoning"] = context.reasoning_trace
            return result

        context.reasoning_trace.append(f"✅ Market Normal (Turbulence: {context.turbulence_index})")

        # === Step 2: Signal Fusion ===
        score = self._calculate_fusion_score(context)
        result["confidence"] = score
        
        # === Step 3: Final Verdict ===
        if context.current_position_size == 0:
            # Entry Logic
            if score >= self.config['min_confidence_score']:
                result["action"] = "BUY"
                context.reasoning_trace.append(f"🚀 BUY SIGNAL: Score {score:.2f} >= {self.config['min_confidence_score']}")
            else:
                result["action"] = "HOLD"
                context.reasoning_trace.append(f"Waiting: Score {score:.2f} < {self.config['min_confidence_score']}")
        else:
            # Exit Logic
            # If Score drops significantly or FinRL says SELL
            if score < 0.3 or context.finrl_action == "SELL" or context.technical_signal == "SELL":
                result["action"] = "SELL"
                result["quantity"] = context.current_position_size
                context.reasoning_trace.append("🔻 SELL SIGNAL: Weak Score or Indicator Exit")
            else:
                result["action"] = "HOLD"
                context.reasoning_trace.append("HOLD: Trend Intact")

        # === Step 4: Position Sizing (Dynamic) ===
        if result["action"] == "BUY":
            # Determine size based on Confidence
            # Base: 10% of Cash
            # Multiplier: 0.5x to 1.5x based on Score (0.6 -> 1.0)
            base_amt = context.cash_available * 0.10
            multiplier = 0.5 + (score * 1.0) # If score 0.6 -> 1.1x, Score 1.0 -> 1.5x
            target_amt = base_amt * multiplier
            
            qty = int(target_amt / context.current_price)
            result["quantity"] = qty
            context.reasoning_trace.append(f"💰 Sizing: {qty} shares (Conviction: {multiplier:.1f}x)")

        result["reasoning"] = context.reasoning_trace
        return result

    def _calculate_fusion_score(self, ctx: DecisionContext) -> float:
        """
        Calculate Weighted Score (0.0 to 1.0)
        """
        w = self.config['weights']
        total_score = 0.0
        
        # 1. Stockformer (-1.0 to 1.0) -> Normalize to 0.0 - 1.0
        # Score > 0 contributes positive confidence
        sf_norm = max(0.0, ctx.stockformer_score) # Simple ReLU for buying confidence
        total_score += sf_norm * w['stockformer']
        ctx.reasoning_trace.append(f"  • Stockformer: {ctx.stockformer_score:.2f} (Contr: {sf_norm * w['stockformer']:.2f})")
        
        # 2. FinRL (Categorical)
        rl_score = 1.0 if ctx.finrl_action == "BUY" else 0.0
        total_score += rl_score * w['finrl']
        ctx.reasoning_trace.append(f"  • FinRL Agent: {ctx.finrl_action} (Contr: {rl_score * w['finrl']:.2f})")
        
        # 3. Technical (Categorical)
        tech_score = 1.0 if ctx.technical_signal == "BUY" else 0.0
        total_score += tech_score * w['technical']
        ctx.reasoning_trace.append(f"  • Tech Filter: {ctx.technical_signal} (Contr: {tech_score * w['technical']:.2f})")
        
        return total_score
