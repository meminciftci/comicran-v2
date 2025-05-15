from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
import sys
import json
import time

port = int(sys.argv[1])
# vbbu_id = "vbbu1" if port == 8080 else "vbbu2"
vbbu_id = f"vbbu{port - 8080 + 1}"
print(vbbu_id)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        value = int(params.get('value', [0])[0])
        ue_id = int(params.get('ue_id', [0])[0])

        # response = f"{vbbu_id}, recieved: {value}, returning: {result}"
        response = json.dumps({
            "vbbu_id": vbbu_id[-1],
            "acknowledgement": f"Acknowledgement #{value}"
        })
        log_line = f"[{timestamp}] Value {value}: Recieved from UE #{ue_id}"
        print(log_line)

        self.send_response(200)
        self.end_headers()
        self.wfile.write(str(response).encode())
        
    def log_message(self, format, *args):
        return        

if __name__ == '__main__':
    print(f"vBBU server running on port {port} as {vbbu_id}")
    HTTPServer(('', port), Handler).serve_forever()
