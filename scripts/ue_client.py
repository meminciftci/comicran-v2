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
    """Gets IP address of a given interface (e.g., 'eth0')"""
    interfaces = os.listdir('/sys/class/net/')
    ifname = 'lo'
    for iface in interfaces:
        if iface != 'lo' and iface.endswith('eth0'):
            ifname = iface 
            break
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15].encode('utf-8'))
    )[20:24])

def log_ue(message):
    with open(log_path, "a") as f:
        f.write(message + "\n")


rrh_ip = sys.argv[1]
ue_id = int(get_id()[-1])
log_path = os.path.join("../outputs", f"ue_output.txt")


if len(sys.argv) < 2:
    print("Usage: python3 ue_client.py <rrh_ip>")
    exit(1)


log_line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting UE client to RRH ({rrh_ip})"
log_ue(log_line)
# with open(log_path, "a") as f:
#     f.write(log_line + "\n")
print(log_line)

value = 0
rrh_status = True
vbbu_status = True

while True:
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    payload = {
        "ue_id": ue_id,
        "value": value
    }

    try:
        # response = requests.get(f"http://{rrh_ip}:8000/?value={value}", timeout=2)
        response = requests.get(f"http://{rrh_ip}:8000/", params=payload, timeout=3)
        rrh_status = True
        if response.status_code != 200:
            if vbbu_status:
                vbbu_status = False
                log_line = f"[{timestamp}] Error: Connected vBBU is not available or none is found. Current value: [{value}] "
                log_ue(log_line)
                raise Exception(f"Unexpected status code: {response.status_code}")
        result = response.json()
        acknowledgement = result["acknowledgement"]
        vbbu_id = result["vbbu_id"]
        log_line = f"   [{timestamp}] {acknowledgement}: Recieved from vBBU #{vbbu_id}"
        log_ue(log_line)
        print(log_line)
        value += 1

    except Exception as e:
        if rrh_status:
            log_line = f"[{timestamp}] Error: Connected RRH is not available or none is found. Current value: [{value}]"
            log_ue(log_line)
            print(log_line)
            rrh_status = False

    except Exception as file_error:
        log_line = f"[{timestamp}] Error: Failed to write log. Current value: [{value}]"
        log_ue(log_line)

    time.sleep(1)  # delay between requests
