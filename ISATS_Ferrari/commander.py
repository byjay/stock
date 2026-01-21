import subprocess
import time
import os
import sys
import signal

# 경로 보정: ISATS_Ferrari 폴더를 path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# ==========================================
# 🎖️ ISATS Ferrari 통합 지휘 통제소 (Commander)
# ==========================================

# 하위 프로세스 관리용 리스트
procs = []

def log(step, msg):
    print(f"\n[{step}] {'='*40}")
    print(f"   📢 {msg}")
    print(f"[{step}] {'='*40}\n")

def run_step(script_path, step_name, wait=True):
    """
    개별 작전을 수행하는 함수
    wait=True: 해당 작업이 끝날 때까지 기다림 (채굴, 학습)
    wait=False: 백그라운드에서 실행해두고 다음으로 넘어감 (수집기)
    """
    full_path = os.path.join(os.getcwd(), script_path)
    
    if not os.path.exists(full_path):
        print(f"❌ [Error] 파일이 없습니다: {script_path}")
        print(f"   경로: {full_path}")
        return False

    cmd = [sys.executable, script_path]
    
    if wait:
        log(step_name, "작전 개시! (완료될 때까지 대기합니다)")
        try:
            subprocess.run(cmd, check=True)
            print(f"   ✅ {step_name} 임무 완수.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"   🔥 {step_name} 작전 실패! (Exit Code: {e.returncode})")
            return False
    else:
        log(step_name, "백그라운드 투입! (다음 단계로 즉시 이동)")
        p = subprocess.Popen(cmd)
        procs.append(p)
        time.sleep(1)  # 프로세스 시작 대기
        return True

def kill_all_processes():
    """종료 시 백그라운드 프로세스들도 함께 사살"""
    print("\n🛑 [Shutdown] 전 병력 철수 명령 하달...")
    for p in procs:
        p.terminate()
        try:
            p.wait(timeout=3)
        except:
            p.kill()
    print("   👋 모든 프로세스가 안전하게 종료되었습니다.")

def main_operation():
    print("\n" + "="*60)
    print("⭐⭐⭐ ISATS FERRARI FULL OPERATION START ⭐⭐⭐")
    print("="*60)
    
    # 현재 위치 확인
    current_dir = os.getcwd()
    print(f"📂 작전 기지: {current_dir}\n")
    
    # ---------------------------------------------------------
    # Phase 0: GUI 대시보드 가동 (백그라운드)
    # ---------------------------------------------------------
    dashboard_path = "dashboard/server.py"
    if os.path.exists(dashboard_path):
        run_step(dashboard_path, "Phase 0: GUI 대시보드 가동", wait=False)
    else:
        print("⚠️ [Warning] GUI 대시보드를 찾을 수 없습니다. 스킵합니다.")
    
    # ---------------------------------------------------------
    # Phase 1: 데이터 채굴 (Mining)
    # ---------------------------------------------------------
    # 이미 데이터가 있다면 스킵 가능
    data_exists = os.path.exists("data/KR") and len(os.listdir("data/KR")) > 10
    
    if data_exists:
        print("✅ [Skip] 데이터가 이미 충분합니다. 채굴 단계를 건너뜁니다.\n")
    else:
        if not run_step("utils/mass_data_miner.py", "Phase 1: 대규모 데이터 채굴"):
            print("⚠️ 채굴 실패했지만 계속 진행합니다...")

    # ---------------------------------------------------------
    # Phase 2: AI 학습 (Training)
    # ---------------------------------------------------------
    # 이미 학습된 모델이 있다면 스킵 가능
    model_exists = os.path.exists("brain/weights") and len(os.listdir("brain/weights")) > 0
    
    if model_exists:
        print("✅ [Skip] 학습된 모델이 이미 존재합니다. 훈련 단계를 건너뜁니다.\n")
    else:
        if not run_step("brain/trainer.py", "Phase 2: Deep Eyes 신경망 훈련"):
            print("⚠️ 훈련 실패했지만 계속 진행합니다...")

    # ---------------------------------------------------------
    # Phase 3: 실시간 수집 (Collection) - 백그라운드
    # ---------------------------------------------------------
    # realtime_collector가 없다면 스킵
    if os.path.exists("core/realtime_collector.py"):
        run_step("core/realtime_collector.py", "Phase 3: 실시간 수집기 가동", wait=False)
    else:
        print("⚠️ [Warning] 실시간 수집기를 찾을 수 없습니다. 스킵합니다.\n")
    
    time.sleep(2)

    # ---------------------------------------------------------
    # Phase 4: 메인 엔진 가동 (Trading)
    # ---------------------------------------------------------
    log("Phase 4", "메인 엔진 점화! (Ctrl+C로 전체 종료)")
    try:
        subprocess.run([sys.executable, "main.py"], check=True)
    except KeyboardInterrupt:
        print("\n⚠️ 사용자에 의한 중단 요청")
    except Exception as e:
        print(f"🔥 엔진 오류: {e}")
    finally:
        kill_all_processes()

if __name__ == "__main__":
    try:
        main_operation()
    except KeyboardInterrupt:
        print("\n⚠️ 긴급 중단!")
        kill_all_processes()
    except Exception as e:
        print(f"\n🔥 치명적 오류: {e}")
        kill_all_processes()
