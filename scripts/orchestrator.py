import socket
import threading
import json
import time
import random
import os

ORCH_HOST = '0.0.0.0'
ORCH_PORT = 9100
RRH_CONTROL_IP = '10.0.0.100'
RRH_CONTROL_PORT = 9200

ue_assignments = {}
vbbu_loads = {}
redirected_vbbus = {}


VBBU_COUNTER = 3  # for naming new vBBUs

orch_log_path = "../outputs/orch_output.txt"

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
            conn.sendall(b"[OK] Assignments received\n")
            log_orch(f"[ASSIGN] Received {count} UE assignments from RRH")
        elif cmd == 'migrate':
            handle_full_migration(message, conn)
        else:
            conn.sendall(b"[ERROR] Unknown command.\n")
    except Exception as e:
        log_orch(f"[ERROR] Command error from {addr}: {e}")
        conn.sendall(b"[ERROR] Internal failure.\n")
    finally:
        conn.close()

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
    log = f"[HANDOVER] {ue_id} → {new_ip}:{new_port}"
    log_orch(log)

    if conn:
        conn.sendall(json.dumps({"status": "ok", "message": log}).encode())

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
            log_orch(f"[RRH] {response.decode().strip()}")
    except Exception as e:
        log_orch(f"[ERROR] RRH unreachable: {e}")

def handle_full_migration(message, conn):
    global VBBU_COUNTER

    from_vbbu = message.get('from_vbbu')
    if not from_vbbu:
        conn.sendall(b"[ERROR] from_vbbu is required.\n")
        return

    new_ip = f"10.0.0.{200+VBBU_COUNTER}"
    new_port = 8080 + VBBU_COUNTER
    new_vbbu = f"{new_ip}:{new_port}"
    vbbu_name = f"vbbu{VBBU_COUNTER}"

    VBBU_COUNTER += 1

    launch_cmd = f"mnexec -a 1 xterm -e 'python3 /home/mininet/vbbu_server.py {new_port} > /tmp/{vbbu_name}.log 2>&1 &'"
    os.system(launch_cmd)
    log_orch(f"[SPAWN] Started {vbbu_name} at {new_vbbu}")

    redirected_vbbus[from_vbbu] = new_vbbu

    migrated = []
    for ue_id, assignment in list(ue_assignments.items()):
        current = f"{assignment['vbbu_ip']}:{assignment['vbbu_port']}"
        if current == from_vbbu:
            ip, port = new_ip, new_port
            cmd = {
                "command": "handover",
                "ue_id": ue_id,
                "new_vbbu_ip": ip,
                "new_vbbu_port": port
            }
            handle_handover_command(cmd)
            migrated.append(ue_id)

    response = {
        "status": "ok",
        "migrated_ues": migrated,
        "new_vbbu": new_vbbu
    }
    conn.sendall(json.dumps(response).encode())
    log_orch(f"[MIGRATION] {len(migrated)} UEs moved from {from_vbbu} to {new_vbbu}")

def start_orchestrator():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((ORCH_HOST, ORCH_PORT))
        server.listen(5)
        log_orch(f"[ORCH] Listening on {ORCH_HOST}:{ORCH_PORT}")
        while True:
            conn, addr = server.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

def cli_loop():
    while True:
        try:
            raw = input("Orchestrator> ").strip()
            if raw.startswith("handover"):
                _, ue, vbbu = raw.split()
                vbbu_map = {
                    "vbbu1": ("10.0.0.201", 8080),
                    "vbbu2": ("10.0.0.202", 8081)
                }
                if vbbu not in vbbu_map:
                    print("[ERROR] Unknown vBBU name.")
                    continue
                ip, port = vbbu_map[vbbu]
                cmd = {
                    "command": "handover",
                    "ue_id": ue.upper(),
                    "new_vbbu_ip": ip,
                    "new_vbbu_port": port
                }
                handle_handover_command(cmd)
                print(f"[OK] Sent handover: {ue} → {vbbu}")

            elif raw.startswith("migrate"):
                _, src, dst = raw.split()
                vbbu_map = {
                    "vbbu1": "10.0.0.10:8080",
                    "vbbu2": "10.0.0.20:8081"
                }
                if src not in vbbu_map or dst not in vbbu_map:
                    print("[ERROR] Unknown vBBU name.")
                    continue
                from_vbbu = vbbu_map[src]
                to_ip, to_port = vbbu_map[dst].split(":")
                redirected_vbbus[from_vbbu] = vbbu_map[dst]

                migrated = []
                for ue_id, assignment in list(ue_assignments.items()):
                    current = f"{assignment['vbbu_ip']}:{assignment['vbbu_port']}"
                    if current == from_vbbu:
                        cmd = {
                            "command": "handover",
                            "ue_id": ue_id,
                            "new_vbbu_ip": to_ip,
                            "new_vbbu_port": int(to_port)
                        }
                        handle_handover_command(cmd)
                        migrated.append(ue_id)
                print(f"[OK] Migrated {len(migrated)} UEs from {src} → {dst}")

            elif raw == "show assignments":
                if not ue_assignments:
                    print("[INFO] No UE assignments found.")
                else:
                    for ue, vbbu in ue_assignments.items():
                        vbbu_str = f"{vbbu['vbbu_ip']}:{vbbu['vbbu_port']}"
                        print(f"{ue} → vBBU{vbbu_str.split(":")[0].split(".")[-1][-1]}")

            elif raw == "show loads":
                for ip, info in vbbu_loads.items():
                    print(f"{ip} → CPU: {info['cpu']}, Connections: {info['connections']}")

            elif raw in ["quit", "exit"]:
                print("Exiting orchestrator.")
                break

            else:
                print("Commands:")
                print("  handover UE9 vbbu1")
                print("  migrate vbbu1 vbbu2")
                print("  show assignments")
                print("  show loads")
                print("  quit")

        except Exception as e:
            print(f"[CLI ERROR] {e}")

if __name__ == "__main__":
    threading.Thread(target=start_orchestrator, daemon=True).start()
    cli_loop()
