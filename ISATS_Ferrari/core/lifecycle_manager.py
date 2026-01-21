import subprocess
import time
import os
import sys
import schedule
import asyncio
from datetime import datetime
from utils.notifier import TelegramBot

# ==========================================
# 🧬 FERRARI LIFECYCLE MANAGER (심장 박동기)
# ==========================================

class LifecycleManager:
    def __init__(self):
        self.bot = TelegramBot()
        self.main_proc = None
        self.running = True
        
    def log(self, msg):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_msg = f"[{timestamp}] {msg}"
        print(full_msg)
        asyncio.run(self.bot.send(msg))

    def run_process(self, script_path, wait=True):
        """스크립트 실행"""
        cmd = [sys.executable, script_path]
        try:
            if wait:
                self.log(f"🎬 작전 개시: {script_path}")
                subprocess.run(cmd, check=True)
                return True
            else:
                self.log(f"🚀 백그라운드 투입: {script_path}")
                return subprocess.Popen(cmd)
        except Exception as e:
            self.log(f"🔥 작전 실패 ({script_path}): {e}")
            return None

    def start_engine(self):
        """메인 매매 엔진 시동"""
        if self.main_proc and self.main_proc.poll() is None:
            self.log("⚠️ 이미 엔진이 가동 중입니다.")
            return

        self.log("🏎️ 페라리 엔진 시동 (Main Operation)")
        self.main_proc = self.run_process("main.py", wait=False)

    def stop_engine(self):
        """엔진 정지"""
        if self.main_proc and self.main_proc.poll() is None:
            self.log("🛑 엔진 정지 및 장부 정리...")
            self.main_proc.terminate()
            try:
                self.main_proc.wait(timeout=10)
            except:
                self.main_proc.kill()
            self.main_proc = None

    def daily_evolution(self):
        """매일 아침 수행하는 진화 작업 (08:30)"""
        self.log("🧬 진화의 시간: 장 전 재학습 및 업데이트 개시")
        
        self.stop_engine()
        
        # 1. 최신 상한가/이슈 종목 스캔
        self.run_process("utils/upper_limit_scanner.py")
        
        # 2. 데이터 채굴 (최근 데이터 보강)
        self.run_process("utils/mass_data_miner.py")
        
        # 3. AI 재학습 (진화)
        self.run_process("brain/trainer.py")
        
        self.log("✅ 진화 완료. 새로운 두뇌로 재부팅합니다.")
        self.start_engine()

    def check_health(self):
        """엔진 생존 확인 및 심폐소생술"""
        if self.main_proc and self.main_proc.poll() is not None:
            self.log("⚠️ 경고: 엔진이 비정상 종료되었습니다. 재점화합니다.")
            self.start_engine()

    def run(self):
        self.log("🏁 ISATS Ferrari 무한 진화 시스템 가동")
        
        # 0. 초기 가동
        self.start_engine()
        
        # 1. 스케줄 등록: 매일 오전 08:30 진화 작전
        schedule.every().day.at("08:30").do(self.daily_evolution)
        
        # 2. 메인 감시 루프
        try:
            while self.running:
                schedule.run_pending()
                self.check_health()
                time.sleep(10) # 10초마다 상태 체크
        except KeyboardInterrupt:
            self.log("👋 사령관님 명령으로 시스템을 종료합니다.")
            self.stop_engine()
            self.running = False

if __name__ == "__main__":
    manager = LifecycleManager()
    manager.run()
