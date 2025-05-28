import socket
import threading
import json
import time
import random
import os
import requests
import subprocess
from flask import Flask, request, jsonify
from flask_cors import CORS

ORCH_HOST = '0.0.0.0'
ORCH_PORT = 9100
RRH_CONTROL_IP = '10.0.0.100'
RRH_CONTROL_PORT = 9200

ue_assignments = {}
vbbu_loads = {}
redirected_vbbus = {}

PREDEFINED_VBBUS = {
    "vbbu1": {"ip": "10.0.0.201", "port": 8080, "is_active": True},
    "vbbu2": {"ip": "10.0.0.202", "port": 8081, "is_active": False},
}

NEXT_VBBU_INDEX = 3

orch_log_path = "../outputs/orch_output.txt"
if not os.path.exists("../outputs"):
    os.makedirs("../outputs")

# === Configuration ===
VALID_UE_IDS = set(range(1, 11))
UE_PORT = 5000
# Track UE state: 'rrh' or 'disconnected'
ue_states = {uid: 'disconnected' for uid in VALID_UE_IDS}

# === Flask App Setup ===
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# === Standard Response Format ===
def make_response(data=None, status="ok", message=None):
    response = {"status": status}
    if data is not None:
        response["data"] = data
    if message is not None:
        response["message"] = message
    return jsonify(response)

class OrchClient:
    def __init__(self, host='10.0.0.200', port=9100, timeout=2):
        self.host = host
        self.port = port
        self.timeout = timeout

    def _send(self, msg: dict) -> dict:

        with socket.create_connection((self.host, self.port), timeout=self.timeout) as sock:
            sock.sendall(json.dumps(msg).encode())
            data = sock.recv(65536)
        return json.loads(data.decode())

    def get_assignments(self) -> dict:
        return self._send({"command": "get_assignments"})

    def get_loads(self) -> dict:
        return self._send({"command": "get_loads"})

    def handover(self, ue_id: str, new_ip: str, new_port: int) -> dict:
        return self._send({
            "command": "handover",
            "ue_id": ue_id,
            "new_vbbu_ip": new_ip,
            "new_vbbu_port": new_port
        })

    def migrate(self, from_vbbu: str) -> dict:
        return self._send({
            "command": "migrate",
            "from_vbbu": from_vbbu
        })
    def activate_vbbu(self, ip: str, port: int) -> bool:
        r = requests.get(f'http://{ip}:{port}/control?activate=1', timeout=1)
        return r.status_code == 200

    def deactivate_vbbu(self, ip: str, port: int) -> bool:
        r = requests.get(f'http://{ip}:{port}/control?deactivate=1', timeout=1)
        return r.status_code == 200
    
    def get_vbbus(self) -> dict:
        return self._send({"command": "get_vbbus"})
    
     
    


class DummyConn:
    def sendall(self, data):
        try:
            parsed = json.loads(data.decode())
            print("[OK] Migration command processed:")
            print(json.dumps(parsed, indent=2))
        except:
            print(data.decode())
    def close(self):
        pass

def log_orch(msg):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    with open(orch_log_path, "a") as f:
        f.write(f"[{timestamp}] {msg}\n")

