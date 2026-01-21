
import FinanceDataReader as fdr
import pandas as pd
import json
import os
from datetime import datetime

OUTPUT_DIR = "backend/data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "market_master.json")
SECTOR_FILE = os.path.join(OUTPUT_DIR, "market_sectors.json")

def fetch_market_master():
    print("🚀 [Step 1] Fetching KRX Stock Listing (KOSPI + KOSDAQ + KONEX)...")
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # 1. Fetch Full Listing
    df_krx = fdr.StockListing('KRX')
    print(f"   - Total Listed: {len(df_krx)}")

    # 2. Fetch Administration Issues (Gwanli Jongmok)
    print("🚀 [Step 2] Fetching Administration/Halting Issues...")
    admin_codes = set()
    try:
        df_admin = fdr.StockListing('KRX-ADMIN') # Manage/Admin Stocks
        if df_admin is not None and not df_admin.empty:
            admin_codes.update(df_admin['Symbol'].tolist())
            print(f"   - Administration Stocks Found: {len(df_admin)}")
    except Exception as e:
        print(f"   - Warning: Could not fetch 'KRX-ADMIN' ({e}). Skipping admin check.")

    # 3. Process Data
    print("🚀 [Step 3] Processing & Enriching Data...")
    
    master_list = []
    sector_map = {}

    for _, row in df_krx.iterrows():
        code = str(row['Code'])
        name = row['Name']
        market = row['Market']
        try:
            sector = row['Sector'] if pd.notna(row.get('Sector')) else "Unknown"
        except:
            sector = "Unknown"
            
        try:
            industry = row['Industry'] if pd.notna(row.get('Industry')) else "Unknown"
        except:
             industry = "Unknown"

        is_admin = code in admin_codes
        
        # Determine Status
        status = "NORMAL"
        if is_admin:
            status = "ADMIN"
        # We assume active trading if in standard list, but 'ADMIN' is a risk flag.
        
        stock_info = {
            "code": code,
            "name": name,
            "market": market,
            "sector": sector,
            "industry": industry,
            "status": status,
            "updated_at": datetime.now().strftime("%Y-%m-%d")
        }
        master_list.append(stock_info)

        # Categorize by Sector
        if sector not in sector_map:
            sector_map[sector] = []
        sector_map[sector].append({
            "code": code,
            "name": name,
            "market": market
        })

    # 4. Save to JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(master_list, f, ensure_ascii=False, indent=2)
    
    with open(SECTOR_FILE, "w", encoding="utf-8") as f:
        json.dump(sector_map, f, ensure_ascii=False, indent=2)

    print(f"✅ Successfully saved {len(master_list)} stocks to {OUTPUT_FILE}")
    print(f"✅ Categorized into {len(sector_map)} sectors in {SECTOR_FILE}")

    # Summary Stats
    kospi_count = len([x for x in master_list if x['market'] == 'KOSPI'])
    kosdaq_count = len([x for x in master_list if x['market'] == 'KOSDAQ'])
    print("="*30)
    print(f"KOSPI : {kospi_count}")
    print(f"KOSDAQ: {kosdaq_count}")
    print(f"ADMIN : {len(admin_codes)}")
    print("="*30)

if __name__ == "__main__":
    fetch_market_master()
