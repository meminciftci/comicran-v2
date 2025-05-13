from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
import sys
import json

port = int(sys.argv[1])
vbbu_id = "vbbu1" if port == 8080 else "vbbu2"

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        value = int(params.get('value', [0])[0])
        result = value + 1

        # response = f"{vbbu_id}, recieved: {value}, returning: {result}"
        response = json.dumps({
            "vbbu": vbbu_id,
            "received": value,
            "returned": result
        })
        print(response)

        self.send_response(200)
        self.end_headers()
        self.wfile.write(str(response).encode())
        
    def log_message(self, format, *args):
        return        

if __name__ == '__main__':
    print(f"vBBU server running on port {port} as {vbbu_id}")
    HTTPServer(('', port), Handler).serve_forever()
