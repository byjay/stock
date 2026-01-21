import asyncio
import logging
import random
import sys
import os
from datetime import datetime

# Adjust path to find backend modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from backend.core.elastic_time_machine import ElasticTimeMachine
from backend.core.universe_provider import UniverseProvider

# Logging Setup
logger = logging.getLogger("ISATS:ContinuousLearner")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(message)s')

async def worker(worker_id):
    """
    Continuous Learning Worker (Elastic Mode).
    """
    logger.info(f"🤖 [Worker-{worker_id}] Online and ready for Elastic Learning.")
    
    # [NEW] Use Elastic Time Machine
    machine = ElasticTimeMachine()
    provider = UniverseProvider()
    
    # 1. Load Universe (FULL MARKET)
    # User Request: "3000 stocks, millions of iterations"
    # We switch to the full CSV list.
    full_market = provider.get_all_from_csv()
    TICKERS = full_market if full_market else provider.get_kr_top_300()
    
    logger.info(f"🌍 [Worker-{worker_id}] Loaded {len(TICKERS)} tickers (Full Market Mode).")
    
    if not TICKERS:
        logger.error("❌ Universe is empty! Check loading logic.")
        return

    while True:
        try:
            target = random.choice(TICKERS)
            
            # [GENETIC MUTATION]
            # Randomly generate 'Rubber Band' timeframes to test.
            # User Idea: "30, 44, 55, 132, 325..."
            # We mix standard Fibonacci sequence with random 'Noise' to find hidden resonances.
            base_genes = [2, 3, 5, 8, 13, 21, 34, 55, 89, 144]
            random_genes = [random.randint(4, 50) for _ in range(3)]
            mutation_pool = list(set(base_genes + random_genes))
            
            # Select 3-4 random frames for this run
            selected_genes = random.sample(mutation_pool, 3)
            # Convert to Pandas Resample Rule (e.g. '13D')
            # Currently focused on 'D' (Day) as we use Daily data. 
            # (To do minutes, we'd need minute data source)
            custom_rules = [f"{g}D" for g in selected_genes]
            
            logger.info(f"🧬 [Worker-{worker_id}] Testing Mutation {custom_rules} for {target}...")
            
            # Run Elastic Learning with Custom Frames
            # Note: We need to update ElasticTimeMachine to accept custom_rules
            # Passing it via a new arg or modifying the class. 
            # Let's assume we pass it as `custom_frames`.
            patterns = await machine.run_elastic_learning(target, lookback_weeks=104, custom_frames=custom_rules) 
            
            if patterns:
                count = len(patterns)
                logger.info(f"✅ [Worker-{worker_id}] Extracted {count} Patterns (Genes: {custom_rules})")
                
                # Save to shared file
                save_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/winning_patterns.jsonl"))
                try:
                    import json
                    with open(save_path, "a", encoding="utf-8") as f:
                        for p in patterns:
                            # Tag the pattern with the frames used
                            p['genetic_frames'] = custom_rules
                            f.write(json.dumps(p) + "\n")
                except Exception as save_err:
                    logger.error(f"❌ [Worker-{worker_id}] Failed to save patterns: {save_err}")

            else:
                 logger.info(f"💤 [Worker-{worker_id}] No resonance found.")

            # Rest to prevent rate limits
            sleep_time = random.randint(5, 15)
            logger.info(f"😴 [Worker-{worker_id}] Resting for {sleep_time}s...")
            await asyncio.sleep(sleep_time)

        except Exception as e:
            logger.error(f"💥 [Worker-{worker_id}] Error: {e}")
            await asyncio.sleep(10)

async def main():
    logger.info("🚀 [SYSTEM] Initializing Elastic Time Machine (Rubber Band Mode)...")
    
    # Spawn 3 Concurrent Workers
    tasks = [worker(i) for i in range(1, 4)]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Learning Loop Terminated by User.")
