# -*- coding: utf-8 -*-
"""
계좌 잔고 조회 테스트 (오류 수정 버전)
"""
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from core.kis_official_api import KISUnifiedClient


def safe_int(value, default=0):
    """안전한 정수 변환"""
    try:
        return int(value) if value and str(value).strip() else default
    except (ValueError, TypeError):
        return default


def safe_float(value, default=0.0):
    """안전한 실수 변환"""
    try:
        return float(value) if value and str(value).strip() else default
    except (ValueError, TypeError):
        return default


def check_all_accounts():
    print("=" * 70)
    print("📊 전체 계좌 잔고 조회")
    print("=" * 70)
    
    # 1. 모의투자 계좌
    print("\n🔵 [모의투자 계좌]")
    print("-" * 70)
    
    try:
        virtual_client = KISUnifiedClient(mode="virtual")
        virtual_client.initialize()
        
        holdings, summary = virtual_client.get_balance(market="KR")
        
        if not holdings.empty:
            print(f"\n보유 종목: {len(holdings)}개")
            print("\n{:<10} {:<20} {:>10} {:>15} {:>10}".format(
                "종목코드", "종목명", "수량", "평가금액", "손익률"
            ))
            print("-" * 70)
            
            for _, row in holdings.iterrows():
                ticker = row.get("pdno", row.get("PDNO", ""))
                name = row.get("prdt_name", row.get("PRDT_NAME", ""))
                qty = safe_int(row.get("hldg_qty", row.get("HLDG_QTY", 0)))
                value = safe_int(row.get("evlu_amt", row.get("EVLU_AMT", 0)))
                profit_rate = safe_float(row.get("evlu_pfls_rt", row.get("EVLU_PFLS_RT", 0)))
                
                if ticker:
                    print(f"{ticker:<10} {name:<20} {qty:>10} {value:>15,} {profit_rate:>9.2f}%")
        else:
            print("보유 종목 없음")
        
        if summary:
            print("\n📈 계좌 요약:")
            total = safe_int(summary.get("tot_evlu_amt", summary.get("TOT_EVLU_AMT", 0)))
            profit = safe_int(summary.get("evlu_pfls_smtl_amt", summary.get("EVLU_PFLS_SMTL_AMT", 0)))
            print(f"  총 평가금액: {total:,}원")
            print(f"  평가손익: {profit:+,}원")
    
    except Exception as e:
        print(f"❌ 조회 실패: {e}")
    
    # 2. 실전 계좌
    print("\n\n🔴 [실전투자 계좌]")
    print("-" * 70)
    
    try:
        real_client = KISUnifiedClient(mode="real")
        real_client.initialize()
        
        holdings, summary = real_client.get_balance(market="KR")
        
        if not holdings.empty:
            print(f"\n보유 종목: {len(holdings)}개")
            print("\n{:<10} {:<20} {:>10} {:>15} {:>10}".format(
                "종목코드", "종목명", "수량", "평가금액", "손익률"
            ))
            print("-" * 70)
            
            for _, row in holdings.iterrows():
                ticker = row.get("pdno", row.get("PDNO", ""))
                name = row.get("prdt_name", row.get("PRDT_NAME", ""))
                qty = safe_int(row.get("hldg_qty", row.get("HLDG_QTY", 0)))
                value = safe_int(row.get("evlu_amt", row.get("EVLU_AMT", 0)))
                profit_rate = safe_float(row.get("evlu_pfls_rt", row.get("EVLU_PFLS_RT", 0)))
                
                if ticker:
                    print(f"{ticker:<10} {name:<20} {qty:>10} {value:>15,} {profit_rate:>9.2f}%")
        else:
            print("보유 종목 없음")
        
        if summary:
            print("\n📈 계좌 요약:")
            total = safe_int(summary.get("tot_evlu_amt", summary.get("TOT_EVLU_AMT", 0)))
            profit = safe_int(summary.get("evlu_pfls_smtl_amt", summary.get("EVLU_PFLS_SMTL_AMT", 0)))
            print(f"  총 평가금액: {total:,}원")
            print(f"  평가손익: {profit:+,}원")
    
    except Exception as e:
        print(f"❌ 조회 실패: {e}")
    
    # 3. 해외주식 잔고 (모의)
    print("\n\n🌍 [해외주식 잔고 - 모의투자]")
    print("-" * 70)
    
    try:
        holdings, summary = virtual_client.get_balance(market="US")
        
        if not holdings.empty:
            print(f"\n보유 종목: {len(holdings)}개")
            for _, row in holdings.iterrows():
                print(row)
        else:
            print("해외 보유 종목 없음")
    
    except Exception as e:
        print(f"❌ 조회 실패: {e}")
    
    print("\n" + "=" * 70)
    print("✅ 조회 완료")
    print("=" * 70)


if __name__ == "__main__":
    check_all_accounts()

