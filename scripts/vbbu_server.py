from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import sys
import json
import time
import threading
import socket
import urllib

# Config from arguments
port = int(sys.argv[1])
vbbu_id = f"vbbu{port - 8080 + 1}"
# vbbu_id = "vbbu1" if port == 8080 else "vbbu2"
print(f"vBBU server running on port {port} as {vbbu_id}")

# Orchestrator address
ORCH_IP = "10.0.0.200"
ORCH_PORT = 9100

# Track active UE IDs
ue_last_seen = {}  # ue_id → timestamp
lock = threading.Lock()

vbbu_log_path = f"../outputs/vbbu{port - 8079}_output.txt"

def log_vbbu(msg):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    with open(vbbu_log_path, "a") as f:
        f.write(f"[{timestamp}] {msg}\n")

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        value = int(params.get('value', [0])[0])
        ue_id = int(params.get('ue_id', [0])[0])

        # Track UE ID
        with lock:
            ue_last_seen[ue_id] = time.time()

        response = json.dumps({
            "vbbu_id": vbbu_id[-1],
            "acknowledgement": f"Acknowledgement #{value}"
        })
        log_line = f"    [REQUEST] Value {value} Recieved from UE{ue_id}"
        log_vbbu(log_line)

        self.send_response(200)
        self.end_headers()
        self.wfile.write(response.encode())

    def log_message(self, format, *args):
        return  # Suppress default logging

# Background thread to report load
def report_load_periodically():
    while True:
        try:
            now = time.time()
            with lock:
                ue_last_seen_filtered = {k: t for k, t in ue_last_seen.items() if now - t < 5}
                ue_last_seen.clear()
                ue_last_seen.update(ue_last_seen_filtered)
                ue_count = len(ue_last_seen)

            report = {
                "command": "report_load",
                "cpu": ue_count*4,           # Simulated load
                "connections": ue_count    # Also treated as connection count
            }

            with socket.create_connection((ORCH_IP, ORCH_PORT), timeout=3) as sock:
                sock.sendall(json.dumps(report).encode())
                _ = sock.recv(1024)
            log_vbbu(f"[REPORT] Sent load to orchestrator: {ue_count} UEs")

        except Exception as e:
            log_vbbu(f"[ERROR] Failed to report load: {e}")
        time.sleep(5)

# Launch reporting in background
threading.Thread(target=report_load_periodically, daemon=True).start()

# Start HTTP server
if __name__ == '__main__':
    log_vbbu(f"vBBU server running on port {port} as {vbbu_id}")
    ThreadingHTTPServer(('', port), Handler).serve_forever()
