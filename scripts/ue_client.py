import requests
import sys
import time
import os
import json
import random
import string
import socket


def generate_dummy_data(size=1024):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=size))        # Buna ihtiyac var mı?

if len(sys.argv) < 2:
    print("Usage: python3 ue_client.py <rrh_ip>")
    exit(1)

rrh_ip = sys.argv[1]
ue_id = socket.gethostname()

log_path = os.path.join("../outputs", f"ue_output.txt")

log_line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting UE client to RRH ({rrh_ip})"
with open(log_path, "a") as f:
    f.write(log_line + "\n")
print(log_line)

value = 0
rrh_status = True
vbbu_status = True

while True:
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    payload = {
        "ue_id": ue_id,
        "value": value,
        "data": generate_dummy_data(1024)  # 1 KB dummy data
    }

    try:
        
        # response = requests.get(f"http://{rrh_ip}:8000/?value={value}", timeout=2)
        response = requests.get(f"http://{rrh_ip}:8000/", params=payload, timeout=3)
        rrh_status = True
        if response.status_code != 200:
            if vbbu_status:
                vbbu_status = False
                log_line = f"[{timestamp}] Value: [{value}] ✘ ERROR: Unexpected status code {response.status_code}"
                with open(log_path, "a") as f:
                    f.write(log_line + "\n")
                raise Exception(f"Unexpected status code: {response.status_code}")
        result = response.json()
        value_from_vbbu = result["returned"]
        vbbu_id = result["vbbu"]
        log_line = f"   [{timestamp}] Previous Value: {value}, New Value: {value_from_vbbu}, vBBU: {vbbu_id}"
        print(log_line)
        value = value_from_vbbu

    except Exception as e:
        if rrh_status:
            log_line = f"[{timestamp}] Value: [{value}] ✘ ERROR: {e}"
            with open(log_path, "a") as f:
                f.write(log_line + "\n")
            print(log_line)
            rrh_status = False

    try:
        if rrh_status and vbbu_status:
            with open(log_path, "a") as f:
                f.write(log_line + "\n")
    except Exception as file_error:
        print(f"[!] Failed to write log: {file_error}")

    time.sleep(1)  # delay between requests
