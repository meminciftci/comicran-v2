from http.server import BaseHTTPRequestHandler, HTTPServer
from collections import defaultdict
import threading
import requests
import os
import time
import sys

default_vbbu_address = "10.0.0.10:8080"

# Per-UE routing table (UE IP → target vBBU address)

# ue_target = defaultdict(lambda: default_vbbu_address)

ue_target = {
    "10.0.0.1": default_vbbu_address,  # ue1 → vbbu1
    "10.0.0.2": default_vbbu_address,  # ue2 → vbbu1 (initially)
}

log_path = "../outputs/rrh_output.txt"
os.makedirs(os.path.dirname(log_path), exist_ok=True)

def log_rrh(message):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    with open(log_path, "a") as f:
        f.write(line + "\n")

class ProxyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        client_ip = self.client_address[0]
        target = ue_target.get(client_ip)

        log_rrh(f"Received request from {client_ip} → forwarding to {target}")

        if not target:
            self.send_response(403)
            self.end_headers()
            self.wfile.write(f"Unknown client {client_ip}".encode())
            return

        url = f"http://{target}{self.path}"
        try:
            resp = requests.get(url)
            log_rrh(f"Response from {target}: {resp.text.strip()}")
            self.send_response(resp.status_code)
            self.end_headers()
            self.wfile.write(resp.content)
        except Exception as e:
            self.send_response(502)
            self.end_headers()
            self.wfile.write(f"Forwarding failed: {e}".encode())

    # 🚫 Suppress logging to avoid terminal clutter
    def log_message(self, format, *args):
        return

def control_loop():
    while True:
        raw = input("Handover> ").strip()               # Error var 
        if raw.startswith("set"):
            try:
                _, ue, vbbu = raw.split()
                log_rrh(f"Starting handover of {ue}...")
                if ue == "ue1":
                    ip = "10.0.0.1"
                elif ue == "ue2":
                    ip = "10.0.0.2"
                else:
                    print("Unknown UE.")
                    continue

                if vbbu == "vbbu1":
                    ue_target[ip] = "10.0.0.10:8080"
                elif vbbu == "vbbu2":
                    ue_target[ip] = "10.0.0.20:8081"
                else:
                    print("Unknown vBBU.")
                    continue

                print(f"{ue} now routes to {vbbu}")
                log_rrh(f"Handover complete: {ue} now routes to {vbbu} ({ue_target[ip]})")
            except:
                print("Usage: set ue1|ue2 vbbu1|vbbu2")
        elif raw == "show":
            for k, v in ue_target.items():
                print(f"{k} → {v}")
        else:
            print("Commands: set <ue1|ue2> <vbbu1|vbbu2>, show")

if __name__ == '__main__':
    threading.Thread(target=control_loop, daemon=True).start()
    print("RRH proxy running on port 8000 (per-UE forwarding)")
    log_rrh("RRH proxy started on port 8000")
    log_rrh(f"Initial UE mapping: {ue_target}")
    server = HTTPServer(('', 8000), ProxyHandler)
    server.serve_forever()
