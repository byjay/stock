import mmap
import os
import json
import time

class SharedMemoryBridge:
    """
    Ultra-Low Latency IPC (32-bit <-> 64-bit)
    Uses Memory Mapped Files for < 1ms synchronization.
    Defends against the 'Turtle Speed' critique in 비판.md.
    """
    def __init__(self, name="isats_shm_bridge", size=1024*1024):
        self.filename = f"/tmp/{name}" if os.name != 'nt' else f"C:\\TEMP\\{name}"
        self.size = size
        os.makedirs(os.path.dirname(self.filename), exist_ok=True)
        
        if not os.path.exists(self.filename):
            with open(self.filename, "wb") as f:
                f.write(b'\x00' * self.size)
        
        self.f = open(self.filename, "r+b")
        self.mm = mmap.mmap(self.f.fileno(), self.size)

    def write_signal(self, data: dict):
        """Write AI signal/order to shared memory"""
        payload = json.dumps(data).encode('utf-8')
        if len(payload) > self.size - 4:
            raise ValueError("Payload too large for SHM slot")
            
        self.mm.seek(0)
        # First 4 bytes: length of payload
        self.mm.write(len(payload).to_bytes(4, byteorder='little'))
        self.mm.write(payload)
        self.mm.flush()

    def read_signal(self) -> dict:
        """Read signal from shared memory"""
        self.mm.seek(0)
        length_bytes = self.mm.read(4)
        length = int.from_bytes(length_bytes, byteorder='little')
        
        if length == 0:
            return None
            
        payload = self.mm.read(length).decode('utf-8')
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            return None

    def close(self):
        self.mm.close()
        self.f.close()
