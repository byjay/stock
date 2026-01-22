import asyncio
import os
import sys
import pandas as pd

# 모듈 경로 보정
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from core.auto_market_scanner import AutoScanner
from core.watchers import SniperAgent, ScoutAgent, PatrolAgent
from core.system_monitor import SystemMonitor

# ==========================================
# ISATS Main Engine
# 역할: 시스템 초기화 및 감시 에이전트 실행 조율
# ==========================================

class MainEngine:
    def __init__(self):
        """기본 설정 및 모니터 초기화"""
        self.target_file = "daily_target_list.csv"
        self.targets = {'S': [], 'A': [], 'B': []}
        self.monitor = SystemMonitor()

    def initialize(self):
        """시스템 부팅 및 사전 점검"""
        print("[Boot] ISATS Engine initializing...")
        
        # 1. 핵심 하드웨어/네트워크 자원 진단
        status = self.monitor.run_diagnostics()
        if status['status'] != 'OK':
            print("❌ 초기화 실패: 시스템 리소스 혹은 네트워크 상태를 점검하십시오.")
            return False
            
        # 2. 공략 종목 리스트 확인 및 스캔
        if not os.path.exists(self.target_file):
            print("⚠️ 타겟 리스트가 없습니다. 실시간 스캐너를 가동합니다...")
            try:
                # 스캐너 인스턴스 실행
                scanner = AutoScanner()
                scanner.run_scan()
            except Exception as e:
                print(f"⚠️ 스캐너 실행 중 오류 발생: {e}")
        
        return self._load_targets()

    def _load_targets(self):
        """리스트에서 등급별 전술적 타겟 분배"""
        try:
            if not os.path.exists(self.target_file):
                 raise FileNotFoundError("타겟 파일 부재")
                 
            df = pd.read_csv(self.target_file)
            # Tier 분배 규정 (Top 3: S, 4~10: A, 이후: B)
            self.targets['S'] = df.iloc[:3]['Ticker'].tolist()
            self.targets['A'] = df.iloc[3:10]['Ticker'].tolist()
            self.targets['B'] = df.iloc[10:20]['Ticker'].tolist()
            
            print(f"✅ 타겟 로드 완료: S({len(self.targets['S'])}), A({len(self.targets['A'])}), B({len(self.targets['B'])})")
            return True
        except Exception as e:
            print(f"❌ 타겟 파일 분석 실패: {e}. 기본 관찰 종목으로 전환합니다.")
            self.targets['S'] = ["005930.KS"] # 예시 (삼성전자)
            return True

    async def run_loop(self):
        """등급별 전술 에이전트 병렬 기동"""
        print("[Engine] 전술 에이전트 그룹(Sniper, Scout, Patrol) 기동 중...")
        
        # 등급별 특화 에이전트 인스턴스 생성
        sniper = SniperAgent(self.targets['S'])
        scout = ScoutAgent(self.targets['A'])
        patrol = PatrolAgent(self.targets['B'])
        
        try:
            # 병렬 감시 시작
            await asyncio.gather(
                sniper.run(),
                scout.run(),
                patrol.run()
            )
        except KeyboardInterrupt:
            print("\n[Engine] 중단 요청 수신. 안전 종료 절차를 시작합니다.")

    def start(self):
        """메인 엔진 서비스 시작"""
        if self.initialize():
            try:
                # 에이전트 루프 진입
                if os.name == 'nt':
                    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
                asyncio.run(self.run_loop())
            except KeyboardInterrupt:
                pass

if __name__ == "__main__":
    engine = MainEngine()
    engine.start()
