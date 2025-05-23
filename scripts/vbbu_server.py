
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import sys
import json
import time
import threading
import socket
import urllib.parse

# Global active flag
ACTIVE = True
active_lock = threading.Lock()

# Config from arguments
port = int(sys.argv[1])
vbbu_id = f"vbbu{port - 8080 + 1}"
print(f"vBBU server running on port {port} as {vbbu_id}")

# Orchestrator address
ORCH_IP = "10.0.0.200"
ORCH_PORT = 9100

# Track active UE IDs
ue_last_seen = {}  # ue_id → timestamp
ue_lock = threading.Lock()

vbbu_log_path = f"../outputs/vbbu{port - 8079}_output.txt"

def log_vbbu(msg):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    with open(vbbu_log_path, "a") as f:
        f.write(f"[{timestamp}] {msg}\n")
    print(f"[{timestamp}] {msg}")

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        global ACTIVE

        # Control endpoint for deactivation
        if self.path.startswith('/control'):
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            if params.get('deactivate', ['0'])[0] == '1':
                with active_lock:
                    ACTIVE = False
                log_vbbu("[CONTROL] Deactivation command received; shutting down service.")
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"status":"deactivated"}')
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'{"error":"unknown control command"}')
            return

        # If deactivated, refuse service
        with active_lock:
            if not ACTIVE:
                self.send_response(503)
                self.end_headers()
                return

        # Normal UE GET handling
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        value = int(params.get('value', [0])[0])
        ue_id = int(params.get('ue_id', [0])[0])

        # Track UE ID
        with ue_lock:
            ue_last_seen[ue_id] = time.time()

        response = json.dumps({
            "vbbu_id": vbbu_id[-1],
            "acknowledgement": f"Acknowledgement #{value}"
        })
        log_vbbu(f"    [REQUEST] Value {value} received from UE{ue_id}")

        self.send_response(200)
        self.end_headers()
        self.wfile.write(response.encode())

    def log_message(self, format, *args):
        return  # Suppress default logging

def report_load_periodically():
    global ACTIVE
    while True:
        with active_lock:
            if not ACTIVE:
                log_vbbu("[REPORT] Service deactivated; stopping load reports.")
                break

        now = time.time()
        with ue_lock:
            # only count UEs seen in last 5s
            ue_last_seen_filtered = {
                k: t for k, t in ue_last_seen.items()
                if now - t < 5
            }
            ue_last_seen.clear()
            ue_last_seen.update(ue_last_seen_filtered)
            ue_count = len(ue_last_seen)

        report = {
            "command": "report_load",
            "cpu": ue_count * 4,
            "connections": ue_count
        }

        try:
            with socket.create_connection((ORCH_IP, ORCH_PORT), timeout=3) as sock:
                sock.sendall(json.dumps(report).encode())
                _ = sock.recv(1024)
            log_vbbu(f"[REPORT] Sent load to orchestrator: {ue_count} UEs")
        except Exception as e:
            log_vbbu(f"[ERROR] Failed to report load: {e}")

        time.sleep(5)

if __name__ == '__main__':
    # Start background reporter
    threading.Thread(target=report_load_periodically, daemon=True).start()

    # Start HTTP server
    log_vbbu(f"vBBU server running on port {port} as {vbbu_id}")
    ThreadingHTTPServer(('', port), Handler).serve_forever()
