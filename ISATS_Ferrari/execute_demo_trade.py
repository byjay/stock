import asyncio
import json
from core.dual_engine_manager import DualEngineManager

async def run_demo():
    print("🚀 [ISATS Ferrari v7.0] 매매 데모를 시작합니다.")
    manager = DualEngineManager()
    
    # 1. 시스템 초기화 (실전 계좌 연동 실패해도 가상 매매는 계속)
    try:
        await manager.setup_clients()
    except Exception as e:
        print(f"⚠️ KIS API 연결 제외 (가상 모드로 계속): {e}")
    
    # 2. 타겟 설정 (Screening Top 1)
    ticker = "009520" # 애니젠
    name = "애니젠"
    price = 18310
    qty = 10 
    
    print(f"🎯 타겟 종목: {name} ({ticker}) | 주문가: {price} | 수량: {qty}")
    
    # 3. 가상 엔진(Virtual) 매매 실행
    print(f"🛠️ Virtual Engine에 매수 주문을 전송합니다...")
    result = await manager.execute_order(
        ticker=ticker,
        action="BUY",
        requested_price=price,
        requested_quantity=qty,
        engine_type="virtual"
    )
    
    if result:
        print(f"✅ 가상 매매 성공!")
        # 잔고 업데이트 및 상태 확인
        await manager.update_balances()
        status = manager.get_status()
        
        virtual_pos = status['positions']['virtual']
        print("\n📊 가상 포트폴리오 현황:")
        if not virtual_pos:
            print(" - 보유 종목 없음")
        else:
            for symbol, quantity in virtual_pos.items():
                print(f" - {symbol}: {quantity}주")
            
        print(f"\n💰 가상 계좌 잔고: {status['balances']['virtual']:,} KRW")
    else:
        print(f"❌ 매매 실패: 잔고 부족 또는 유동성 매칭 실패")

if __name__ == "__main__":
    asyncio.run(run_demo())