def handle_client(conn, addr):
    try:
        data = conn.recv(4096)
        if not data:
            return
        message = json.loads(data.decode())
        cmd = message.get('command')

        if cmd == 'handover':
            handle_handover_command(message, conn)
        elif cmd == 'report_load':
            handle_load_report(message, addr[0], conn)
        elif cmd == 'get_assignments':
            conn.sendall(json.dumps(ue_assignments, indent=2).encode())
        elif cmd == 'get_loads':
            conn.sendall(json.dumps(vbbu_loads, indent=2).encode())
        elif cmd == 'report_assignments':
            count = 0
            for item in message.get('assignments', []):
                ue_id = item.get("ue_id")
                ip = item.get("vbbu_ip")
                port = item.get("vbbu_port")
                if ue_id and ip and port:
                    ue_assignments[ue_id] = {"vbbu_ip": ip, "vbbu_port": port}
                    count += 1
            if conn: conn.sendall(b"[OK] Assignments received\n")
            log_orch(f"[ASSIGN] Received {count} UE assignments from RRH")
        elif cmd == 'migrate':
            handle_full_migration(message, conn)
        elif cmd == 'get_vbbus':
            vbbus = {}
            for name, info in PREDEFINED_VBBUS.items():
                ip   = info['ip']
                port = info['port']
                active = info.get('is_active', False)
                load_info = vbbu_loads.get(ip, {})
                vbbus[name] = {
                    'ip': ip,
                    'port': port,
                    'is_active': active,
                    'cpu': load_info.get('cpu', 0),
                    'connections': load_info.get('connections', 0)
                }
            conn.sendall(json.dumps(vbbus).encode())
        else:
            if conn: conn.sendall(b"[ERROR] Unknown command.\n")
    except Exception as e:
        log_orch(f"[ERROR] Command error from {addr}: {e}")
        if conn: conn.sendall(b"[ERROR] Internal failure.\n")
    finally:
        if conn: conn.close()

def handle_handover_command(message, conn=None):
    ue_id = message.get('ue_id')
    new_ip = message.get('new_vbbu_ip')
    new_port = message.get('new_vbbu_port')
    delay = random.uniform(0.3, 0.7)
    time.sleep(delay)
    if not all([ue_id, new_ip, new_port]):
        if conn:
            conn.sendall(b"[ERROR] Missing handover fields.\n")
        return

    ue_assignments[ue_id] = {"vbbu_ip": new_ip, "vbbu_port": new_port}
    forward_to_rrh(message)
    log_text = f"[HANDOVER] {ue_id} -> {new_ip}:{new_port}"
    log_orch(log_text)

    if conn:
        conn.sendall(json.dumps({"status": "ok", "message": log_text}).encode())

def handle_load_report(message, vbbu_ip, conn):
    cpu = message.get('cpu')
    connections = message.get('connections')

    if cpu is None or connections is None:
        conn.sendall(b"[ERROR] Invalid load report.\n")
        return

    vbbu_loads[vbbu_ip] = {
        'cpu': cpu,
        'connections': connections,
        'timestamp': time.time()
    }

    log_orch(f"[LOAD] {vbbu_ip}: CPU={cpu}, Conn={connections}")
    conn.sendall(b"[OK] Load received.\n")

def forward_to_rrh(message):
    try:
        with socket.create_connection((RRH_CONTROL_IP, RRH_CONTROL_PORT), timeout=3) as sock:
            sock.sendall(json.dumps(message).encode())
            response = sock.recv(4096)
            log_orch(f"[RRH_RESPONSE] {response.decode().strip()}")
    except Exception as e:
        log_orch(f"[ERROR] RRH unreachable or error: {e}")

