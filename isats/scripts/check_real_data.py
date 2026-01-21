import sys
import os
import logging
from backend.core.korea_inv_wrapper import KoreaInvWrapper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RealDataCheck")

def check_real_data_access():
    """
    Try to fetch REAL historical data for a few stocks to verify API access.
    """
    broker = KoreaInvWrapper()
    
    # Real tickers: Samsung Elec, SK Hynix, Naver, Kakao, EcoPro BM
    test_tickers = ["005930", "000660", "035420", "035720", "247540"]
    
    success_count = 0
    for code in test_tickers:
        logger.info(f"Fetching Real History for {code}...")
        try:
            # Fetch 30-minute candles for the last few days
            # '30' is 30-minute, period depends on API limits, trying to get enough.
            # Wrapper daily default seems to be 'D'. Let's try to pass params if possible or use default.
            df = broker.fetch_history(code, timeframe="30", period_code="30") 
            
            if df is not None and not df.empty:
                logger.info(f"✅ Success! Got {len(df)} rows for {code}.")
                logger.info(f"   Sample: {df.head(1).to_dict()}")
                success_count += 1
            else:
                logger.error(f"❌ Failed to get data for {code} (Empty).")
                
        except Exception as e:
            logger.error(f"❌ Exception fetching {code}: {e}")

    if success_count == len(test_tickers):
        print("\nSUCCESS: Real data access confirmed for all test tickers.")
    elif success_count > 0:
        print(f"\nPARTIAL SUCCESS: {success_count}/{len(test_tickers)} accessed.")
    else:
        print("\nFAILURE: Could not access real data. Check API/Auth.")

if __name__ == "__main__":
    check_real_data_access()
