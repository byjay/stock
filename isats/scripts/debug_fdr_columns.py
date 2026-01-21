
import FinanceDataReader as fdr
import pandas as pd

def debug_columns():
    # 1. Check KRX (Standard)
    print("--- KRX ---")
    try:
        df = fdr.StockListing('KRX')
        print(df.columns.tolist())
    except:
        print("KRX Failed")

    # 2. Check NASDAQ (US)
    print("\n--- NASDAQ ---")
    try:
        df = fdr.StockListing('NASDAQ')
        print(df.columns.tolist())
        print(df.head(1).to_string())
    except:
        print("NASDAQ Failed")

    # 3. Check ETF/KR
    print("\n--- ETF/KR ---")
    try:
        df = fdr.StockListing('ETF/KR')
        print(df.columns.tolist())
    except:
        pass

if __name__ == "__main__":
    debug_columns()
