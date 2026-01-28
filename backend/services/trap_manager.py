import subprocess
import os
import signal
import json
import sys
from core.config import settings

class TrapManager:
    def __init__(self):
        self.process = None
        self.log_file = os.path.join(settings.BASE_DIR, "data", "traps.jsonl")
        self.mib_path = os.path.join(settings.BASE_DIR, "data", "mibs")
        self.resolve_mibs = True
        
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
    
    def start(self, port=1162, community="public", resolve_mibs=True):
        if self.process and self.process.poll() is None:
            return {"status": "already_running", "pid": self.process.pid}
        
        self.resolve_mibs = resolve_mibs
        
        cmd = [
            sys.executable, "workers/trap_receiver.py",
            "--port", str(port),
            "--community", community,
            "--mib-path", self.mib_path,
            "--output", self.log_file,
            "--resolve-mibs", "true" if resolve_mibs else "false"
        ]
        
        self.process = subprocess.Popen(
            cmd,
            cwd=settings.BASE_DIR,
            stdout=sys.stdout, 
            stderr=sys.stderr
        )
        
        return {"status": "started", "pid": self.process.pid, "resolve_mibs": resolve_mibs}
    
    def stop(self):
        if self.process:
            if self.process.poll() is None:
                self.process.terminate()
                try:
                    self.process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.process.kill()
            self.process = None
            return {"status": "stopped"}
        return {"status": "not_running"}
    
    def get_status(self):
        running = self.process is not None and self.process.poll() is None
        return {
            "running": running,
            "pid": self.process.pid if running else None,
            "port": 1162,
            "resolve_mibs": self.resolve_mibs if running else None
        }
    
    def get_traps(self, limit=50):
        data = []
        if not os.path.exists(self.log_file):
            return []
        try:
            with open(self.log_file, 'r') as f:
                lines = f.readlines()
                for line in reversed(lines[-limit:]):
                    if line.strip():
                        try:
                            data.append(json.loads(line))
                        except: 
                            pass
        except Exception:
            pass
        return data
    
    def clear_traps(self):
        open(self.log_file, 'w').close()

trap_manager = TrapManager()
