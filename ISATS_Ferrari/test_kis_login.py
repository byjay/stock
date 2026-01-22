"""
KIS API 로그인 테스트 스크립트
"""
import asyncio
import sys
import os

# UTF-8 인코딩 강제 설정 (Windows 콘솔 문제 해결)
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

# 프로젝트 루트 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.kis_api_client import KISAPIClient

async def test_login():
    """KIS API 로그인 테스트"""
    print("="*80)
    print("[TEST] KIS API 로그인 테스트 시작")
    print("="*80)

    try:
        # KIS API 클라이언트 생성
        client = KISAPIClient()

        print(f"\n[INFO] 계좌 정보:")
        print(f"  - 계좌번호: {client.account_no}-{client.prdt_cd}")
        print(f"  - 모드: {client.mode}")
        print(f"  - API Key: {client.app_key[:10]}...{client.app_key[-5:]}")
        print(f"  - Base URL: {client.base_url}")

        # 초기화 (토큰 발급)
        print(f"\n[INFO] 토큰 발급 시도 중...")
        await client.initialize()

        if client.access_token:
            print(f"\n[SUCCESS] 로그인 성공!")
            print(f"  - Access Token: {client.access_token[:20]}...{client.access_token[-10:]}")

            # 잔고 조회 테스트
            print(f"\n[INFO] 잔고 조회 테스트 중...")
            balance = await client.get_balance()

            if balance:
                print(f"\n[SUCCESS] 잔고 조회 성공!")
                print(f"  - 총 평가금액: {balance.get('total_value', 0):,.0f}원")
                print(f"  - 예수금: {balance.get('cash', 0):,.0f}원")
                print(f"  - 평가손익: {balance.get('profit', 0):,.0f}원")
                print(f"  - 보유 종목 수: {len(balance.get('positions', []))}개")
            else:
                print(f"\n[WARNING] 잔고 조회 실패 (API 응답 없음)")
        else:
            print(f"\n[ERROR] 로그인 실패 - 토큰을 받지 못했습니다")

        # 세션 종료
        await client.close()

        print(f"\n" + "="*80)
        print("[TEST] 테스트 완료")
        print("="*80)

    except Exception as e:
        print(f"\n[ERROR] 예외 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_login())
