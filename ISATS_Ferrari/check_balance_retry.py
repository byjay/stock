import asyncio
import sys
import os
import time

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.kis_api_client import KISAPIClient

async def persistent_balance_check():
    """성공할 때까지 무한 재시도하는 잔고 조회 루프"""
    print("\n" + "="*60)
    print("🚀 [ISATS] 실전 계좌 연동 무한 재시도 모드 가동 (Target: 74493388-01)")
    print("="*60 + "\n")
    
    client = KISAPIClient()
    retry_count = 0
    
    while True:
        try:
            retry_count += 1
            if not client.session or client.session.closed:
                await client.initialize()
            
            print(f"🔄 [{time.strftime('%H:%M:%S')}] 시도 #{retry_count}: 토큰 발급 및 잔고 조회 중...")
            
            # 토큰 발급 시도 (이미 KISAPIClient.initialize 내에서 수행되지만 명시적 확인)
            token_ok = await client.get_access_token()
            if not token_ok:
                print("   ⚠️ 토큰 발급 실패 (403 Forbidden 등 권한 확인 필요)")
                await asyncio.sleep(10)
                continue

            # 잔고 조회 시도
            balance = await client.get_balance()
            if balance:
                print("\n" + "✨"*30)
                print(f"🎯 [연동 성공! 실전 계좌: 74493388-01]")
                print(f"   • 총 평가금액: {balance['total_value']:,.0f} 원")
                print(f"   • 총 예수금:   {balance['cash']:,.0f} 원")
                print(f"   • 총 수익금:   {balance['profit']:,.0f} 원")
                print(f"   • 총 수익률:   {balance['profit_pct']:.2f} %")
                print("✨"*30 + "\n")
                
                if balance['positions']:
                    print("📦 [보유 종목 리스트]")
                    for pos in balance['positions']:
                        print(f"   - {pos['name']} ({pos['ticker']}): {pos['qty']}주 | {pos['profit_pct']:.2f}%")
                
                break # 성공 시 루프 탈출
            else:
                print("   ⚠️ 잔고 조회 응답 없음 (데이터 파싱 오류 가능성)")
                
        except Exception as e:
            print(f"   ❌ 오류 발생: {e}")
        
        await asyncio.sleep(10) # 10초 대기 후 재시도

    if client.session:
        await client.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(persistent_balance_check())
    except KeyboardInterrupt:
        print("\n\n👋 [ISATS] 사용자에 의해 중단되었습니다.")
