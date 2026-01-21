
import os
from datetime import datetime
import shutil

class LiveMDLogger:
    """
    Writes real-time trading and analysis logs to Markdown files.
    Implements Dual-Storage (Local & Simulated Cloud/Server).
    """
    def __init__(self):
        # 1. Define Dual Paths
        self.local_path = r"c:\Users\FREE\Desktop\주식\LIVE_TRADING_LOG.md"
        self.server_path = r"c:\Users\FREE\Desktop\주식\isats\backend\cloud\LIVE_TRADING_LOG_BACKUP.md"
        
        # Ensure server directory exists
        os.makedirs(os.path.dirname(self.server_path), exist_ok=True)
        
        # Initialize File if not exists
        if not os.path.exists(self.local_path):
            self._write_header()

    def _write_header(self):
        header = f"""# 🟢 LIVE TRADING SESSION LOG
**Session Start:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Market:** US Stock Market (NASDAQ/NYSE)
**Mode:** AI Autonomous Trading (Evidence-Based)

---

| Timestamp | Type | Symbol | Price | Action/Analysis | Evidence Hash |
| :--- | :--- | :--- | :--- | :--- | :--- |
"""
        self._append(header)

    def log_execution(self, trade_data):
        """Log a executed trade"""
        ts = datetime.now().strftime('%H:%M:%S')
        symbol = trade_data.get('symbol')
        price = trade_data.get('price')
        action = trade_data.get('action', 'BUY') # Default to BUY if missing
        
        # Handle Evidence: Dict or String
        raw_evidence = trade_data.get('evidence', 'N/A')
        
        if isinstance(raw_evidence, dict):
            # Format: "Ask:$186.25 (x100) | Bid:$186.20"
            ask_p = raw_evidence.get('ask')
            bid_p = raw_evidence.get('bid')
            
            # Formatting nicely for Markdown Table
            if ask_p and bid_p:
                evidence_str = f"Ask:${ask_p} | Bid:${bid_p}"
            else:
                evidence_str = f"Snapshot:{raw_evidence.get('price')}"
        else:
            evidence_str = str(raw_evidence)
        
        row = f"| **{ts}** | 🔴 **TRADE** | `{symbol}` | `${price}` | **{action} EXECUTED** | `{evidence_str}` |\n"
        self._append(row)

    def log_analysis(self, symbol, result, score, details):
        """Log analysis result (even if not traded)"""
        ts = datetime.now().strftime('%H:%M:%S')
        # Only log significant checks to avoid spamming
        icon = "🟡" if result == "WATCH" else "⚪"
        
        row = f"| {ts} | {icon} SCAN | `{symbol}` | - | Score: {score:.2f} ({details}) | - |\n"
        self._append(row)

    def _append(self, content):
        try:
            # 1. Write to Local
            with open(self.local_path, "a", encoding="utf-8") as f:
                f.write(content)
            
            # 2. Write to Server (Sync)
            with open(self.server_path, "a", encoding="utf-8") as f:
                f.write(content)
                
        except Exception as e:
            print(f"⚠️ [MDLogger] Write Error: {e}")

# Singleton Instance
md_logger = LiveMDLogger()