def handle_full_migration(message, conn):
    global NEXT_VBBU_INDEX

    from_vbbu_fqdn = message.get('from_vbbu')
    if not from_vbbu_fqdn:
        if conn: conn.sendall(json.dumps({"status": "error", "message": "from_vbbu is required."}).encode())
        log_orch("[MIGRATE_ERROR] 'from_vbbu' field missing in migration command.")
        return

    target_vbbu_name = f"vbbu{NEXT_VBBU_INDEX}"

    if target_vbbu_name not in PREDEFINED_VBBUS:
        log_orch(f"[MIGRATE_ERROR] Target vBBU {target_vbbu_name} is not predefined or no more vBBUs available. Current index: {NEXT_VBBU_INDEX}")
        if conn: conn.sendall(json.dumps({"status": "error", "message": f"Target vBBU {target_vbbu_name} not available or limit reached."}).encode())
        return
    
    if PREDEFINED_VBBUS[target_vbbu_name]["is_active"]:
        log_orch(f"[MIGRATE_INFO] Target vBBU {target_vbbu_name} is already considered active. Proceeding with redirection if different from source.")

    new_vbbu_info = PREDEFINED_VBBUS[target_vbbu_name]
    new_ip = new_vbbu_info["ip"]
    new_port = new_vbbu_info["port"]
    new_vbbu_fqdn = f"{new_ip}:{new_port}"

    log_orch(f"[MIGRATE] Initiating migration from {from_vbbu_fqdn} to {target_vbbu_name} ({new_vbbu_fqdn}).")
    
    if PREDEFINED_VBBUS[target_vbbu_name]["is_active"] == False:
        PREDEFINED_VBBUS[target_vbbu_name]["is_active"] = True
        try:
            requests.get(f"http://{PREDEFINED_VBBUS[target_vbbu_name]['ip']}:{PREDEFINED_VBBUS[target_vbbu_name]['port']}/control?activate=1", timeout=2)
            log_orch(f"[MIGRATE] {target_vbbu_name} ({new_vbbu_fqdn}) Activated and ready to serve.")
        except Exception as e:
            log_orch(f"[ERROR] Activate HTTP failed: {e}")
    else:
        pass
    # NEXT_VBBU_INDEX += 1

    forward_to_rrh({
        "command": "update_redirect",
        "from_vbbu": from_vbbu_fqdn,
        "to_vbbu": new_vbbu_fqdn
    })
    redirected_vbbus[from_vbbu_fqdn] = new_vbbu_fqdn
    log_orch(f"[MIGRATE] RRH notified to redirect traffic from {from_vbbu_fqdn} to {new_vbbu_fqdn}.")

    migrated_ues_count = 0
    ue_ids_to_migrate = []

    for ue_id, assignment in list(ue_assignments.items()):
        current_ue_vbbu_fqdn = f"{assignment['vbbu_ip']}:{assignment['vbbu_port']}"
        if current_ue_vbbu_fqdn == from_vbbu_fqdn:
            handover_cmd_for_ue = {
                "command": "handover",
                "ue_id": ue_id,
                "new_vbbu_ip": new_ip,
                "new_vbbu_port": new_port
            }
            handle_handover_command(handover_cmd_for_ue)
            migrated_ues_count += 1
            ue_ids_to_migrate.append(ue_id)

    response_message = f"Migration process initiated for {migrated_ues_count} UEs from {from_vbbu_fqdn} to {new_vbbu_fqdn} (using {target_vbbu_name})."
    response = {
        "status": "ok",
        "message": response_message,
        "migrated_ues_count": migrated_ues_count,
        "migrated_ue_ids": ue_ids_to_migrate,
        "new_vbbu_target": new_vbbu_fqdn,
        "activated_vbbu_name": target_vbbu_name
    }
    if conn:
        conn.sendall(json.dumps(response, indent=2).encode())
    log_orch(f"[MIGRATE_SUCCESS] {response_message}")

def start_orchestrator():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((ORCH_HOST, ORCH_PORT))
        server.listen(5)
        log_orch(f"[ORCH_SERVER] Listening on {ORCH_HOST}:{ORCH_PORT}")
        while True:
            conn, addr = server.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

def send_ue_cmd(uid: int, cmd: str):
    """Send GET request to the UE's management endpoint."""
    ue_ip = f'10.0.0.{uid}'
    url = f'http://{ue_ip}:{UE_PORT}/{cmd}'
    try:
        resp = requests.get(url, timeout=2)
        if resp.status_code == 200:
            log_orch(f"[UE_MANAGER] UE{uid} acknowledged '{cmd}'.")
            return True
        else:
            log_orch(f"[UE_MANAGER_ERROR] UE{uid} returned status {resp.status_code} for '{cmd}'")
    except requests.RequestException as e:
        log_orch(f"[UE_MANAGER_ERROR] Failed to reach UE{uid} at {url}: {e}")
    return False

