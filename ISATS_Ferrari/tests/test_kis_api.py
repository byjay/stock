import aiohttp
import asyncio
import yaml
import json
import os
import sys
import time

# ==========================================
# 🇰🇷 KIS (한국투자증권) API 연결 정밀 진단기
# ==========================================

async def test_kis_connectivity():
    print("\n" + "="*50)
    print("      📡 KIS (Korea Investment) API TEST      ")
    print("="*50)

    # 1. 비밀 파일(secrets.yaml) 수색
    print("🔍 [Step 1] 설정 파일 찾는 중...")
    
    # 가능한 모든 경로 후보
    possible_paths = [
        "secrets.yaml",
        "config/secrets.yaml",
        "../secrets.yaml",
        "../isats/secrets.yaml",
        "../../isats/secrets.yaml",
        "ISATS_Ferrari/config/secrets.yaml"
    ]
    
    config_path = None
    for path in possible_paths:
        if os.path.exists(path):
            config_path = path
            print(f"   ✅ 발견: {os.path.abspath(path)}")
            break
            
    if not config_path:
        print("❌ [Error] 'secrets.yaml' 파일을 찾을 수 없습니다!")
        print("   -> ISATS_Ferrari/config/ 폴더 안에 넣어주세요.")
        return

    # 2. 설정 로드
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            
        # 키 확인 (구조가 다를 수 있어 안전하게 get 사용)
        app_key = config.get("key", {}).get("kis_app_key") or config.get("kis_app_key")
        app_secret = config.get("key", {}).get("kis_secret_key") or config.get("kis_secret_key")
        mode = config.get("system", {}).get("mode", "REAL") # REAL or VIRTUAL
        
        if not app_key or not app_secret:
            print("❌ [Error] yaml 파일 안에 'kis_app_key' 또는 'kis_secret_key'가 비어있습니다.")
            return

        # 모의투자(VIRTUAL) vs 실전투자(REAL) URL 구분
        if mode == "REAL":
            base_url = "https://openapi.koreainvestment.com:9443"
            print("   🌐 모드: 실전 투자 (REAL)")
        else:
            base_url = "https://openapivts.koreainvestment.com:29443"
            print("   🌐 모드: 모의 투자 (VIRTUAL)")
            
    except Exception as e:
        print(f"❌ [Error] yaml 파싱 실패: {e}")
        return

    # 3. 네트워크 통신 테스트
    print("\n📡 [Step 2] 서버 통신 시도...")
    
    auth_url = f"{base_url}/oauth2/tokenP"
    payload = {
        "grant_type": "client_credentials",
        "appkey": app_key,
        "appsecret": app_secret
    }
    
    timeout = aiohttp.ClientTimeout(total=5) # 5초 타임아웃 (무한대기 방지)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            start_time = time.time()
            print(f"   -> 접속 시도: {auth_url}")
            
            async with session.post(auth_url, json=payload) as resp:
                elapsed = time.time() - start_time
                print(f"   -> 응답 시간: {elapsed:.2f}초")
                
                if resp.status == 200:
                    res_data = await resp.json()
                    token = res_data.get('access_token')
                    expired = res_data.get('access_token_token_expired')
                    
                    print("\n🎉 [Success] 연결 성공!")
                    print(f"   🔑 Access Token 발급 완료 (길이: {len(token)})")
                    print(f"   ⏰ 토큰 만료 일시: {expired}")
                    print("   -> 페라리의 연료 주입구가 정상 작동합니다.")
                else:
                    text = await resp.text()
                    print(f"\n⛔ [Fail] 서버 거부 (상태코드: {resp.status})")
                    print(f"   -> 메시지: {text}")
                    
    except asyncio.TimeoutError:
        print("\n🔥 [Timeout] 5초 동안 응답이 없습니다. (방화벽/인터넷 확인 필요)")
    except Exception as e:
        print(f"\n🔥 [Error] 통신 중 치명적 오류: {e}")

if __name__ == "__main__":
    # 윈도우 환경에서 aiohttp 멈춤 현상 해결을 위한 필수 코드
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    asyncio.run(test_kis_connectivity())
