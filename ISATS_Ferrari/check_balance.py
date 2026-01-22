import asyncio
import sys
import os

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.kis_api_client import KISAPIClient

async def check_account_balance():
    """실전 계좌 잔고 조회 및 보고"""
    print("\n" + "="*50)
    print("🚀 [ISATS] 실전 계좌 잔고 조회 시작...")
    print("="*50 + "\n")
    
    client = KISAPIClient()
    try:
        await client.initialize()
        balance = await client.get_balance()
        
        if balance:
            print(f"📊 [계좌 요약: {client.account_no}-{client.prdt_cd}]")
            print(f"   • 총 평가금액: {balance['total_value']:,.0f} 원")
            print(f"   • 총 예수금:   {balance['cash']:,.0f} 원")
            print(f"   • 총 수익금:   {balance['profit']:,.0f} 원")
            print(f"   • 총 수익률:   {balance['profit_pct']:.2f} %")
            print("\n📦 [보유 종목]")
            
            if not balance['positions']:
                print("   - 현재 보유 중인 종목이 없습니다.")
            else:
                for pos in balance['positions']:
                    print(f"   - {pos['name']} ({pos['ticker']})")
                    print(f"     수량: {pos['qty']} | 수익률: {pos['profit_pct']:.2f}% | 수익금: {pos['profit']:,.0f}원")
        else:
            print("❌ 잔고 데이터를 수신하지 못했습니다. (API 응답 오류)")
            
    except Exception as e:
        print(f"❌ 조회 중 오류 발생: {e}")
    finally:
        if client.session:
            await client.session.close()
    
    print("\n" + "="*50)

if __name__ == "__main__":
    asyncio.run(check_account_balance())
