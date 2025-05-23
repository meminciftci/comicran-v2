import socket
import threading
import json
import time
import random
import os
import requests

ORCH_HOST = '0.0.0.0'
ORCH_PORT = 9100
RRH_CONTROL_IP = '10.0.0.100'
RRH_CONTROL_PORT = 9200

ue_assignments = {}
vbbu_loads = {}
redirected_vbbus = {}

PREDEFINED_VBBUS = {
    "vbbu1": {"ip": "10.0.0.201", "port": 8080, "is_active": True},
    "vbbu2": {"ip": "10.0.0.202", "port": 8081, "is_active": True},
    "vbbu3": {"ip": "10.0.0.203", "port": 8082, "is_active": False},
    "vbbu4": {"ip": "10.0.0.204", "port": 8083, "is_active": False},
    "vbbu5": {"ip": "10.0.0.205", "port": 8084, "is_active": False},
}

NEXT_VBBU_INDEX = 3

orch_log_path = "../outputs/orch_output.txt"
if not os.path.exists("../outputs"):
    os.makedirs("../outputs")


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

    log_orch(f"[MIGRATE] Initiating migration from {from_vbbu_fqdn} to pre-started {target_vbbu_name} ({new_vbbu_fqdn}).")
    
    PREDEFINED_VBBUS[target_vbbu_name]["is_active"] = True
    NEXT_VBBU_INDEX += 1

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
            log_orch(f"[ORCH_SERVER] Accepted connection from {addr}")
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()



def cli_loop():
    cli_vbbu_map_to_fqdn = {
        name: f"{info['ip']}:{info['port']}"
        for name, info in PREDEFINED_VBBUS.items()
    }

    while True:
        try:
            raw_input_str = input("Orchestrator> ").strip()

            if raw_input_str.startswith("handover"):
                parts = raw_input_str.split()
                if len(parts) != 3:
                    print("[ERROR] Usage: handover <UE_ID> <TARGET_VBBU_NAME (e.g., vbbu2)>")
                    continue
                
                _, ue_id_cli, target_vbbu_name_cli = parts
                
                if target_vbbu_name_cli not in PREDEFINED_VBBUS:
                    print(f"[ERROR] Unknown target vBBU name: {target_vbbu_name_cli}. Available: {', '.join(PREDEFINED_VBBUS.keys())}")
                    continue

                target_info = PREDEFINED_VBBUS[target_vbbu_name_cli]
                cmd = {
                    "command": "handover",
                    "ue_id": ue_id_cli.upper(),
                    "new_vbbu_ip": target_info["ip"],
                    "new_vbbu_port": target_info["port"]
                }
                handle_handover_command(cmd)
                print(f"[OK] Sent handover: {ue_id_cli.upper()} -> {target_vbbu_name_cli} ({target_info['ip']}:{target_info['port']})")

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
                print("  handover <UE_ID> <TARGET_VBBU_NAME>  - Manually handover a UE (e.g., handover UE1 vbbu2)")
                print("  migrate <SOURCE_VBBU_NAME>         - Migrate UEs from a source vBBU to a new one (e.g., migrate vbbu1)")
                print("  show assignments                   - Show current UE to vBBU assignments")
                print("  show loads                         - Show reported loads from vBBUs")
                print("  show vbbus                         - Show status of predefined vBBUs")
                print("  help                               - Show this help message")
                print("  quit / exit                        - Exit the orchestrator CLI")
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

if __name__ == "__main__":
    log_orch("[INIT] Orchestrator process started.")
    server_thread = threading.Thread(target=start_orchestrator, daemon=True)
    server_thread.start()
    
    cli_loop()
    log_orch("[EXIT] Orchestrator process finished.")