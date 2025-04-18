from http.server import BaseHTTPRequestHandler, HTTPServer
import requests

# Per-UE routing table (UE IP → target vBBU address)
ue_target = {
    "10.0.0.1": "10.0.0.10:8080",  # ue1 → vbbu1
    "10.0.0.2": "10.0.0.10:8080",  # ue2 → vbbu1 (initially)
}

class ProxyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        client_ip = self.client_address[0]
        target = ue_target.get(client_ip)

        if not target:
            self.send_response(403)
            self.end_headers()
            self.wfile.write(f"Unknown client {client_ip}".encode())
            return

        url = f"http://{target}{self.path}"
        print(f"[{client_ip}] → Forwarding to {url}")

        try:
            resp = requests.get(url)
            self.send_response(resp.status_code)
            self.end_headers()
            self.wfile.write(resp.content)
        except Exception as e:
            self.send_response(502)
            self.end_headers()
            self.wfile.write(f"Forwarding failed: {e}".encode())

if __name__ == '__main__':
    import threading

    def control_loop():
        while True:
            raw = input("Handover> ").strip()
            if raw.startswith("set"):
                try:
                    _, ue, vbbu = raw.split()
                    if ue == "ue1":
                        ip = "10.0.0.1"
                    elif ue == "ue2":
                        ip = "10.0.0.2"
                    else:
                        print("Unknown UE.")
                        continue

                    if vbbu == "vbbu1":
                        ue_target[ip] = "10.0.0.10:8080"
                    elif vbbu == "vbbu2":
                        ue_target[ip] = "10.0.0.20:8081"
                    else:
                        print("Unknown vBBU.")
                        continue

                    print(f"✔ {ue} now routes to {vbbu}")
                except:
                    print("Usage: set ue1|ue2 vbbu1|vbbu2")
            elif raw == "show":
                for k, v in ue_target.items():
                    print(f"{k} → {v}")
            else:
                print("Commands: set <ue1|ue2> <vbbu1|vbbu2>, show")

    threading.Thread(target=control_loop, daemon=True).start()

    server = HTTPServer(('', 8000), ProxyHandler)
    print("RRH proxy running on port 8000 (per-UE forwarding)")
    server.serve_forever()