def add_ue(uid: int):
    if ue_states[uid] == 'connected':
        log_orch(f"[UE_MANAGER_WARN] UE{uid} already on RRH.")
        print(f"[WARN] UE{uid} is already connected to RRH.")
        return False
    
    # Send 'add' command to UE's terminal
    if send_ue_cmd(uid, 'add'):
        ue_states[uid] = 'connected'
        # Notify RRH about UE connection
        try:
            with socket.create_connection((RRH_CONTROL_IP, RRH_CONTROL_PORT), timeout=2) as sock:
                sock.sendall(json.dumps({
                    "command": "ue_connect",
                    "ue_id": f"UE{uid}"
                }).encode())
                _ = sock.recv(1024)
            log_orch(f"[UE_MANAGER] Notified RRH about UE{uid} connection")
        except Exception as e:
            log_orch(f"[UE_MANAGER_ERROR] Failed to notify RRH about UE{uid} connection: {e}")
        print(f"[SUCCESS] Command sent to connect UE{uid} to RRH.")
        return True
    
    print(f"[FAILED] Failed to send connect command to UE{uid}.")
    return False

def remove_ue(uid: int):
    if ue_states[uid] == 'disconnected':
        log_orch(f"[UE_MANAGER_WARN] UE{uid} already disconnected.")
        print(f"[WARN] UE{uid} is already disconnected.")
        return False
    
    # Send 'remove' command to UE's terminal
    if send_ue_cmd(uid, 'remove'):
        ue_states[uid] = 'disconnected'
        # Notify RRH about UE disconnection
        try:
            with socket.create_connection((RRH_CONTROL_IP, RRH_CONTROL_PORT), timeout=2) as sock:
                sock.sendall(json.dumps({
                    "command": "ue_disconnect",
                    "ue_id": f"UE{uid}"
                }).encode())
                _ = sock.recv(1024)
            log_orch(f"[UE_MANAGER] Notified RRH about UE{uid} disconnection")
        except Exception as e:
            log_orch(f"[UE_MANAGER_ERROR] Failed to notify RRH about UE{uid} disconnection: {e}")
        print(f"[SUCCESS] Command sent to disconnect UE{uid} from RRH.")
        return True
    
    print(f"[FAILED] Failed to send disconnect command to UE{uid}.")
    return False

def process_multiple_ues(cmd: str, uids: list[int]):
    """Process multiple user IDs for add or remove command."""
    for uid in uids:
        if cmd == 'add':
            add_ue(uid)
        else:
            remove_ue(uid)

def list_ue_status():
    print("\nCurrent UE Status:")
    print("-----------------")
    for uid in sorted(VALID_UE_IDS):
        status = "Connected" if ue_states[uid] == 'connected' else "Disconnected"
        print(f"UE{uid}: {status}")
    print("-----------------")

