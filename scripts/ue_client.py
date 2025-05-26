#!/usr/bin/env python3
"""
UE Client for COMIC-RAN demo with HTTP-managed destination switching.

Endpoints:
  GET /add    -> switch to RRH IP
  GET /remove -> switch to dummy IP

Usage:
  python3 ue_client.py <rrh_ip>
"""
import requests
import sys
import time
import os
import json
import random
import string
import socket
import fcntl
import struct
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# === Configuration ===
PORT = 5000
DUMMY_IP = '10.0.0.200'

# === Parse args ===
if len(sys.argv) < 2:
    print("Usage: python3 ue_client.py <rrh_ip>")
    sys.exit(1)
rrh_ip = sys.argv[1]
# Global dynamic destination IP (starts at RRH)
dest_ip = rrh_ip

# === Logging setup ===
ue_id = None
log_path = None

def log_ue(message):
    """Append a timestamped message to the UE log."""
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{timestamp}] {message}"
    with open(log_path, 'a') as f:
        f.write(line + '\n')

# === HTTP Management Server ===
class ManagerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global dest_ip
        if self.path == '/add':
            dest_ip = rrh_ip
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'Switched to RRH')
        elif self.path == '/remove':
            dest_ip = DUMMY_IP
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'Switched to Dummy')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Suppress default HTTP request logging
        pass


def start_http_server():
    server = HTTPServer(('0.0.0.0', PORT), ManagerHandler)
    server.serve_forever()

# Launch HTTP server thread
threading.Thread(target=start_http_server, daemon=True).start()

# === Helper functions ===
def get_id():
    """Return the last byte of the UE's IP address as integer ID."""
    interfaces = os.listdir('/sys/class/net/')
    ifname = 'lo'
    for iface in interfaces:
        if iface != 'lo' and iface.endswith('eth0'):
            ifname = iface
            break
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ip = socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15].encode('utf-8'))
    )[20:24])
    return int(ip.strip().split('.')[-1])

# === Main UE loop ===
# Initialize
ue_id = get_id()
log_dir = os.path.join(os.path.dirname(__file__), '..', 'outputs')
os.makedirs(log_dir, exist_ok=True)
log_path = os.path.join(log_dir, f"ue{ue_id}_output.txt")

log_ue(f"Starting UE client #{ue_id}, initial target={rrh_ip}")

value = 0
rrh_status = True
vbbu_status = True

# UE agent lifecycle
while True:
    payload = {"ue_id": ue_id, "value": value}
    try:
        # Use dynamic destination IP
        response = requests.get(
            f'http://{dest_ip}:8000/', params=payload, timeout=3
        )
        rrh_status = True
        if response.status_code != 200:
            if vbbu_status:
                vbbu_status = False
                log_ue(f"Error: Connected vBBU unavailable. Value: {value}")
            raise Exception(f"Unexpected status: {response.status_code}")
        result = response.json()
        ack = result.get('acknowledgement')
        vbbu_id = result.get('vbbu_id')
        log_ue(f"    [RESPONSE] Ack#{value} from vBBU{vbbu_id} to UE{ue_id}")
        value += 1

    except Exception as e:
        if rrh_status:
            log_ue(f"Error: RRH unreachable. Value: {value}")
            value = 0
            rrh_status = False

    time.sleep(random.uniform(1.5, 3.0))
