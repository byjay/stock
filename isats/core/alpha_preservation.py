import random
import logging
import time

logger = logging.getLogger("AlphaPreservation")

class AlphaPreservation:
    """
    [Anti-Fragility] Execution Obfuscation (Stealth Ops).
    Prevents predator bots from detecting and front-running our signals.
    Defends against 'Alpha Decay' critique in 비판.md.
    """
    def __init__(self):
        pass

    def obfuscate_order(self, order_data: dict):
        """
        Adds random time jitter and price/qty slight randomization 
        to break deterministic patterns that HFT bots look for.
        """
        # 1. Time Jitter (100ms to 2s)
        jitter = random.uniform(0.1, 2.0)
        
        # 2. Qty Slicing (Slightly non-round numbers)
        original_qty = order_data.get('qty', 0)
        noise = random.randint(-2, 2)
        randomized_qty = max(1, original_qty + noise)
        
        logger.info(f"🕵️ [STEALTH] Obfuscating order. Jitter: {jitter:.2f}s, Qty adjustment: {noise}")
        
        modified_order = order_data.copy()
        modified_order['qty'] = randomized_qty
        modified_order['jitter_ms'] = int(jitter * 1000)
        
        return modified_order

    def execute_iceberg(self, symbol, total_qty, side='BUY', display_ratio=0.05):
        """
        [Phase E] Iceberg Execution
        Only shows a small fraction (display_ratio) of the order to the market.
        """
        display_qty = max(1, int(total_qty * display_ratio))
        remaining_qty = total_qty
        
        logger.info(f"❄️ [ICEBERG] Starting {side} for {symbol}. Total: {total_qty}, Display: {display_qty}")
        
        chunk_count = 0
        while remaining_qty > 0:
            current_chunk = min(display_qty, remaining_qty)
            # In real world, this would be a single order with 'Display Quantity' attribute
            # but for our simulation/stealth logic, we model it as sequence of small orders.
            logger.debug(f"[ICEBERG-CHUNK] Submitting visible chunk {chunk_count+1}: {current_chunk}")
            
            remaining_qty -= current_chunk
            chunk_count += 1
            
            # Simulate wait for fill (randomized to avoid detection)
            # time.sleep(random.uniform(5, 15)) 
            
        return True

    def rotate_execution_strategy(self, total_qty):
        """
        Randomly switches between TWAP, VWAP, and Iceberg.
        """
        strategies = ["TWAP", "VWAP", "ICEBERG"]
        chosen = random.choice(strategies)
        logger.info(f"🔄 [ROTATION] Switching to {chosen} Execution to hide fingerprints.")
        return chosen
