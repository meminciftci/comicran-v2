from http.server import BaseHTTPRequestHandler, HTTPServer
import sys

class VBBUHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        response = f"Response from vBBU on port {self.server.server_port}"
        self.wfile.write(response.encode())

if __name__ == "__main__":
    port = int(sys.argv[1])
    server = HTTPServer(('', port), VBBUHandler)
    print(f"vBBU server started on port {port}")
    server.serve_forever()

