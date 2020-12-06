from http.server import BaseHTTPRequestHandler
import socketserver

HOST = '127.0.0.1'
PORT = 8000


with socketserver.TCPServer((HOST, PORT), BaseHTTPRequestHandler) as server:
    server.serve_forever()