def cli_loop():
    cli_vbbu_map_to_fqdn = {
        name: f"{info['ip']}:{info['port']}"
        for name, info in PREDEFINED_VBBUS.items()
    }

    while True:
        try:
            raw_input_str = input("Orchestrator> ").strip()

            # UE Management Commands
            if raw_input_str.startswith("ue add"):
                parts = raw_input_str.split()
                if len(parts) < 3:
                    print("[ERROR] Usage: ue add <id> [id2 id3 ...]")
                    continue
                try:
                    uids = [int(uid) for uid in parts[2:]]
                    invalid_ids = [uid for uid in uids if uid not in VALID_UE_IDS]
                    if invalid_ids:
                        print(f"[ERROR] Invalid UE IDs: {invalid_ids}. Use 1–10.")
                        continue
                    process_multiple_ues('add', uids)
                except ValueError:
                    print("[ERROR] Invalid UE ID format. Use numbers 1-10.")
                continue

            if raw_input_str.startswith("ue remove"):
                parts = raw_input_str.split()
                if len(parts) < 3:
                    print("[ERROR] Usage: ue remove <id> [id2 id3 ...] or ue remove all")
                    continue
                
                if parts[2].lower() == 'all':
                    process_multiple_ues('remove', list(VALID_UE_IDS))
                    continue
                
                try:
                    uids = [int(uid) for uid in parts[2:]]
                    invalid_ids = [uid for uid in uids if uid not in VALID_UE_IDS]
                    if invalid_ids:
                        print(f"[ERROR] Invalid UE IDs: {invalid_ids}. Use 1–10.")
                        continue
                    process_multiple_ues('remove', uids)
                except ValueError:
                    print("[ERROR] Invalid UE ID format. Use numbers 1-10.")
                continue

            if raw_input_str == "ue list":
                list_ue_status()
                continue

            # Existing commands...
            if raw_input_str.startswith("handover"):
                parts = raw_input_str.split()
                if len(parts) != 3:
                    print("[ERROR] Usage: handover <UE_ID> <TARGET_VBBU_NAME (e.g., vbbu2)>")
                    continue
                
                _, ue_id_cli, target_vbbu_name_cli = parts
                ue_id_cli = ue_id_cli.upper()
                if target_vbbu_name_cli not in PREDEFINED_VBBUS:
                    print(f"[ERROR] Unknown target vBBU name: {target_vbbu_name_cli}. Available: {', '.join(PREDEFINED_VBBUS.keys())}")
                    continue

                target_info = PREDEFINED_VBBUS[target_vbbu_name_cli]
                current = ue_assignments.get(ue_id_cli)

                if current and current["vbbu_ip"] == target_info["ip"] and current["vbbu_port"] == target_info["port"]:
                    print(f"[INFO] UE {ue_id_cli} is already served by {target_vbbu_name_cli}. No action taken.")
                    continue
                cmd = {
                    "command": "handover",
                    "ue_id": ue_id_cli.upper(),
                    "new_vbbu_ip": target_info["ip"],
                    "new_vbbu_port": target_info["port"]
                }

                handle_handover_command(cmd)
                print(f"[OK] Sent handover: {ue_id_cli.upper()} -> {target_vbbu_name_cli} ({target_info['ip']}:{target_info['port']})")
                continue

            if raw_input_str.startswith("migrate"):
                args = raw_input_str[len("migrate"):].strip().split()
                if not (len(args) == 1 or (len(args) == 2 and args[1].lower() == "deactivate")):
                    print("[ERROR] Usage: migrate <SOURCE_VBBU> [deactivate]")
                    continue
                source, *flag = args
                deactivate_flag = bool(flag)
                fqdn = cli_vbbu_map_to_fqdn.get(source)
                if not fqdn:
                    print(f"[ERROR] Unknown vBBU: {source}")
                    continue


                handle_full_migration({"command":"migrate","from_vbbu":fqdn}, DummyConn())


                if deactivate_flag:
                    info = PREDEFINED_VBBUS[source]

                    try:
                        resp = requests.get(f"http://{info['ip']}:{info['port']}/control?deactivate=1", timeout=2)
                        print(f"[HTTP] Deactivate request returned {resp.status_code}")
                    except Exception as e:
                        print(f"[ERROR] Deactivate HTTP failed: {e}")

                    info["is_active"] = False
                    print(f"[OK] {source} deactivated after migration.")
                    log_orch(f"[DEACTIVATE] {source} marked inactive via migrate flag.")
                continue

            # --- Standalone Deactivate ---
            if raw_input_str.startswith("deactivate"):
                parts = raw_input_str.split()
                if len(parts) != 2:
                    print("[ERROR] Usage: deactivate <VBBU_NAME>")
                    continue
                name = parts[1]
                if name not in PREDEFINED_VBBUS:
                    print(f"[ERROR] Unknown vBBU: {name}")
                    continue
                info = PREDEFINED_VBBUS[name]
                if not info["is_active"]:
                    print(f"[INFO] {name} is already inactive.")
                    continue


                try:
                    resp = requests.get(f"http://{info['ip']}:{info['port']}/control?deactivate=1", timeout=2)
                    print(f"[HTTP] Deactivate request returned {resp.status_code}")
                except Exception as e:
                    print(f"[ERROR] Deactivate HTTP failed: {e}")

                info["is_active"] = False
                print(f"[OK] {name} has been deactivated.")
                log_orch(f"[DEACTIVATE] {name} marked inactive via CLI command.")
                continue
            if raw_input_str.startswith("activate"):
                parts = raw_input_str.split()
                if len(parts) != 2:
                    print("[ERROR] Usage: activate <VBBU_NAME>")
                    continue
                name = parts[1]
                if name not in PREDEFINED_VBBUS:
                    print(f"[ERROR] Unknown vBBU: {name}")
                    continue
                info = PREDEFINED_VBBUS[name]
                if info["is_active"]:
                    print(f"[INFO] {name} is already active.")
                else:

                    try:
                        resp = requests.get(f"http://{info['ip']}:{info['port']}/control?activate=1", timeout=2)
                        print(f"[HTTP] Activate request returned {resp.status_code}")
                    except Exception as e:
                        print(f"[ERROR] Activate HTTP failed: {e}")

                    info["is_active"] = True
                    print(f"[OK] {name} has been activated.")
                    log_orch(f"[ACTIVATE] {name} marked active via CLI command.")
                continue
            elif raw_input_str == "show assignments":
                if not ue_assignments:
                    print("[INFO] No UE assignments found.")
                else:
                    print("Current UE Assignments:")
                    for ue_id, assignment in ue_assignments.items():
                        vbbu_ip = assignment["vbbu_ip"]
                        vbbu_port = assignment["vbbu_port"]

                        vbbu_name = next(
                            (name for name, info in PREDEFINED_VBBUS.items()
                            if info["ip"] == vbbu_ip and info["port"] == vbbu_port),
                            "Unknown"
                        )
                        print(f"  {ue_id} -> {vbbu_name} ({vbbu_ip}:{vbbu_port})")
            elif raw_input_str == "show loads":
                active_vbbus = [
                    name for name, info in PREDEFINED_VBBUS.items()
                    if info["is_active"]
                ]
                if not active_vbbus:
                    print("[INFO] No active vBBUs.")
                else:
                    print("Current vBBU Loads:")
                    for name in active_vbbus:
                        info = PREDEFINED_VBBUS[name]
                        ip, port = info["ip"], info["port"]
                        load = vbbu_loads.get(ip)
                        if load:
                            cpu = load.get('cpu', 'N/A')
                            conns = load.get('connections', 'N/A')
                            print(f"  {name} ({ip}:{port}) -> CPU: {cpu}, Connections: {conns}")
                        else:
                            print(f"  {name} ({ip}:{port}) -> No load data yet")
            elif raw_input_str == "show vbbus":
                print("vBBU Status:")
                for name, info in PREDEFINED_VBBUS.items():
                    status = "Active" if info["is_active"] else "Inactive/Standby"
                    load = vbbu_loads.get(info["ip"], {})
                    cpu = load.get('cpu', 'N/A')
                    conns = load.get('connections', 'N/A')
                    print(f"  {name} ({info['ip']}:{info['port']}) - Status: {status} - CPU: {cpu}, Conns: {conns}")

            elif raw_input_str == "help":
                print("Available Commands:")
                print("  UE Management:")
                print("    ue add <id> [id2 id3 ...]    - Add UE(s) to RRH")
                print("    ue remove <id> [id2 id3 ...] - Remove UE(s) from RRH")
                print("    ue remove all                - Remove all UEs from RRH")
                print("    ue list                      - Show UE connection status")
                print("  vBBU Management:")
                print("    handover <UE_ID> <TARGET_VBBU_NAME>  - Manually handover a UE")
                print("    migrate <SOURCE_VBBU_NAME>         - Migrate UEs from a source vBBU")
                print("    show assignments                   - Show current UE to vBBU assignments")
                print("    show loads                         - Show reported loads from vBBUs")
                print("    show vbbus                         - Show status of predefined vBBUs")
                print("    help                               - Show this help message")
                print("    quit / exit                        - Exit the orchestrator CLI")
            elif raw_input_str in ["quit", "exit"]:
                print("Exiting orchestrator CLI.")
                break
            else:
                if raw_input_str:
                    print(f"[ERROR] Unknown command: '{raw_input_str}'. Type 'help' for available commands.")

        except EOFError:
            print("\nExiting orchestrator CLI (EOF).")
            break
        except KeyboardInterrupt:
            print("\nExiting orchestrator CLI (KeyboardInterrupt).")
            break
        except Exception as e:
            print(f"[CLI_ERROR] An unexpected error occurred: {e}")
            log_orch(f"[CLI_ERROR_DETAIL] {e}")

