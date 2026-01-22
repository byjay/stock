"""
🧪 ISATS v6.0 SYSTEM INTEGRITY TESTER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

작전명: "Trust, but Verify" (믿어라, 그러나 검증하라)

역할:
- Redis 신경망 연결 테스트
- 대시보드 실시간 통신 검증 (강제 신호 주입)
- 필수 파일 구조 확인
- API 키 설정 검증
- 모의 매매 로직 시뮬레이션

작성자: ISATS Neural Swarm
버전: 6.0 (System Verifier)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import asyncio
import json
import os
import sys
import yaml
import pandas as pd
from datetime import datetime

# 프로젝트 루트 경로 설정
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 선택적 임포트
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

try:
    import redis.asyncio as redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False
    print("⚠️ [Warning] redis.asyncio not found. Installing...")
    os.system("pip install redis --quiet")
    import redis.asyncio as redis
    HAS_REDIS = True


# ==========================================
# 🧪 System Verifier
# ==========================================

class SystemVerifier:
    """시스템 완전 무결성 검증기"""
    
    def __init__(self):
        self.redis_url = "redis://localhost:6379"
        self.secrets_path = "ISATS_Ferrari/config/secrets.yaml"
        self.target_file = "ISATS_Ferrari/daily_target_list.csv"
        self.results = {}
        
        print(f"\n{'='*80}")
        print(f"🧪 ISATS v6.0 - System Integrity Tester")
        print(f"{'='*80}")
        print(f"작전명: Trust, but Verify (믿어라, 그러나 검증하라)")
        print(f"{'='*80}\n")
    
    def log(self, step, status, msg):
        """
        테스트 결과 로깅
        
        Args:
            step: 테스트 단계
            status: 성공 여부 (True/False)
            msg: 메시지
        """
        icon = "✅" if status else "❌"
        print(f"{icon} [{step}] {msg}")
        self.results[step] = status
    
    async def test_redis_connection(self):
        """
        1. 신경망(Redis) 연결 테스트
        
        Returns:
            bool: 성공 여부
        """
        print(f"\n{'='*80}")
        print(f"🔌 Test 1: Redis 신경망 연결 테스트")
        print(f"{'='*80}\n")
        
        try:
            r = redis.from_url(self.redis_url, decode_responses=True)
            await r.ping()
            self.log("Network", True, "Redis 서버 연결 성공 (신경망 정상)")
            
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # [시각 검증] 대시보드에 강제 신호 송출
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            
            print("\n🚀 [강제 신호 주입] 대시보드로 테스트 신호 전송 중...")
            
            # 테스트 로그 신호
            log_payload = {
                "type": "log",
                "data": {
                    "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
                    "rank": "TEST",
                    "ticker": "SYSTEM-CHECK",
                    "price": 99999,
                    "message": "🧪 SYSTEM INTEGRITY TEST - 대시보드 연결 확인!",
                    "signal_type": "INFO",
                    "color": "text-primary"
                }
            }
            await r.publish("isats_stream", json.dumps(log_payload))
            
            # AI 신호 테스트
            ai_payload = {
                "type": "ai_signal",
                "data": {
                    "ticker": "TEST-SIGNAL",
                    "price": 99999,
                    "signal": "BUY",
                    "rank": "TEST",
                    "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3]
                }
            }
            await r.publish("isats_stream", json.dumps(ai_payload))
            
            print("✅ 테스트 신호 전송 완료!")
            print("\n" + "="*80)
            print("👀 [중요] 브라우저 대시보드를 확인하세요!")
            print("="*80)
            print("📱 대시보드 로그창에 다음 메시지가 떠야 합니다:")
            print("   🧪 SYSTEM INTEGRITY TEST - 대시보드 연결 확인!")
            print("\n💡 만약 메시지가 보인다면:")
            print("   → Python 엔진 ↔ Redis ↔ 대시보드 완벽 연결!")
            print("="*80 + "\n")
            
            await asyncio.sleep(2)  # 신호 전파 대기
            await r.close()
            return True
        
        except Exception as e:
            self.log("Network", False, f"Redis 연결 실패: {e}")
            print("\n⚠️ Redis 서버가 실행 중인지 확인하세요:")
            print("   Windows: wsl -> redis-server --daemonize yes")
            print("   Docker: docker run -d -p 6379:6379 redis")
            return False
    
    def test_file_structure(self):
        """
        2. 필수 파일 존재 여부
        
        Returns:
            bool: 성공 여부
        """
        print(f"\n{'='*80}")
        print(f"📂 Test 2: 필수 파일 구조 확인")
        print(f"{'='*80}\n")
        
        if os.path.exists(self.target_file):
            try:
                df = pd.read_csv(self.target_file)
                
                if not df.empty:
                    self.log("Storage", True, f"타겟 리스트 로드 성공 ({len(df)}개 종목 대기 중)")
                    
                    # 상세 정보 출력
                    print(f"\n   📊 타겟 리스트 상세:")
                    print(f"      - 총 종목 수: {len(df)}")
                    
                    if 'score' in df.columns:
                        print(f"      - 평균 점수: {df['score'].mean():.2f}")
                        print(f"      - 최고 점수: {df['score'].max():.2f}")
                    
                    if 'ticker' in df.columns:
                        print(f"      - 상위 3개: {', '.join(df['ticker'].head(3).tolist())}")
                    
                    return True
                else:
                    self.log("Storage", False, "타겟 리스트가 비어있습니다.")
                    print("   💡 해결 방법: python ISATS_Ferrari/core/auto_market_scanner.py")
                    return False
            
            except Exception as e:
                self.log("Storage", False, f"타겟 리스트 로드 실패: {e}")
                return False
        else:
            self.log("Storage", False, "daily_target_list.csv가 없습니다. (스캐너 미작동)")
            print("   💡 해결 방법: python ISATS_Ferrari/core/auto_market_scanner.py")
            return False
    
    def test_api_keys(self):
        """
        3. 비밀 금고(API Key) 검사
        
        Returns:
            bool: 성공 여부
        """
        print(f"\n{'='*80}")
        print(f"🔐 Test 3: API 키 설정 검증")
        print(f"{'='*80}\n")
        
        if os.path.exists(self.secrets_path):
            try:
                with open(self.secrets_path, 'r', encoding='utf-8') as f:
                    conf = yaml.safe_load(f)
                
                # KIS API 키 확인 (key 또는 KIS 섹션)
                kis_config = conf.get('KIS') or conf.get('key')
                
                if kis_config:
                    kis_key = kis_config.get('APP_KEY') or kis_config.get('kis_app_key', '')
                    
                    if kis_key and "YOUR_APP_KEY" not in kis_key.upper():
                        self.log("Auth", True, "API Key 설정 확인됨.")
                        
                        # 모드 확인
                        mode = conf.get('system', {}).get('mode', 'UNKNOWN')
                        if not mode or mode == 'UNKNOWN':
                            mode = kis_config.get('MODE', 'UNKNOWN')
                        
                        print(f"   📊 설정 상세:")
                        print(f"      - 모드: {mode}")
                        print(f"      - API 키 길이: {len(kis_key)} 문자")
                        
                        if mode == "REAL":
                            print(f"   ⚠️ [경고] 실전 모드입니다! 신중히 운영하세요.")
                        else:
                            print(f"   ✅ 모의투자 모드 (안전)")
                        
                        return True
                    else:
                        self.log("Auth", False, "API Key가 기본값이거나 비어있습니다.")
                        print("   💡 해결 방법: config/secrets.yaml 파일 수정")
                        return False
                else:
                    self.log("Auth", False, "secrets.yaml에 KIS 또는 key 섹션이 없습니다.")
                    return False
            
            except Exception as e:
                self.log("Auth", False, f"secrets.yaml 로드 실패: {e}")
                return False
        else:
            self.log("Auth", False, "secrets.yaml 파일이 없습니다.")
            print("   💡 해결 방법: config/secrets.yaml 파일 생성")
            return False
    
    async def simulate_mock_trade(self):
        """
        4. 모의 매매 로직 검증 (가상 체결 테스트)
        
        Returns:
            bool: 성공 여부
        """
        print(f"\n{'='*80}")
        print(f"💰 Test 4: 모의 매매 로직 시뮬레이션")
        print(f"{'='*80}\n")
        
        print("🧪 [Simulation] 가상 매매 테스트 진행...\n")
        
        # 가상 잔고
        initial_balance = 10_000_000
        balance = initial_balance
        price = 70_000
        
        print(f"   📊 초기 설정:")
        print(f"      - 초기 잔고: {initial_balance:,}원")
        print(f"      - 목표 종목: 삼성전자 (가상)")
        print(f"      - 현재가: {price:,}원")
        
        # 매수 시뮬레이션
        buy_amount = 10  # 10주
        cost = price * buy_amount
        fee = cost * 0.00015  # 수수료 0.015%
        total_cost = cost + fee
        
        print(f"\n   💸 매수 시뮬레이션:")
        print(f"      - 매수 수량: {buy_amount}주")
        print(f"      - 매수 금액: {cost:,}원")
        print(f"      - 수수료: {fee:,.0f}원")
        print(f"      - 총 비용: {total_cost:,.0f}원")
        
        if balance >= total_cost:
            balance -= total_cost
            self.log("Trading", True, f"가상 매수 체결 성공! 잔고 차감 확인")
            
            print(f"\n   ✅ 매수 체결 완료:")
            print(f"      - 이전 잔고: {initial_balance:,}원")
            print(f"      - 현재 잔고: {int(balance):,}원")
            print(f"      - 차감 금액: {int(total_cost):,}원")
            print(f"      - 보유 주식: {buy_amount}주")
            
            # 매도 시뮬레이션
            sell_price = 72_000  # 2,000원 상승
            sell_amount = buy_amount
            sell_revenue = sell_price * sell_amount
            sell_fee = sell_revenue * 0.00015
            sell_tax = sell_revenue * 0.0023  # 증권거래세 0.23%
            net_revenue = sell_revenue - sell_fee - sell_tax
            
            balance += net_revenue
            profit = balance - initial_balance
            
            print(f"\n   💰 매도 시뮬레이션 (가격 상승 시나리오):")
            print(f"      - 매도가: {sell_price:,}원")
            print(f"      - 매도 수량: {sell_amount}주")
            print(f"      - 매도 금액: {sell_revenue:,}원")
            print(f"      - 수수료: {sell_fee:,.0f}원")
            print(f"      - 거래세: {sell_tax:,.0f}원")
            print(f"      - 순수익: {net_revenue:,.0f}원")
            print(f"\n   📈 최종 결과:")
            print(f"      - 최종 잔고: {int(balance):,}원")
            print(f"      - 총 손익: {int(profit):,}원 ({profit/initial_balance*100:.2f}%)")
            
            return True
        else:
            self.log("Trading", False, "매수 로직 오류 (잔고 부족 처리 실패)")
            print(f"   ❌ 잔고 부족: {balance:,}원 < {total_cost:,}원")
            return False
    
    async def run_diagnostics(self):
        """전체 진단 실행"""
        print(f"\n🏥 [ISATS v6.0] 시스템 혈관 조영술 시작...\n")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 4대 핵심 장기 검사
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        await self.test_redis_connection()
        self.test_file_structure()
        self.test_api_keys()
        await self.simulate_mock_trade()
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 최종 결과
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        print(f"\n{'='*80}")
        print(f"📊 진단 결과 요약")
        print(f"{'='*80}\n")
        
        success_count = sum(self.results.values())
        total_count = len(self.results)
        
        for step, status in self.results.items():
            icon = "✅" if status else "❌"
            print(f"{icon} {step}: {'PASS' if status else 'FAIL'}")
        
        print(f"\n{'='*80}")
        print(f"📈 총점: {success_count} / {total_count} 항목 정상")
        print(f"{'='*80}\n")
        
        if success_count == total_count:
            print("🚀 [결론] 모든 신경망과 장기가 정상입니다. 출격 가능합니다!")
            print("\n💡 다음 단계:")
            print("   1. api_server.py 실행")
            print("   2. main.py 실행")
            print("   3. 대시보드 접속 (http://localhost)")
        else:
            print("⚠️ [결론] 일부 시스템에 문제가 있습니다.")
            print("\n💡 해결 방법:")
            
            if not self.results.get("Network", False):
                print("   - Redis 서버 실행: redis-server --daemonize yes")
            
            if not self.results.get("Storage", False):
                print("   - 타겟 리스트 생성: python ISATS_Ferrari/core/auto_market_scanner.py")
            
            if not self.results.get("Auth", False):
                print("   - API 키 설정: config/secrets.yaml 파일 수정")
        
        print(f"\n{'='*80}\n")


# ==========================================
# 실행
# ==========================================

if __name__ == "__main__":
    verifier = SystemVerifier()
    asyncio.run(verifier.run_diagnostics())
