import datetime
import email
import os
import shutil
import urllib
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler
import socketserver

HOST = '127.0.0.1'
PORT = 8000


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        """Serve a GET request."""
        f = self.send_head()
        if f:
            try:
                chunk_size = 200
                while True:
                    buf = f.read(chunk_size)
                    if not buf:
                        self.wfile.write(b'0\r\n\r\n')
                        f.close()
                        break

                    self.wfile.write(hex(len(buf))[2:].encode('ascii') + b'\r\n' + buf + b'\r\n')
            finally:
                print('chunk sent')

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
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return None

        try:
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-type", ctype)
            # self.send_header("Content-Length", str(fs[6]))
            self.send_header("Transfer-encoding", 'chunked')
            self.end_headers()
            return f
        except:
            f.close()
            raise


with socketserver.TCPServer((HOST, PORT), Handler) as server:
    server.serve_forever()