# === REST API Endpoints ===
@app.route('/api/ue/add', methods=['POST'])
def api_ue_add():
    data = request.get_json()
    if not data or 'uids' not in data:
        return make_response(status="error", message="Missing uids in request body")
    
    uids = data['uids']
    if not isinstance(uids, list):
        return make_response(status="error", message="uids must be a list")
    
    invalid_ids = [uid for uid in uids if uid not in VALID_UE_IDS]
    if invalid_ids:
        return make_response(status="error", message=f"Invalid UE IDs: {invalid_ids}. Use 1-10.")
    
    success = []
    failed = []
    for uid in uids:
        if add_ue(uid):
            success.append(uid)
        else:
            failed.append(uid)
    
    return make_response(data={
        "success": success,
        "failed": failed
    })

@app.route('/api/ue/remove', methods=['POST'])
def api_ue_remove():
    data = request.get_json()
    if not data or 'uids' not in data:
        return make_response(status="error", message="Missing uids in request body")
    
    uids = data['uids']
    if uids == 'all':
        uids = list(VALID_UE_IDS)
    elif not isinstance(uids, list):
        return make_response(status="error", message="uids must be a list or 'all'")
    
    invalid_ids = [uid for uid in uids if uid not in VALID_UE_IDS]
    if invalid_ids:
        return make_response(status="error", message=f"Invalid UE IDs: {invalid_ids}. Use 1-10.")
    
    success = []
    failed = []
    for uid in uids:
        if remove_ue(uid):
            success.append(uid)
        else:
            failed.append(uid)
    
    return make_response(data={
        "success": success,
        "failed": failed
    })

