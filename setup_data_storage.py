import os
import json
import shutil

# ==========================================
# ⛽ ISATS v2.0 데이터 저장소 구축 및 연결
# ==========================================

BASE_DIR = "ISATS_Ferrari"
OLD_DIR = "isats_legacy"  # 이전에 사용하던 폴더가 있다면 이름을 맞춥니다.

def create_storage_bunkers():
    """데이터를 담을 폴더 생성"""
    directories = [
        "data",            # CSV 등 Raw Data
        "database",        # SQLite 등
        "brain/weights",   # 모델 가중치 파일
        "logs"             # 실행 로그
    ]
    
    print("🏗️ [저장소 구축] 데이터 벙커를 생성합니다...")
    for d in directories:
        path = os.path.join(BASE_DIR, d)
        os.makedirs(path, exist_ok=True)
        print(f"   📂 생성 완료: {path}")

def update_dna_paths():
    """DNA(설정파일)에 데이터 경로 등록"""
    dna_path = os.path.join(BASE_DIR, "config/dna.json")
    
    # DNA 파일이 없으면 기본 생성
    if not os.path.exists(dna_path):
        print("   ⚠️ DNA 파일이 없어 기본 템플릿을 생성합니다.")
        dna = {"genes": {"rsi_period": 14}}
    else:
        with open(dna_path, 'r', encoding='utf-8') as f:
            dna = json.load(f)
    
    # 경로 정보 주입
    dna["paths"] = {
        "training_data": "./data",
        "model_save": "./brain/weights",
        "logs": "./logs"
    }
    
    with open(dna_path, 'w', encoding='utf-8') as f:
        json.dump(dna, f, indent=4, ensure_ascii=False)
    
    print("🧬 [DNA 업데이트] 데이터 경로가 설정 파일에 각인되었습니다.")

def find_and_suggest_migration():
    """옛날 폴더에서 가져올만한 데이터 탐색"""
    print("\n🔍 [보물 찾기] 기존 폴더에서 중요한 데이터 파일을 탐색합니다...")
    
    valuable_extensions = ['.csv', '.pth', '.pt', '.h5', '.db', '.sqlite']
    found_files = []

    # root_dir 수준에서 예전 폴더 탐색
    search_targets = ["isats", "archived", "data_collectors"] 
    
    for target in search_targets:
        if os.path.exists(target):
            for root, dirs, files in os.walk(target):
                for f in files:
                    ext = os.path.splitext(f)[1]
                    if ext in valuable_extensions:
                        full_path = os.path.join(root, f)
                        if "venv" not in full_path and "__pycache__" not in full_path:
                            found_files.append(full_path)
    
    if found_files:
        print(f"   💎 발견된 중요 데이터 ({len(found_files)}개):")
        for f in found_files[:5]: # 5개만 예시로 출력
            print(f"      - {f}")
        if len(found_files) > 5:
            print(f"      ...외 {len(found_files)-5}개")
        print("\n   💡 팁: 위 파일들을 'ISATS_Ferrari/data' 또는 'brain/weights'로 수동 복사하세요.")
    else:
        print("   ❓ 기존 폴더에서 명확한 데이터 파일을 찾지 못했습니다. (직접 확인 필요)")

if __name__ == "__main__":
    create_storage_bunkers()
    update_dna_paths()
    find_and_suggest_migration()
    print("\n✅ [완료] 엔진과 연료 탱크 연결 준비 끝.")
