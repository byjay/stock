import asyncio
import sys
import os

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.kis_api_client import KISAPIClient

async def check_all_accounts():
    """스크린샷에서 확인된 모든 계좌의 잔고 조회"""
    accounts = [
        {"cano": "74505901", "prdt_cd": "01", "name": "위탁계좌 1"},
        {"cano": "74505901", "prdt_cd": "21", "name": "금융상품 계좌"},
        {"cano": "74493388", "prdt_cd": "01", "name": "위탁계좌 2 (현재 연동)"}
    ]
    
    print("\n" + "="*70)
    print("🚀 [ISATS] 사령관님 보유 전 계좌 자산 현황 조회 시작")
    print("="*70 + "\n")
    
    client = KISAPIClient()
    total_equity = 0
    
    try:
        await client.initialize()
        
        for acc in accounts:
            print(f"🔍 [{acc['name']}: {acc['cano']}-{acc['prdt_cd']}] 조회 중...")
            
            # 클라이언트 내부 파라미터 임시 변경 (조회용)
            # KISAPIClient 내부에서 CANO를 하드코딩한 부분을 우회하기 위해 
            # get_balance를 직접 호출하는 대신 params를 커스텀합니다.
            
            url = f"{client.base_url}/uapi/domestic-stock/v1/trading/inquire-balance"
            headers = client._get_headers("TTTC8434R")
            params = {
                "CANO": acc['cano'],
                "ACNT_PRDT_CD": acc['prdt_cd'],
                "AFHR_FLPR_YN": "N",
                "OFL_YN": "",
                "INQR_DVSN": "02",
                "UNPR_DVSN": "01",
                "FUND_STTL_ICLD_YN": "N",
                "FNCG_AMT_AUTO_RDPT_YN": "N",
                "PRCS_DVSN": "01",
                "CTX_AREA_FK100": "",
                "CTX_AREA_NK100": ""
            }
            
            async with client.session.get(url, headers=headers, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    # 기존 KISAPIClient의 파싱 로직 적용
                    output1 = data.get('output1', [])
                    output2_raw = data.get('output2', [])
                    output2 = output2_raw[0] if isinstance(output2_raw, list) and len(output2_raw) > 0 else (output2_raw if isinstance(output2_raw, dict) else {})
                    
                    cash = float(output2.get('dnca_tot_amt', 0))
                    eval_amt = float(output2.get('tot_evlu_amt', 0))
                    total_equity += eval_amt
                    
                    print(f"   • 총 평가금액: {eval_amt:,.0f} 원")
                    print(f"   • 예수금:     {cash:,.0f} 원")
                    if output1:
                        print(f"   • 보유 종목:  {len(output1)}건")
                    else:
                        print(f"   • 보유 종목 없음")
                else:
                    print(f"   ❌ 조회 실패 (Status: {resp.status})")
            print("-" * 40)

        print("\n" + "🏆" * 35)
        print(f"💰 전체 계좌 통합 자산 합계: {total_equity:,.0f} 원")
        print("🏆" * 35 + "\n")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    finally:
        if client.session:
            await client.session.close()

if __name__ == "__main__":
    asyncio.run(check_all_accounts())
