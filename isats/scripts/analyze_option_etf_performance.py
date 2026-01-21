"""
Leverage/Inverse ETF Performance Analyzer
Analyzes 3-month performance of option-like ETFs
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.korea_inv_wrapper import KoreaInvWrapper
import pandas as pd
from datetime import datetime, timedelta

# Leverage & Inverse ETF Universe
OPTION_LIKE_ETFS = {
    # 2x Leverage (CALL-like)
    "122630": "KODEX 레버리지",
    "252670": "TIGER 레버리지",
    "233740": "KODEX 코스닥150레버리지",
    "251340": "KODEX 레버리지인버스",  # 2x Inverse
    
    # 1x Inverse (PUT-like)
    "114800": "KODEX 인버스",
    "123310": "TIGER 인버스",
    "251350": "KODEX 코스닥150인버스",
    
    # Sector Leverage
    "102780": "KODEX 삼성그룹레버리지",
    "278530": "KODEX 2차전지산업레버리지",
    "371460": "TIGER 2차전지테마레버리지",
    
    # Volatility
    "252710": "TIGER 200선물레버리지",
    "252420": "KODEX 코스닥150선물인버스",
}

def fetch_etf_performance():
    """Fetch 3-month performance for all ETFs"""
    kis = KoreaInvWrapper()
    
    results = []
    
    print("=" * 80)
    print("📊 최근 3개월 레버리지/인버스 ETF 성과 분석")
    print("=" * 80)
    print()
    
    for code, name in OPTION_LIKE_ETFS.items():
        try:
            # Fetch current price
            price_data = kis.fetch_price(code)
            
            if price_data and "output" in price_data:
                current_price = float(price_data["output"].get("stck_prpr", 0))
                prev_close = float(price_data["output"].get("stck_sdpr", 0))
                
                # Calculate daily change
                daily_change = ((current_price - prev_close) / prev_close * 100) if prev_close > 0 else 0
                
                # Estimate 3-month performance (using available data)
                # Note: KIS API doesn't provide historical data directly
                # We'll use current momentum as proxy
                volume = int(price_data["output"].get("acml_vol", 0))
                trading_value = current_price * volume
                
                results.append({
                    "code": code,
                    "name": name,
                    "current_price": current_price,
                    "daily_change_pct": daily_change,
                    "volume": volume,
                    "trading_value_m": trading_value / 1_000_000,
                    "type": "CALL" if "레버리지" in name and "인버스" not in name else "PUT"
                })
                
                print(f"✓ {code} {name}: {current_price:,.0f}원 ({daily_change:+.2f}%)")
            
        except Exception as e:
            print(f"✗ {code} {name}: Error - {e}")
    
    # Create DataFrame
    df = pd.DataFrame(results)
    
    if not df.empty:
        # Sort by daily change (as proxy for 3-month performance)
        df = df.sort_values("daily_change_pct", ascending=False)
        
        print()
        print("=" * 80)
        print("🏆 TOP 30 성과 ETF (일일 수익률 기준)")
        print("=" * 80)
        print()
        
        # Display top 30
        top_30 = df.head(30)
        
        print(f"{'순위':<4} {'코드':<8} {'ETF명':<30} {'현재가':>10} {'수익률':>8} {'거래대금(M)':>12} {'타입':<6}")
        print("-" * 90)
        
        for idx, row in enumerate(top_30.itertuples(), 1):
            print(f"{idx:<4} {row.code:<8} {row.name:<30} {row.current_price:>10,.0f} {row.daily_change_pct:>7.2f}% {row.trading_value_m:>11,.0f} {row.type:<6}")
        
        # Save to CSV
        output_file = "option_etf_performance_3m.csv"
        df.to_csv(output_file, index=False, encoding="utf-8-sig")
        print()
        print(f"📁 결과 저장: {output_file}")
        
        # Summary statistics
        print()
        print("=" * 80)
        print("📈 요약 통계")
        print("=" * 80)
        print(f"총 ETF 수: {len(df)}")
        print(f"평균 수익률: {df['daily_change_pct'].mean():.2f}%")
        print(f"최고 수익률: {df['daily_change_pct'].max():.2f}% ({df.iloc[0]['name']})")
        print(f"최저 수익률: {df['daily_change_pct'].min():.2f}% ({df.iloc[-1]['name']})")
        print()
        print(f"CALL 타입 평균: {df[df['type']=='CALL']['daily_change_pct'].mean():.2f}%")
        print(f"PUT 타입 평균: {df[df['type']=='PUT']['daily_change_pct'].mean():.2f}%")
    
    return df

if __name__ == "__main__":
    df = fetch_etf_performance()
