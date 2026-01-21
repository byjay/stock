import asyncio
import logging
import pandas as pd
import os
from datetime import datetime

# ISATS Core
from backend.core.korea_inv_wrapper import KoreaInvWrapper
from backend.core.multiplex_engine import MultiplexDecisionEngine
from backend.core.universe_provider import UniverseProvider

# Logging Setup
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename=f"logs/mass_sim_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger('').addHandler(console)

logger = logging.getLogger("MassSimulation")

async def run_mass_simulation():
    """
    [Phase 45] Mass Scale Ingestion & Verification
    1. Fetch Data for Top KR/US Stocks (Real or Mock)
    2. Store to Data Lake (Simulated via Local FS/DataFrame for now)
    3. Run Multiplex Engine
    4. Aggregate Results
    """
    
    logger.info("🚀 Starting Mass Scale Multiplex Simulation...")
    
    # 1. Initialize Components
    broker = KoreaInvWrapper() # Auto-loads credentials from secrets.yaml
    engine = MultiplexDecisionEngine()
    
    # 2. Get Universe
    universe = UniverseProvider.get_full_universe()
    kr_codes = universe['KR']
    us_codes = universe['US']
    
    logger.info(f"🎯 Targets: KR {len(kr_codes)} stocks, US {len(us_codes)} stocks")
    
    results = []
    
    # --- PROCESSING KR STOCKS ---
    logger.info(">>> Processing KR Market...")
    for code in kr_codes:
        logger.info(f"   Now Processing: {code}")
        
        # A. Fetch Data (Real API)
        # Fetch 100 days of history (~5 months) to test Multiplex Engine
        history_data = await broker.fetch_history(code, days=100)
        
        if not history_data:
            logger.warning(f"   ⚠️ No Data for {code}. Skipping.")
            continue
            
        # Standardize Data for Engine
        # KIS returns list of dicts -> DataFrame
        df = pd.DataFrame(history_data)
        
        # Rename columns to standard O/H/L/C
        # KIS keys: stck_oprc, stck_hgpr, stck_lwpr, stck_clpr, acml_vol
        rename_map = {
            "stck_oprc": "open", "stck_hgpr": "high", "stck_lwpr": "low",
            "stck_clpr": "close", "acml_vol": "volume", "stck_bsop_date": "date"
        }
        df = df.rename(columns=rename_map)
        
        # Type Conversion
        cols = ['open', 'high', 'low', 'close', 'volume']
        for c in cols:
            df[c] = df[c].astype(float)
            
        # Set Index
        df['datetime'] = pd.to_datetime(df['date'], format='%Y%m%d')
        df = df.set_index('datetime')
        df = df.sort_index()

        # B. Run Multiplex Engine
        # Note: We are feeding Daily Data as 1-min data for simulation 
        # (Since we don't have 1-min history API easily in KIS for 5 years without paid plan/restrictions)
        # The Engine is robust enough to handle 1D as base if we treat it carefully, 
        # BUT MultiplexEngine expects 1-min to resample UP. 
        # If we feed Daily, Resampling to 5min is impossible. 
        # **Simulation Tweak**: We will assume this IS the base data. 
        # For meaningful testing, we need Intraday. 
        # Since KIS API heavily limits Intraday history, we will perform a 'Daily Strategy Check' 
        # using the engine's 1D frame.
        
        analysis = engine.analyze_ticker(code, df, news_sentiment=0.5)
        
        results.append({
            "market": "KR",
            "code": code,
            "decision": analysis["decision"],
            "consensus": analysis["consensus_ratio"],
            "oracle": analysis["oracle_confidence"],
            "bet_size": analysis["recommended_bet_size"],
            "reason": analysis["reason"]
        })
        
        # Rate Limit Mitigation
        await asyncio.sleep(0.2) 

    # --- PROCESSING US STOCKS (Mock/Partial) ---
    logger.info(">>> Processing US Market...")
    # US API implementation is still Mock in Wrapper, so this will verify logic flow.
    # In 'Real' run, we need KIS US Access Token.
    
    # ... (Similar loop for US if enabled) ...

    # 4. Report Generation
    res_df = pd.DataFrame(results)
    
    if res_df.empty:
        logger.error("❌ No valid results generated.")
        return

    logger.info("\n" + "="*50)
    logger.info("       MULTIPLEX SIMULATION REPORT        ")
    logger.info("="*50)
    logger.info(f"Total Reviewed: {len(res_df)}")
    logger.info(f"BUY Signals: {len(res_df[res_df['decision'] == 'BUY'])}")
    logger.info("="*50)
    
    # Save Report
    report_path = "simulation_report_phase45.csv"
    res_df.to_csv(report_path, index=False)
    logger.info(f"📄 Full Report Saved to: {os.path.abspath(report_path)}")
    
    # Show Top Picks
    buys = res_df[res_df['decision'] == 'BUY']
    if not buys.empty:
        print("\n[📢 DETECTED OPPORTUNITIES (MULTIPLEX CONFIRMED)]")
        print(buys[['market', 'code', 'consensus', 'oracle', 'bet_size', 'reason']].to_string())
    else:
        print("\n[⚠️ NO BUY SIGNALS - MARKET IS DANGEROUS]")

if __name__ == "__main__":
    asyncio.run(run_mass_simulation())
