import requests
import sys
import time

if len(sys.argv) < 2:
    print("Usage: python3 ue_client.py <rrh_ip>")
    exit(1)

rrh_ip = sys.argv[1]

print(f"Starting continuous request loop to RRH ({rrh_ip})...")

while True:
    try:
        r = requests.get(f"http://{rrh_ip}:8000", timeout=2)
        print("[✔] Response:", r.text.strip())
    except Exception as e:
        print("[✘] ERROR:", e)
    time.sleep(1)  # delay between requests

