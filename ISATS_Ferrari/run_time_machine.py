import sys
import os

# 모듈 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from brain.time_machine import TimeMachineTrainer

def start_mission():
    print("\n" + "="*60)
    print("🚀 [Time Machine Protocol v2.0] 가동 준비")
    print("="*60)
    
    # 1. 대상 종목 선택
    ticker_input = input("   🎯 타겟 종목 코드 (예: 005930.KS): ") or "005930.KS"
    
    # 2. 기간 설정 (몇 일 전으로 돌아갈지)
    try:
        days_input = input("   ⏳ 몇 일 전 과거로 이동합니까? (기본: 365): ") or "365"
        days_back = int(days_input)
    except:
        days_back = 365
        
    print(f"\n   ⚙️ 설정 확인: {ticker_input} / {days_back}일 간의 생존 훈련")
    
    # 3. 훈련 개시
    pilot = TimeMachineTrainer(ticker=ticker_input, market="KR")
    pilot.run_simulation(start_idx_offset=days_back)

if __name__ == "__main__":
    try:
        start_mission()
    except KeyboardInterrupt:
        print("\n\n👋 작전 중단. 타임머신 가동을 멈춥니다.")
    except Exception as e:
        print(f"\n🔥 치명적 오류: {e}")
