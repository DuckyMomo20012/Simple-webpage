import os
import urllib
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler
import socketserver

HOST = '127.0.0.1'
PORT = 8000


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        """Serve a GET request."""
        self.protocol_version = 'HTTP/1.1'
        f = self.send_head()
        if f:
            try:
                chunk_size = 1024
                while True:
                    buf = f.read(chunk_size)
                    # time.sleep(1) # only for illustrating chunked transferring
                    if not buf:
                        self.wfile.write(b'0\r\n\r\n')
                        break

                    self.wfile.write(hex(len(buf))[2:].encode('ascii') + b'\r\n' + buf + b'\r\n')

            finally:
                f.close()

    def send_head(self):
        path = self.translate_path(self.path)
        f = None
        if os.path.isdir(path):
            parts = urllib.parse.urlsplit(self.path)
            if not parts.path.endswith('/'):
                # redirect browser - doing basically what apache does
                self.send_response(HTTPStatus.MOVED_PERMANENTLY)
                new_parts = (parts[0], parts[1], parts[2] + '/',
                             parts[3], parts[4])
                new_url = urllib.parse.urlunsplit(new_parts)
                self.send_header("Location", new_url)
                self.end_headers()
                return None
            for index in "index.html", "index.htm":
                index = os.path.join(path, index)
                if os.path.exists(index):
                    path = index
                    break
            else:
                return self.list_directory(path)
        ctype = self.guess_type(path)
        # check for trailing "/" which should return 404. See Issue17324
        # The test for this was added in test_httpserver.py
        # However, some OS platforms accept a trailingSlash as a filename
        # See discussion on python-dev and Issue34711 regarding
        # parsing and rejection of filenames with a trailing slash
        if path.endswith("/"):
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return None
        try:
            f = open(path, 'rb')
        except OSError:
            # self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            self.send_response(HTTPStatus.NOT_FOUND)
            self.send_header("Transfer-Encoding", "chunked")
            f = open('404.html', 'rb')
            self.end_headers()
            return f

        try:
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-type", ctype)
            # self.send_header("Content-Length", str(fs[6]))
            self.send_header("Transfer-Encoding", "chunked")
            self.end_headers()
            return f
        except:
            f.close()
            raise

# def ReadRequest(Client):
#     re = ""
#     Client.settimeout(1)
#     try:
#         re = Client.recv(1024).decode()
#         while (re):
#             re = re + Client.recv(1024).decode()
#     except socket.timeout: # fail after 1 second of no activity
#         if not re:
#             print("Didn't receive data! [Timeout]")
#     finally:
#         return re
#
# def ReadHTTPRequest(Server):
#     re = ""
#     while (re == ""):
#         Client, address = Server.accept()
#         print("Client: ", address," da ket noi toi Server")
#         re = ReadRequest(Client)
#     return Client, re
#
# def CheckPass(Request):
#     if "POST / HTTP/1.1" not in Request:
#         return False
#     if "Username=admin&Password=admin" in Request:
#         return True
#     else:
#         return False

with socketserver.TCPServer((HOST, PORT), Handler) as server:
    server.serve_forever()
