import logging
import datetime
from .cafe_repository_manager import cafe_repo

logger = logging.getLogger("SynergyEngine")

class SynergyFilterEngine:
    """
    The 'Ultra-Filter': Fuses Quant (800 Swarm) and Qual (Cafe Intelligence).
    Goal: Select the Top 5 High-Yield candidates for 50-80% daily cumulative returns.
    """
    def __init__(self, hq):
        self.hq = hq
        self.daily_targets = []
        self.last_update = None

    def calculate_synergy_score(self, ticker, quant_signal):
        """
        Calculates a hybrid score (0.0 to 2.0).
        - Quant (Swarm): 0.0 to 1.0 (based on RSI/Resonance)
        - Qual (Cafe): 0.5 booster if expert mentioned it recently.
        """
        # 1. Base Quant Score (Normalized RSI/MA/Volume)
        # Higher score for stronger 'Resonance' in the swarm
        quant_score = (quant_signal.get("resonance", 1.0) - 1.0) * 2.0 # 0 to 1
        
        # 2. Qual Booster (From Cafe Intelligence DB)
        # Check if this ticker has a fresh expert signal in the last 6 hours
        recent_expert = [s for s in cafe_repo.get_recent_signals(hours=6) if s["ticker"] == ticker]
        qual_booster = 0.5 if recent_expert else 0.0
        
        # 3. Sentiment Weight (Qualitative Bias)
        sentiment_score = 0.0
        if recent_expert:
            # If expert profit was high, the booster increases
            max_profit = max([s["profit_pct"] for s in recent_expert])
            sentiment_score = min(max_profit / 30.0, 0.5) # Max 0.5 additional boost

        total_score = quant_score + qual_booster + sentiment_score
        return min(total_score, 2.0)

    async def select_ultra_targets(self):
        """
        Ranks all 800 workers and picks the Top 5 most synergized candidates.
        """
        candidates = []
        for ticker, worker in self.hq.aggregator.workers.items():
            if worker.status == "MONITORING" and worker.prediction:
                score = self.calculate_synergy_score(ticker, worker.prediction)
                candidates.append({
                    "ticker": ticker,
                    "score": score,
                    "quant_reason": worker.prediction["reason"],
                    "qual_reason": "Cafe Consensus Found" if score > 1.2 else "Quant Only"
                })
        
        # Sort by score descending
        candidates.sort(key=lambda x: x["score"], reverse=True)
        
        # Select Top 5 for HIGH YIELD focus
        self.daily_targets = candidates[:5]
        
        if self.daily_targets:
            logger.info("🔥 ULTRA-TARGETS SELECTED (Targeting 50-80% Daily):")
            for t in self.daily_targets:
                logger.info(f"   🎯 [{t['ticker']}] Score: {t['score']:.2f} | Reason: {t['quant_reason']} + {t['qual_reason']}")
        
        return self.daily_targets

    def apply_aggressive_risk_parameters(self, target_ticker):
        """
        Applies 'High-Yield' parameters (Higher target, tighter stop)
        for the Selected Top 5.
        """
        # For Top 5 targets, we aim for 10% instead of 3%
        return {
            "target_pct": 0.10, # 10% Profit Target
            "stop_pct": 0.02,   # 2% Tight Stop
            "trailing_stop": True
        }

# Logic Group: Synergy Engine
# self.synergy_engine = SynergyFilterEngine(self)
