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

def get_id():
    """Gets last byte of IP address (e.g., 10.0.0.25 → 25)"""
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
    return int(ip.strip().split(".")[-1])  # last byte of IP as ID

def log_ue(message):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{timestamp}] {message}"
    with open(log_path, "a") as f:
        f.write(line + "\n")

# === Entry point ===
if len(sys.argv) < 2:
    print("Usage: python3 ue_client.py <rrh_ip>")
    exit(1)

rrh_ip = sys.argv[1]
ue_id = get_id()
log_path = os.path.join("../outputs", f"ue{ue_id}_output.txt")

log_ue(f"Starting UE client #{ue_id} targeting RRH at {rrh_ip}")

value = 0
rrh_status = True
vbbu_status = True

# === UE agent lifecycle ===


while True:
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    payload = {
        "ue_id": ue_id,
        "value": value
    }

    try:
        response = requests.get(f"http://{rrh_ip}:8000/", params=payload, timeout=3)
        rrh_status = True
        if response.status_code != 200:
            if vbbu_status:
                vbbu_status = False
                log_ue(f"Error: Connected vBBU unavailable. Value: {value}")
                raise Exception(f"Unexpected status code: {response.status_code}")
        result = response.json()
        acknowledgement = result.get("acknowledgement")
        vbbu_id = result.get("vbbu_id")
        log_ue(f"    [RESPONSE] Ack#{value} from vBBU{vbbu_id} to UE{ue_id}")
        value += 1

    except Exception as e:
        if rrh_status:
            log_ue(f"Error: RRH unreachable. Value: {value}")
            rrh_status = False

    time.sleep(random.uniform(1.5, 3.0))

