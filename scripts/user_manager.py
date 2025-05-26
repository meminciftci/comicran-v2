#!/usr/bin/env python3
"""
HTTP-Driven UE Manager for COMIC-RAN demo.

When you call `add <id>` or `remove <id>`, this script sends a GET request to the UE client
listening on port 5000 at IP 10.0.0.<id>. The UE client must expose /add and /remove endpoints
and update its destination IP accordingly.

Usage:
  python3 user_manager.py
  UEManager> list
  UEManager> remove 3   # sends GET http://10.0.0.3:5000/remove
  UEManager> add 3      # sends GET http://10.0.0.3:5000/add
  UEManager> remove 1 2 3  # removes multiple users
  UEManager> add 1 2 3     # adds multiple users
  UEManager> remove all    # removes all users
  UEManager> exit
"""
import requests
import sys

# Configuration
VALID_IDS = set(range(1, 11))
PORT = 5000
# Track state: 'rrh' or 'diconnected'
states = {uid: 'rrh' for uid in VALID_IDS}


def send_cmd(uid: int, cmd: str):
    """Send GET request to the UE's management endpoint."""
    ue_ip = f'10.0.0.{uid}'
    url = f'http://{ue_ip}:{PORT}/{cmd}'
    try:
        resp = requests.get(url, timeout=2)
        if resp.status_code == 200:
            print(f"[OK] UE{uid} acknowledged '{cmd}'.")
            return True
        else:
            print(f"[ERROR] UE{uid} returned status {resp.status_code} for '{cmd}'")
    except requests.RequestException as e:
        print(f"[ERROR] Failed to reach UE{uid} at {url}: {e}")
    return False


def add(uid: int):
    if states[uid] == 'rrh':
        print(f"[WARN] UE{uid} already on RRH.")
        return
    if send_cmd(uid, 'add'):
        states[uid] = 'rrh'


def remove(uid: int):
    if states[uid] == 'disconnected':
        print(f"[WARN] UE{uid} already disconnected.")
        return
    if send_cmd(uid, 'remove'):
        states[uid] = 'disconnected'


def process_multiple_users(cmd: str, uids: list[int]):
    """Process multiple user IDs for add or remove command."""
    for uid in uids:
        if cmd == 'add':
            add(uid)
        else:
            remove(uid)


def list_status():
    for uid in sorted(VALID_IDS):
        print(f"UE{uid}: {states[uid]}")


def usage():
    print("Commands:")
    print("  add <id> [id2 id3 ...] — instruct UE(s) to route to RRH")
    print("  remove <id> [id2 id3 ...] — instruct UE(s) to disconnect")
    print("  remove all — instruct all UEs to disconnect")
    print("  list        — show all UE statuses")
    print("  exit        — quit manager")


def main():
    print("UE Manager started. Initial state: all UEs on RRH.")
    usage()
    while True:
        try:
            parts = input('UEManager> ').strip().split()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not parts:
            continue
        cmd = parts[0].lower()
        if cmd == 'exit':
            break
        elif cmd == 'list':
            list_status()
        elif cmd in ('add', 'remove'):
            if len(parts) < 2:
                usage()
                continue
                
            if parts[1].lower() == 'all' and cmd == 'remove':
                process_multiple_users(cmd, list(VALID_IDS))
                continue
                
            # Process multiple user IDs
            try:
                uids = [int(uid) for uid in parts[1:]]
                invalid_ids = [uid for uid in uids if uid not in VALID_IDS]
                if invalid_ids:
                    print(f"[ERROR] Invalid UE IDs: {invalid_ids}. Use 1–10.")
                    continue
                process_multiple_users(cmd, uids)
            except ValueError:
                print("[ERROR] Invalid UE ID format. Use numbers 1-10.")
        else:
            usage()
    print("Exiting UE Manager.")


if __name__ == '__main__':
    main()
