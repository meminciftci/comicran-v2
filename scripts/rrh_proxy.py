from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import requests
import os
import time
import sys
import socket
import json
import random

# === Initial Setup ===
vbbu_choices = ["10.0.0.10:8080", "10.0.0.20:8081"]
ue_target = {
    f"10.0.0.{i}": random.choice(vbbu_choices)
    for i in range(1, 51)
}
redirected_vbbus = {}  # e.g., "10.0.0.10:8080" → "10.0.0.30:8082"

log_path = "../outputs/rrh_output.txt"
os.makedirs(os.path.dirname(log_path), exist_ok=True)

def log_rrh(message):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    with open(log_path, "a") as f:
        f.write(line + "\n")

# === HTTP Proxy ===
class ProxyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        client_ip = self.client_address[0]
        target = ue_target.get(client_ip)


        if target in redirected_vbbus:
            new_vbbu = redirected_vbbus[target]
            ue_target[client_ip] = new_vbbu
            target = new_vbbu
            log_rrh(f"[REDIRECT] {client_ip} was mapped to deprecated {target}, now → {new_vbbu}")

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

    def log_message(self, format, *args):
        return

# === Manual CLI Control ===
def control_loop():
    while True:
        raw = input("Handover> ").strip()
        if raw.startswith("set"):
            try:
                _, ue, vbbu = raw.split()
                log_rrh(f"Manual handover command: {ue} → {vbbu}")
                if ue.startswith("ue") and ue[2:].isdigit():
                    ip = f"10.0.0.{int(ue[2:])}"
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
                log_rrh(f"Manual handover complete: {ue} → {ue_target[ip]}")
            except:
                print("Usage: set ueX vbbu1|vbbu2")
        elif raw == "show":
            for k, v in ue_target.items():
                print(f"{k} → {v}")
        else:
            print("Commands: set <ueX> <vbbuX>, show")

# === TCP Listener for Orchestrator ===
def orchestrator_listener():
    host = '0.0.0.0'
    port = 9200
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen(5)
        log_rrh("RRH command listener started on port 9200")
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_orchestrator_command, args=(conn, addr), daemon=True).start()

def handle_orchestrator_command(conn, addr):
    orchestrator_ip = addr[0]
    try:
        data = conn.recv(4096)
        if not data:
            return
        message = json.loads(data.decode())
        cmd = message.get("command")

        if cmd == "handover":
            ue_id = message.get("ue_id")
            new_ip = message.get("new_vbbu_ip")
            new_port = message.get("new_vbbu_port")

            if ue_id.startswith("UE") and ue_id[2:].isdigit():
                ue_ip = f"10.0.0.{int(ue_id[2:])}"
            else:
                error_msg = {
                    "status": "error",
                    "reason": "Unknown UE ID",
                    "from": orchestrator_ip
                }
                conn.sendall(json.dumps(error_msg).encode())
                log_rrh(f"[REJECTED] Handover from {orchestrator_ip}: unknown UE ID {ue_id}")
                return

            new_target = f"{new_ip}:{new_port}"
            ue_target[ue_ip] = new_target
            log_rrh(f"[ORCH {orchestrator_ip}] Handover: {ue_id} ({ue_ip}) → {new_target}")

            conn.sendall(json.dumps({
                "status": "ok",
                "ue_id": ue_id,
                "ue_ip": ue_ip,
                "new_target": new_target,
                "from": orchestrator_ip
            }).encode())

        elif cmd == "update_redirect":
            old = message.get("from_vbbu")
            new = message.get("to_vbbu")
            if old and new:
                redirected_vbbus[old] = new
                log_rrh(f"[ORCH {orchestrator_ip}] Redirect rule: {old} → {new}")
                conn.sendall(b"[OK] Redirect rule updated\n")
            else:
                conn.sendall(b"[ERROR] Missing fields in update_redirect\n")
        else:
            conn.sendall(json.dumps({
                "status": "error",
                "reason": "Unknown command",
                "from": orchestrator_ip
            }).encode())
            log_rrh(f"[REJECTED] Unknown command from {orchestrator_ip}: {message}")
    except Exception as e:
        log_rrh(f"[ERROR] From {orchestrator_ip}: {e}")
        conn.sendall(json.dumps({
            "status": "error",
            "reason": str(e),
            "from": orchestrator_ip
        }).encode())
    finally:
        conn.close()

# === Main Entry ===
if __name__ == '__main__':
    threading.Thread(target=control_loop, daemon=True).start()
    threading.Thread(target=orchestrator_listener, daemon=True).start()
    print("RRH proxy running on port 8000 (per-UE forwarding)")
    log_rrh("RRH proxy started on port 8000")
    log_rrh(f"Initial UE mapping: {ue_target}")
    server = HTTPServer(('', 8000), ProxyHandler)
    server.serve_forever()
