from http.server import SimpleHTTPRequestHandler
import socketserver

HOST = '127.0.0.1'
PORT = 8000

with socketserver.TCPServer((HOST, PORT), SimpleHTTPRequestHandler) as server:
    server.serve_forever()
