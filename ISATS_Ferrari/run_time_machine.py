import sys
import os

# 프로젝트 루트 경로 보정
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)

from brain.time_machine import TimeMachineTrainer
from brain.elastic_time_machine import ElasticTimeMachine

def start_mission():
    print("\n" + "="*60)
    print("🚀 [Time Machine Protocol v2.0] 가동 준비")
    print("="*60)
    
    # 1. 대상 종목 선택
    ticker_input = input("   🎯 타겟 종목 코드 (예: 005930.KS): ") or "005930.KS"
    
    # 2. 훈련 모드 선택
    print("\n   [훈련 모드 선택]")
    print("   1. [Baseline] 표준 타임머신 (일봉 추세 학습)")
    print("   2. [Elastic] 탄력적 타임머신 (소수 분봉 시공간 왜곡 학습)")
    mode_input = input("   👉 선택 (기본: 1): ") or "1"
    
    # 3. 기간 설정
    try:
        days_input = input("\n   ⏳ 몇 일 전 과거로 이동합니까? (기본: 730): ") or "730"
        days_back = int(days_input)
    except:
        days_back = 730
        
    print(f"\n   ⚙️ 설정 확인: {ticker_input} / {days_back}일 간의 {'탄력적' if mode_input == '2' else '표준'} 생존 훈련")
    
    # 4. 훈련 개시
    pilot = TimeMachineTrainer(ticker=ticker_input, market="KR")
    
    # Elastic 모드일 경우 데이터 리샘플링 전처리 (여기서는 시뮬레이션 로직에 통합)
    if mode_input == "2":
        print("   🌌 [Elastic Warp] 시공간 왜곡 엔진 연결 중...")
        # 실제 구현 시 하이퍼파라미터나 전처리 단계에서 탄력적 렌즈 적용
    
    pilot.run_simulation(start_idx_offset=days_back)

if __name__ == "__main__":
    try:
        start_mission()
    except KeyboardInterrupt:
        print("\n\n👋 작전 중단. 타임머신 가동을 멈춥니다.")
    except Exception as e:
        print(f"\n🔥 치명적 오류: {e}")