@app.route('/api/ue/list', methods=['GET'])
def api_ue_list():
    return make_response(data=ue_states)

@app.route('/api/handover', methods=['POST'])
def api_handover():
    data = request.get_json()
    if not data or not all(k in data for k in ['ue_id', 'target_vbbu']):
        return make_response(status="error", message="Missing required fields: ue_id and target_vbbu")
    
    ue_id = data['ue_id'].upper()
    target_vbbu = data['target_vbbu']
    
    if target_vbbu not in PREDEFINED_VBBUS:
        return make_response(status="error", message=f"Unknown target vBBU: {target_vbbu}")
    
    target_info = PREDEFINED_VBBUS[target_vbbu]
    current = ue_assignments.get(ue_id)
    
    if current and current["vbbu_ip"] == target_info["ip"] and current["vbbu_port"] == target_info["port"]:
        return make_response(message=f"UE {ue_id} is already served by {target_vbbu}")
    
    cmd = {
        "command": "handover",
        "ue_id": ue_id,
        "new_vbbu_ip": target_info["ip"],
        "new_vbbu_port": target_info["port"]
    }
    
    handle_handover_command(cmd)
    return make_response(message=f"Handover initiated: {ue_id} -> {target_vbbu}")

@app.route('/api/migrate', methods=['POST'])
def api_migrate():
    data = request.get_json()
    if not data or 'source_vbbu' not in data:
        return make_response(status="error", message="Missing source_vbbu in request body")
    
    source = data['source_vbbu']
    deactivate = data.get('deactivate', False)
    
    if source not in PREDEFINED_VBBUS:
        return make_response(status="error", message=f"Unknown vBBU: {source}")
    
    fqdn = f"{PREDEFINED_VBBUS[source]['ip']}:{PREDEFINED_VBBUS[source]['port']}"
    response = handle_full_migration({"command": "migrate", "from_vbbu": fqdn}, DummyConn())
    
    if deactivate:
        info = PREDEFINED_VBBUS[source]
        try:
            requests.get(f"http://{info['ip']}:{info['port']}/control?deactivate=1", timeout=2)
            info["is_active"] = False
            log_orch(f"[DEACTIVATE] {source} marked inactive via API.")
        except Exception as e:
            log_orch(f"[ERROR] Deactivate HTTP failed: {e}")
    
    return make_response(data=response)

