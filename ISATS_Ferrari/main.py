import asyncio
import os
import sys

# 경로 설정: 현재 폴더를 패키지 경로로 인식
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from strategy.active_bot import ActiveBot

async def main_engine():
    print("\n" + "="*50)
    print("      🏎️  ISATS v2.0 'FERRARI' IGNITION SEQUENCE      ")
    print("="*50)
    
    # 1. 전략(운전자) 탑승
    try:
        bot = ActiveBot()
        print(f"✅ [Driver] 전략 '{bot.name}' 초기화 완료.")
        print(f"   -> 현재 DNA: {bot.params}")
    except Exception as e:
        print(f"❌ [Error] 전략 초기화 실패: {e}")
        return

    # 2. 데이터 수집기(연료 펌프) 연결 확인
    data_dir = "data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print("⛽ [Fuel] 데이터 저장소가 비어있어 새로 생성했습니다.")
    else:
        print(f"⛽ [Fuel] 데이터 저장소 연결됨 ({len(os.listdir(data_dir))} files).")

    print("\n🚀 [System] 엔진 시동 중... (Ctrl+C로 종료)")
    await asyncio.sleep(1) # 부팅 연출
    
    # 3. 메인 루프 (무한 주행)
    loop_count = 0
    try:
        while True:
            # A. 시장 데이터 수집 (실제 구현 시 Redis에서 가져옴)
            market_data = None # 현재는 더미
            
            # B. 두뇌 판단
            decision = await bot.analyze(market_data)
            
            # C. 생존 신고 (로그) - 너무 자주 뜨지 않게 5초마다
            if loop_count % 5 == 0:
                print(f"   ⏱️ [Loop {loop_count}] 상태: 정상 | 판단: {decision} | 진화 대기 중...")
            
            loop_count += 1
            await asyncio.sleep(1) # 1초 틱

    except KeyboardInterrupt:
        print("\n🛑 [Stop] 사용자에 의한 엔진 정지.")
    except Exception as e:
        print(f"\n🔥 [Crash] 치명적 오류 발생: {e}")

if __name__ == "__main__":
    # 윈도우 비동기 루프 정책 설정 (필요시)
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    asyncio.run(main_engine())
