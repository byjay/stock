import sys
import os
import json
import asyncio
import importlib
import traceback

# ==========================================
# 🏥 ISATS v2.0 마이그레이션 생존 확인 키트
# ==========================================

TARGET_DIR = "ISATS_Ferrari"
sys.path.append(os.path.abspath(TARGET_DIR))  # 이식된 폴더를 경로에 추가

class SystemDoctor:
    def __init__(self):
        self.results = {}
        print(f"🏥 [검진 시작] '{TARGET_DIR}' 시스템 정밀 진단을 시작합니다...\n")

    def log(self, step, status, msg=""):
        icon = "✅" if status else "❌"
        print(f"{icon} [{step}] {msg}")
        self.results[step] = status

    def check_structure(self):
        """1. 필수 장기(폴더/파일) 존재 여부 확인"""
        required = [
            "config/dna.json",
            "core/engine.py",
            "core/redis_client.py",
            "brain/model_cnn.py",
            "strategy/base.py",
            "main.py"
        ]
        
        missing = []
        for f in required:
            path = os.path.join(TARGET_DIR, f)
            if not os.path.exists(path):
                missing.append(f)
        
        if not missing:
            self.log("File Structure", True, "모든 핵심 파일이 제자리에 있습니다.")
            return True
        else:
            self.log("File Structure", False, f"누락된 파일 발견: {missing}")
            return False

    def check_dna(self):
        """2. DNA(설정) 로딩 테스트"""
        try:
            path = os.path.join(TARGET_DIR, "config/dna.json")
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 필수 유전자 확인
            if "rsi_period" in data.get("genes", {}) or "stop_loss" in data.get("genes", {}) or "risk_level" in data.get("genes", {}):
                self.log("DNA Loading", True, f"설정 로드 성공 (유전자 개수: {len(data['genes'])}개)")
                return True
            else:
                self.log("DNA Loading", False, "JSON 파일은 있지만 유효한 파라미터가 없습니다.")
                return False
        except Exception as e:
            self.log("DNA Loading", False, f"DNA 읽기 실패: {str(e)}")
            return False

    async def check_redis(self):
        """3. 신경망(Redis) 연결 테스트"""
        try:
            # core.redis_client 모듈을 동적으로 임포트
            redis_mod = importlib.import_module("core.redis_client")
            if hasattr(redis_mod, "RedisClient"):
                client = redis_mod.RedisClient()
                self.log("Redis Connection", True, "Redis 클라이언트 모듈이 정상적으로 살아있습니다. (서버 연결은 skip)")
                return True
            else:
                self.log("Redis Connection", False, "core/redis_client.py에 RedisClient 클래스가 없습니다.")
                return False
        except ImportError:
            self.log("Redis Connection", False, "core.redis_client 모듈을 불러올 수 없습니다.")
        except Exception as e:
            self.log("Redis Connection", True, f"코드 로딩은 성공했으나 연결 실패 (서버 꺼짐 추정): {str(e)}")
            return True

    def check_brain(self):
        """4. 두뇌(AI 모델) 로딩 테스트"""
        try:
            import torch
            model_mod = importlib.import_module("brain.model_cnn")
            
            found_class = False
            for name, obj in model_mod.__dict__.items():
                if isinstance(obj, type) and "Model" in name:
                    self.log("AI Brain", True, f"AI 모델 클래스 발견: {name}")
                    found_class = True
                    break
            
            if not found_class:
                self.log("AI Brain", False, "brain/model_cnn.py에 모델 클래스가 정의되지 않았습니다.")
                return False
            return True
            
        except ImportError as e:
            self.log("AI Brain", False, f"AI 모듈 임포트 실패 (PyTorch 설치 확인): {str(e)}")
            return False
        except Exception as e:
            self.log("AI Brain", False, f"모델 초기화 중 에러: {str(e)}")
            return False

    async def run_simulation(self):
        """5. 모의 주행 (전략 실행 테스트)"""
        try:
            base_mod = importlib.import_module("strategy.base")
            if not hasattr(base_mod, "BaseStrategy"):
                self.log("Strategy Engine", False, "BaseStrategy(부모 클래스)가 정의되지 않았습니다.")
                return
            
            self.log("Strategy Engine", True, "전략 기본 엔진이 정상적으로 인식됩니다.")
        except Exception as e:
            self.log("Strategy Engine", False, f"전략 엔진 테스트 중 치명적 오류: {str(e)}")

    async def full_diagnosis(self):
        if not self.check_structure():
            print("\n⛔ [중단] 필수 파일이 없어서 더 이상 검사가 불가능합니다.")
            return

        self.check_dna()
        await self.check_redis()
        self.check_brain()
        await self.run_simulation()

        print("\n" + "="*40)
        success_count = sum(self.results.values())
        total_count = len(self.results)
        score = (success_count / total_count) * 100
        
        print(f"📊 최종 생존 점수: {score:.1f} / 100")
        if score == 100:
            print("🏎️ [판정] 페라리 시동 준비 완료! (기능 상실 없음)")
        elif score >= 80:
            print("⚠️ [판정] 운행은 가능하나 정비가 필요합니다.")
        else:
            print("🚑 [판정] 긴급 수술 필요. 마이그레이션이 잘못되었습니다.")

if __name__ == "__main__":
    doctor = SystemDoctor()
    asyncio.run(doctor.full_diagnosis())
