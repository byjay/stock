import logging
from datetime import datetime
from backend.advanced_analytics.disclosure_analyzer import DisclosureAnalyzer

logger = logging.getLogger("Core:RealTimeEventManager")

class RealTimeEventManager:
    """
    [Phase 9] Real-Time Event & News Response System
    Responsibility:
    - Listen to Live Events from Kiwoom (News, Disclosures, VI notifications).
    - Consult `DisclosureAnalyzer` to judge impact (Positive/Negative).
    - Issue IMMEDIATE 'Action Signals' to StrategyEngine (Buy/Sell/Block).
    """
    def __init__(self, strategy_engine, disclosure_analyzer: DisclosureAnalyzer):
        self.strategy_engine = strategy_engine
        self.disclosure_analyzer = disclosure_analyzer
        self.active_alerts = {} 

    def handle_realtime_news(self, code: str, title: str, content: str, received_time: datetime):
        """
        Called when Kiwoom pushes a News/Disclosure ID.
        """
        logger.info(f"🚨 [REAL-TIME NEWS] {code}: {title}")
        
        # 1. Analyze Sentiment & History
        sentiment = self.disclosure_analyzer.get_event_sentiment(code, content) # BULLISH/BEARISH/NEUTRAL
        
        # 2. Decide Action (The "Explicit Standard" User requested)
        decision = self._decide_news_action(sentiment, title)
        
        # 3. Execute or Notify
        if decision["action"] != "IGNORE":
            logger.info(f"⚡ ACTION TRIGGERED: {decision['action']} due to '{decision['reason']}'")
            # In a real system, direct routing to OrderManager or StrategyEngine overrides
            # self.strategy_engine.inject_external_signal(code, decision)

    def _decide_news_action(self, sentiment: str, title: str) -> dict:
        """
        [USER REQUEST] Clear Standards for Action.
        """
        # Rule 1: Bad News (Embezzlement, Capital Decrease) -> IMMEDIATE EXIT
        if sentiment == "BEARISH":
            return {
                "action": "PANIC_SELL",
                "reason": f"Critical Bad News Detected: {title}",
                "priority": "HIGH"
            }
            
        # Rule 2: Good News (Supply Contract) -> CHECK CHART
        elif sentiment == "BULLISH":
            return {
                "action": "WATCH_FOR_BUY",
                "reason": "Good News Detected. Check Chart for Volume Spike.",
                "priority": "MEDIUM"
            }
            
        return {"action": "IGNORE", "reason": "Neutral News"}

    def handle_vi_trigger(self, code: str, direction: str):
        """
        Called when Volatility Interruption (VI) activates.
        direction: 'UP' or 'DOWN'
        """
        if direction == "UP":
            logger.info(f"🚀 VI ALERT (UP): {code}. Preparing for Spike Strategy...")
            # Trigger SpikeScalpingStrategy checks
        else:
            logger.warning(f"📉 VI ALERT (DOWN): {code}. Analyzing Potential Dip/Crash...")
