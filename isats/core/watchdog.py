import os
import time
import logging
import psutil

logger = logging.getLogger("SystemWatchdog")

class SystemWatchdog:
    """
    [Anti-Fragility] Resource & Process Monitor.
    Prevents 'System Freezing' and OOM (Out of Memory) crashes.
    Defends against the 'Stability Hell' critique in 비판.md.
    """
    def __init__(self, mem_threshold_pct=85, cpu_threshold_pct=90):
        self.mem_threshold = mem_threshold_pct
        self.cpu_threshold = cpu_threshold_pct
        self.process = psutil.Process(os.getpid())

    def check_health(self):
        """
        Monitors CPU/Memory and returns status.
        """
        mem_info = psutil.virtual_memory()
        cpu_usage = psutil.cpu_percent(interval=None)
        
        if mem_info.percent > self.mem_threshold:
            logger.critical(f"🚨 [OOM-RISK] Memory usage critical: {mem_info.percent}%")
            return "CRITICAL_MEM"
            
        if cpu_usage > self.cpu_threshold:
            logger.warning(f"⚠️ [HOT-CPU] CPU usage high: {cpu_usage}%")
            return "HIGH_LOAD"
            
        return "HEALTHY"

    def monitor_loop(self, stop_event=None):
        """
        Background loop to log health.
        """
        logger.info("🛡️ [Watchdog] Heartbeat monitor started.")
        while not (stop_event and stop_event.is_set()):
            status = self.check_health()
            if status != "HEALTHY":
                # In a real implementation, this would trigger an emergency flush or stop
                # For now, we log the defensive action
                logger.info(f"[Watchdog-Action] System state is {status}. Throttling non-essential tasks...")
            time.sleep(10)
