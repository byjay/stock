import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Set

logger = logging.getLogger("DynamicUniverse")

class DynamicUniverseManager:
    """
    [Phase 46] Alive Watchlist Manager
    - Condition: Only track stocks that are 'Moving'. 
    - Action: Add 'Hot' stocks, Drop 'Cold' stocks periodically.
    """
    def __init__(self):
        self.active_targets: Set[str] = set()
        self.watch_data: Dict[str, dict] = {} # {code: {added_at: dt, last_price: float, reason: str}}
        self.max_size = 50 # Keep it focused
        
        # Criteria
        self.min_volatility = 1.5 # 1.5% Minimum movement to keep watching
        self.stagnant_minutes = 10 # If flat for 10 mins, DROP.
        
    def get_targets(self) -> List[str]:
        return list(self.active_targets)

    def add_target(self, code: str, reason: str, price: float):
        if code in self.active_targets:
            return
            
        if len(self.active_targets) >= self.max_size:
            self._evict_weakest()
            
        self.active_targets.add(code)
        self.watch_data[code] = {
            "added_at": datetime.now(),
            "last_price": price,
            "reason": reason,
            "last_active": datetime.now()
        }
        logger.info(f"🔥 [ADD] {code} added to Active Watchlist ({reason})")

    def update_target(self, code: str, current_price: float):
        """Called every time we get new data for a watched stock."""
        if code not in self.watch_data:
            return
            
        meta = self.watch_data[code]
        prev_price = meta['last_price']
        
        # Check movement
        change = abs((current_price - prev_price) / prev_price) * 100
        
        if change > 0.1: # Even 0.1% move is activity
            meta['last_active'] = datetime.now()
            meta['last_price'] = current_price

    def prune_stagnant(self):
        """Remove stocks that haven't moved or triggered signals."""
        now = datetime.now()
        to_remove = []
        
        for code, meta in self.watch_data.items():
            inactive_duration = (now - meta['last_active']).total_seconds() / 60
            
            if inactive_duration > self.stagnant_minutes:
                to_remove.append(code)
                logger.info(f"❄️ [DROP] {code} removed (Stagnant for {inactive_duration:.1f} min)")
                
        for code in to_remove:
            self.active_targets.discard(code)
            del self.watch_data[code]

    def _evict_weakest(self):
        """Remove the oldest added target to make space."""
        if not self.watch_data: return
        
        oldest_code = min(self.watch_data, key=lambda k: self.watch_data[k]['added_at'])
        self.active_targets.discard(oldest_code)
        del self.watch_data[oldest_code]
        logger.info(f"♻️ [EVICT] {oldest_code} removed to make space.")
