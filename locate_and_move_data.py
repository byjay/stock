import os
import shutil
import time

# ==========================================
# 🕵️♂️ ISATS v2.0 데이터 수색 및 구조대 (Data Rescue)
# ==========================================

# 1. 수색할 구역 (과거의 유산들)
SEARCH_ZONES = [
    "databases", 
    "data_collectors", 
    "isats", 
    "archived", 
    "models" # 혹시 models 폴더에 가중치가 있을 수 있음
]

# 2. 이송할 목적지 (새로운 차고)
DEST_DATA = "ISATS_Ferrari/data"
DEST_BRAIN = "ISATS_Ferrari/brain/weights"

# 3. 보물 지도 (찾아야 할 확장자)
TARGET_DATA_EXT = [".csv", ".xlsx", ".db", ".sqlite"]
TARGET_MODEL_EXT = [".pth", ".pt", ".h5"]

def rescue_mission():
    print("🚁 [작전 시작] 흩어진 데이터와 모델을 수색합니다...\n")
    
    found_data = 0
    found_models = 0
    
    # 목적지 폴더 확실히 생성
    os.makedirs(DEST_DATA, exist_ok=True)
    os.makedirs(DEST_BRAIN, exist_ok=True)

    # 현재 위치(루트) 기준 수색
    current_dir = os.getcwd()

    for zone in SEARCH_ZONES:
        zone_path = os.path.join(current_dir, zone)
        
        if not os.path.exists(zone_path):
            continue

        print(f"🔎 수색 중: {zone} 구역...")
        
        for root, dirs, files in os.walk(zone_path):
            # 가상환경, 캐시 폴더는 건너뜀
            if "venv" in root or "__pycache__" in root:
                continue

            for file in files:
                src_path = os.path.join(root, file)
                ext = os.path.splitext(file)[1].lower()
                
                # A. 학습 데이터 발견 (.csv, .db)
                if ext in TARGET_DATA_EXT:
                    # 너무 작은 파일(1KB 미만)은 설정 파일일 수 있으니 무시
                    if os.path.getsize(src_path) > 1024: 
                        dst_path = os.path.join(DEST_DATA, file)
                        # 중복 파일일 경우 덮어쓰거나 이름 변경 (여기선 덮어쓰기)
                        shutil.copy2(src_path, dst_path)
                        print(f"   📦 [데이터 확보] {file} -> {DEST_DATA}/")
                        found_data += 1

                # B. AI 모델 발견 (.pth)
                elif ext in TARGET_MODEL_EXT:
                    dst_path = os.path.join(DEST_BRAIN, file)
                    shutil.copy2(src_path, dst_path)
                    print(f"   🧠 [두뇌 확보] {file} -> {DEST_BRAIN}/")
                    found_models += 1

    print("\n" + "="*40)
    print(f"📊 작전 결과 보고:")
    print(f"   - 확보한 데이터 파일: {found_data}개")
    print(f"   - 확보한 모델 가중치: {found_models}개")
    
    if found_data == 0 and found_models == 0:
        print("\n⚠️ [경고] 수색 결과, 유의미한 데이터 파일을 찾지 못했습니다.")
        print("   -> 기존에 수집된 데이터가 없다면, 봇을 실행하여 새로 수집해야 합니다.")
    else:
        print("\n✅ [성공] 모든 연료와 두뇌 기억이 'ISATS_Ferrari'로 이송되었습니다.")

if __name__ == "__main__":
    rescue_mission()
