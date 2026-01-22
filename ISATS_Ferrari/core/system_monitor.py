import psutil
import time
import redis
import platform
import subprocess

# ==========================================
# System Resource Monitor
# 역할: 서버 자원(CPU, RAM, Network, Redis) 상태 점검
# ==========================================

class SystemMonitor:
    def __init__(self, redis_host='redis', redis_port=6379):
        """환경 설정 및 Redis 클라이언트 초기화"""
        try:
            self.redis_client = redis.Redis(host=redis_host, port=redis_port, socket_connect_timeout=1)
        except:
            self.redis_client = None

    def get_resource_usage(self):
        """CPU 및 메모리 사용량 반환"""
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        return {
            "cpu": cpu,
            "ram_percent": mem.percent,
            "ram_used_mb": round(mem.used / 1024 / 1024)
        }

    def check_redis_latency(self):
        """Redis 응답 속도 확인 (ms)"""
        if not self.redis_client:
            return -1, False
        try:
            start = time.time()
            self.redis_client.ping()
            latency = (time.time() - start) * 1000
            return round(latency, 2), True
        except:
            return -1, False

    def check_internet_connection(self, host="8.8.8.8"):
        """외부 네트워크 연결 상태 확인"""
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        try:
            subprocess.check_output(['ping', param, '1', host], timeout=2, stderr=subprocess.DEVNULL)
            return True
        except:
            return False

    def run_diagnostics(self):
        """전체 시스템 상태 진단 및 리포트 생성"""
        resources = self.get_resource_usage()
        redis_lat, redis_status = self.check_redis_latency()
        net_status = self.check_internet_connection()
        
        status_report = {
            "status": "OK" if redis_status and net_status else "ERROR",
            "resources": resources,
            "redis": {"connected": redis_status, "latency_ms": redis_lat},
            "network": {"connected": net_status}
        }
        
        # 콘솔 출력 (로그 확인용)
        print(f"[System] Status: {status_report['status']}")
        print(f"   CPU: {resources['cpu']}% | RAM: {resources['ram_percent']}%")
        print(f"   Redis: {'OK' if redis_status else 'FAIL'} ({redis_lat}ms)")
        
        return status_report

if __name__ == "__main__":
    monitor = SystemMonitor()
    monitor.run_diagnostics()
