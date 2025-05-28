from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
import requests
import os
import time
import sys
import socket
import json
import random

# === Initial Setup ===
vbbu_choices = ["10.0.0.201:8080", "10.0.0.202:8081"]
ue_target = {
    f"10.0.0.{i}": "10.0.0.201:8080"
    for i in range(1, 11)
}
redirected_vbbus = {}  # e.g., "10.0.0.201:8080" → "10.0.0.202:8082"

# Track UE connection status
ue_connection_status = {
    f"10.0.0.{i}": "disconnected"
    for i in range(1, 11)
}

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
        ue_id = client_ip.split('.')[-1]               # e.g. "5" for 10.0.0.5

        # Look up the original target
        old_target = ue_target.get(client_ip)
        if not old_target:
            self.send_response(403)
            self.end_headers()
            self.wfile.write(f"Unknown client {client_ip}".encode())
            log_rrh(f"[ERROR] Unknown client UE{ue_id}")
            return

        # If there's a redirect rule, install it now
        new_target = redirected_vbbus.get(old_target)
        if new_target:
            ue_target[client_ip] = new_target
            target = new_target
            log_rrh(f"[INFO] UE{ue_id} traffic redirected: {old_target} → {new_target}")
        else:
            target = old_target

        # Log exactly one line showing where we actually forward
        vBBU_id = '1' if target.split(':')[0].split('.')[-1][-1] == '1' else '1-prime'
        log_rrh(f"    [REQUEST] UE{ue_id} → forwarding to vBBU{vBBU_id} ({target})")

        # Perform the HTTP GET
        url = f"http://{target}{self.path}"
        try:
            resp = requests.get(url, timeout=3)
            log_rrh(f"    [RESPONSE] vBBU{vBBU_id} → UE{ue_id} ({resp.status_code})")
            self.send_response(resp.status_code)
            self.end_headers()
            self.wfile.write(resp.content)
        except Exception as e:
            self.send_response(502)
            self.end_headers()
            self.wfile.write(f"Forwarding failed: {e}".encode())
            log_rrh(f"[ERROR] Failed forwarding UE{ue_id} → {target}: {e}")

    def log_message(self, format, *args):
        return

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

            if ue_id.upper().startswith("UE") and ue_id[2:].isdigit():
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
            log_rrh(f"[ORCH] Handover: {ue_id} → vBBU1-prime")

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
                log_rrh(f"[ORCH] Redirect rule: {old} → {new}")
                conn.sendall(b"[OK] Redirect rule updated\n")
            else:
                conn.sendall(b"[ERROR] Missing fields in update_redirect\n")
        elif cmd == "ue_connect":
            ue_id = message.get("ue_id")
            if ue_id.upper().startswith("UE") and ue_id[2:].isdigit():
                ue_ip = f"10.0.0.{int(ue_id[2:])}"
                ue_connection_status[ue_ip] = "connected"
                log_rrh(f"[ORCH] UE{ue_id} connected")
                conn.sendall(b"[OK] UE connected\n")
            else:
                conn.sendall(b"[ERROR] Invalid UE ID\n")
        elif cmd == "ue_disconnect":
            ue_id = message.get("ue_id")
            if ue_id.upper().startswith("UE") and ue_id[2:].isdigit():
                ue_ip = f"10.0.0.{int(ue_id[2:])}"
                ue_connection_status[ue_ip] = "disconnected"
                log_rrh(f"[ORCH] UE{ue_id} disconnected")
                conn.sendall(b"[OK] UE disconnected\n")
            else:
                conn.sendall(b"[ERROR] Invalid UE ID\n")
        else:
            conn.sendall(json.dumps({
                "status": "error",
                "reason": "Unknown command",
                "from": orchestrator_ip
            }).encode())
            log_rrh(f"[REJECTED] Unknown command from {orchestrator_ip}: {message}")
    except Exception as e:
        log_rrh(f"[ERROR] From orchestrator {orchestrator_ip}: {e}")
        conn.sendall(json.dumps({
            "status": "error",
            "reason": str(e),
            "from": orchestrator_ip
        }).encode())
    finally:
        conn.close()

def report_assignments_periodically():
    # send one immediately
    send_assignments()

    # then every 2 seconds
    while True:
        time.sleep(2)
        send_assignments()

def send_assignments():
    ORCH_IP   = "10.0.0.200"
    ORCH_PORT = 9100

    try:
        assignments = []
        for ip, vbbu in ue_target.items():
            # Only include connected UEs in assignments
            if ue_connection_status[ip] == "connected":
                ue_id = f"UE{ip.split('.')[-1]}"
                vbbu_ip, vbbu_port = vbbu.split(":")
                assignments.append({
                    "ue_id": ue_id,
                    "vbbu_ip": vbbu_ip,
                    "vbbu_port": int(vbbu_port)
                })
        message = {"command":"report_assignments",
                   "assignments": assignments}
        with socket.create_connection((ORCH_IP, ORCH_PORT), timeout=3) as sock:
            sock.sendall(json.dumps(message).encode())
            _ = sock.recv(1024)
        log_rrh(f"[REPORT] Sent {len(assignments)} UE assignments to orchestrator")
    except Exception as e:
        log_rrh(f"[ERROR] Failed to report assignments: {e}")

# === Main Entry ===
if __name__ == '__main__':
    threading.Thread(target=orchestrator_listener, daemon=True).start()
    threading.Thread(target=report_assignments_periodically, daemon=True).start()
    print("RRH proxy running on port 8000 (per-UE forwarding)")
    log_rrh("RRH proxy started on port 8000")
    log_rrh(f"Initial UE mapping: {ue_target}")
    log_rrh(f"Initial UE connection status: {ue_connection_status}")
    server = ThreadingHTTPServer(('', 8000), ProxyHandler)
    server.serve_forever()
