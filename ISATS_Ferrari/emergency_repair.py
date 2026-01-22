"""
🛠️ ISATS v6.0 EMERGENCY REPAIR KIT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

작전명: "Fix Broken Parts Automatically"

역할:
- secrets.yaml 자동 생성 (템플릿)
- daily_target_list.csv 자동 생성 (스캐너 실행)
- 시스템 복구 자동화

작성자: ISATS Neural Swarm
버전: 6.0 (Emergency Repair)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import sys
import yaml
import subprocess
import time

# ==========================================
# 🛠️ ISATS v6.0 EMERGENCY REPAIR KIT
# "Fix Broken Parts Automatically"
# ==========================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def fix_auth():
    """1. 인증 파일(secrets.yaml) 복구"""
    config_dir = os.path.join(BASE_DIR, "config")
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
        print("   📂 'config' 폴더 생성 완료.")

    secrets_path = os.path.join(config_dir, "secrets.yaml")
    
    if not os.path.exists(secrets_path):
        print("   ⚠️ 'secrets.yaml' 미발견. 기본 템플릿을 생성합니다...")
        
        template = {
            "key": {
                "kis_app_key": "YOUR_APP_KEY_HERE",
                "kis_secret_key": "YOUR_SECRET_KEY_HERE",
                "account_no": "YOUR_ACCOUNT_NO"
            },
            "system": {
                "mode": "VIRTUAL"  # 안전을 위해 모의투자 기본
            },
            "telegram": {
                "token": "",
                "chat_id": ""
            }
        }
        
        with open(secrets_path, "w", encoding="utf-8") as f:
            yaml.dump(template, f, default_flow_style=False, allow_unicode=True)
            
        print(f"   ✅ [FIXED] 'config/secrets.yaml' 생성 완료!")
        print("      -> 주의: 파일 열어서 실제 키를 입력해야 작동합니다.")
    else:
        print("   ✅ [OK] 'secrets.yaml'이 이미 존재합니다.")


def fix_storage():
    """2. 타겟 리스트(Storage) 복구"""
    target_path = os.path.join(BASE_DIR, "daily_target_list.csv")
    
    if not os.path.exists(target_path):
        print("\n   ⚠️ 'daily_target_list.csv' 미발견. 스캐너를 가동합니다...")
        
        # 데이터 폴더 확인
        data_dir = os.path.join(BASE_DIR, "data", "KR")
        if not os.path.exists(data_dir) or not os.listdir(data_dir):
            print("   ❌ [CRITICAL] 'data/KR' 폴더가 비어있습니다!")
            print("      -> 먼저 'utils/universal_data_collector.py'를 실행해 데이터를 수집하세요.")
            return

        # 스캐너 실행
        scanner_script = os.path.join(BASE_DIR, "core", "auto_market_scanner.py")
        try:
            print("   🚀 Auto Scanner 가동 중 (잠시 대기)...")
            subprocess.run([sys.executable, scanner_script], check=True)
            print("   ✅ [FIXED] 타겟 리스트 생성 완료!")
        except Exception as e:
            print(f"   ❌ 스캐너 실행 실패: {e}")
    else:
        print("   ✅ [OK] 'daily_target_list.csv'가 이미 존재합니다.")


def main():
    print("\n" + "="*80)
    print("      🛠️  ISATS v6.0 EMERGENCY REPAIR SEQUENCE      ")
    print("="*80)
    
    print("\n[Step 1] 보안/인증(Auth) 수리")
    fix_auth()
    
    print("\n[Step 2] 저장소(Storage) 수리")
    fix_storage()
    
    print("\n" + "="*80)
    print("🎉 수리 완료. 다음 단계:")
    print("1. 'ISATS_Ferrari/config/secrets.yaml' 파일을 열어 API 키 입력")
    print("2. 'tests/verify_full_system.py'를 다시 실행하여 All Pass 확인")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
