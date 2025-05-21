import socket
import threading
import json
import logging
import time
import random

ORCH_HOST = '0.0.0.0'
ORCH_PORT = 9100
RRH_CONTROL_IP = '10.0.0.100'
RRH_CONTROL_PORT = 9200

ue_assignments = {}
vbbu_loads = {}
redirected_vbbus = {}

CPU_OVERLOAD = 8
MAX_CONNECTIONS = 10
VBBU_COUNTER = 3  # for naming new vBBUs

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
        elif cmd == 'migrate':
            handle_full_migration(message, conn)
        else:
            conn.sendall(b"[ERROR] Unknown command.\n")
    except Exception as e:
        logging.error(f"[ERROR] Command error from {addr}: {e}")
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
    logging.info(log)

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

    logging.info(f"[LOAD] {vbbu_ip}: CPU={cpu}, Conn={connections}")
    conn.sendall(b"[OK] Load received.\n")

def forward_to_rrh(message):
    try:
        with socket.create_connection((RRH_CONTROL_IP, RRH_CONTROL_PORT), timeout=3) as sock:
            sock.sendall(json.dumps(message).encode())
            response = sock.recv(4096)
            logging.info(f"[RRH] {response.decode().strip()}")
    except Exception as e:
        logging.error(f"[ERROR] RRH unreachable: {e}")

def handle_full_migration(message, conn):
    global VB_BU_COUNTER

    from_vbbu = message.get('from_vbbu')
    if not from_vbbu:
        conn.sendall(b"[ERROR] from_vbbu is required.\n")
        return

    # Auto-generate new vBBU
    new_ip = f"10.0.0.{30 + VBBU_COUNTER}"
    new_port = 8080 + VBBU_COUNTER
    new_vbbu = f"{new_ip}:{new_port}"
    vbbu_name = f"vbbu{VBBU_COUNTER}"

    VB_BU_COUNTER += 1

    # Launch new vBBU via shell
    launch_cmd = f"mnexec -a 1 xterm -e 'python3 /home/mininet/vbbu_server.py {new_port} > /tmp/{vbbu_name}.log 2>&1 &'"
    os.system(launch_cmd)
    logging.info(f"[SPAWN] Started {vbbu_name} at {new_vbbu}")

    # Redirect mapping for unknown UEs
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
    logging.info(f"[MIGRATION] {len(migrated)} UEs moved from {from_vbbu} to {new_vbbu}")

def start_orchestrator():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((ORCH_HOST, ORCH_PORT))
        server.listen(5)
        logging.info(f"[ORCH] Listening on {ORCH_HOST}:{ORCH_PORT}")
        while True:
            conn, addr = server.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    import os
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
    start_orchestrator()