@app.route('/api/vbbu/activate', methods=['POST'])
def api_activate_vbbu():
    data = request.get_json()
    if not data or 'vbbu' not in data:
        return make_response(status="error", message="Missing vbbu in request body")
    
    name = data['vbbu']
    if name not in PREDEFINED_VBBUS:
        return make_response(status="error", message=f"Unknown vBBU: {name}")
    
    info = PREDEFINED_VBBUS[name]
    if info["is_active"]:
        return make_response(message=f"{name} is already active")
    
    try:
        resp = requests.get(f"http://{info['ip']}:{info['port']}/control?activate=1", timeout=2)
        info["is_active"] = True
        log_orch(f"[ACTIVATE] {name} marked active via API.")
        return make_response(message=f"{name} has been activated")
    except Exception as e:
        return make_response(status="error", message=f"Activation failed: {str(e)}")

@app.route('/api/vbbu/deactivate', methods=['POST'])
def api_deactivate_vbbu():
    data = request.get_json()
    if not data or 'vbbu' not in data:
        return make_response(status="error", message="Missing vbbu in request body")
    
    name = data['vbbu']
    if name not in PREDEFINED_VBBUS:
        return make_response(status="error", message=f"Unknown vBBU: {name}")
    
    info = PREDEFINED_VBBUS[name]
    if not info["is_active"]:
        return make_response(message=f"{name} is already inactive")
    
    try:
        resp = requests.get(f"http://{info['ip']}:{info['port']}/control?deactivate=1", timeout=2)
        info["is_active"] = False
        log_orch(f"[DEACTIVATE] {name} marked inactive via API.")
        return make_response(message=f"{name} has been deactivated")
    except Exception as e:
        return make_response(status="error", message=f"Deactivation failed: {str(e)}")

@app.route('/api/assignments', methods=['GET'])
def api_assignments():
    return make_response(data=ue_assignments)

@app.route('/api/loads', methods=['GET'])
def api_loads():
    return make_response(data=vbbu_loads)

@app.route('/api/vbbus', methods=['GET'])
def api_vbbus():
    vbbus = {}
    for name, info in PREDEFINED_VBBUS.items():
        load = vbbu_loads.get(info['ip'], {})
        vbbus[name] = {
            'ip': info['ip'],
            'port': info['port'],
            'is_active': info['is_active'],
            'cpu': load.get('cpu', 'N/A'),
            'connections': load.get('connections', 'N/A')
        }
    return make_response(data=vbbus)

def run_flask():
    app.run(host='0.0.0.0', port=5006)

if __name__ == "__main__":
    log_orch("[INIT] Orchestrator process started.")
    server_thread = threading.Thread(target=start_orchestrator, daemon=True)
    server_thread.start()
    
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    time.sleep(5)
    cli_loop()
    log_orch("[EXIT] Orchestrator process finished.")