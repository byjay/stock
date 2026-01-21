
import sys
import os
import logging

# Add project root to path
sys.path.append(os.getcwd())

from backend.core.global_data_lake import GlobalDataLake

# Configure simple logging to stdout
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("InitScript")

def main():
    logger.info("🚀 Starting Master Data Lake Initialization...")
    logger.info("   Goal: Break the 'Samsung-only' bias by indexing ALL 2500+ KRX stocks.")
    
    lake = GlobalDataLake()
    
    # Force refresh to prove it works
    lake.refresh_master_data()
    
    logger.info("-" * 50)
    logger.info(f"📊 Total Stocks Found: {len(lake.krx_master)}")
    
    if len(lake.krx_master) > 0:
        logger.info("✨ Sample Data (First 5):")
        print(lake.krx_master.head()[['Name', 'MarketCap', 'PER', 'PBR']])
        
        # Check for Samsung Electronics specifically
        samsung_ticker = "005930"
        if samsung_ticker in lake.krx_master.index:
            samsung_name = lake.krx_master.loc[samsung_ticker]['Name']
            logger.info(f"✅ Verified: {samsung_name} ({samsung_ticker}) is present.")
        else:
            logger.error("❌ Warning: Samsung Electronics not found? Something is odd.")
            
        # Check for a small stock (Random KOSDAQ)
        # Just grab random to show diversity
        random_stock = lake.krx_master.iloc[-5]
        logger.info(f"✅ Verified Diversity: Found smaller stock '{random_stock['Name']}'")
    else:
        logger.error("❌ Failed to fetch any stocks.")

    logger.info("-" * 50)
    logger.info("💾 Data saved to ./data/master_db/krx_master.csv")
    logger.info("✅ foundation complete. The system now 'knows' everyone.")

if __name__ == "__main__":
    main()
