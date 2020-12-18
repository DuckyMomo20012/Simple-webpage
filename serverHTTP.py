import mimetypes
import os
import socket


class HTTPserver:
    def __init__(self, HOST, PORT):
        self.HOST = HOST
        self.PORT = PORT
        self.s = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind((self.HOST, self.PORT))
        self.s.listen(5)
        self.request = ""
        self.request_header = {}
        self.response = []

    def serve_forever(self):
        while True:
            self.conn, self.addr = self.s.accept()
            try:
                self.request = self.conn.recv(1024).decode('utf-8')
                print("Connect to: %s-port: %d" % (self.HOST, self.PORT))
                self.handle()
                self.conn.send(b"".join(self.response))
                self.response = []
            finally:
                self.conn.close()

    def send_response(self, status_code):
        self.response.append(b"%s %s\r\n" % (b"HTTP/1.1", status_code.encode("utf-8")))

    def send_header(self, keyword, value):
        self.response.append(b"%s: %s\r\n" % (keyword.encode("utf-8"), value.encode("utf-8")))

    def end_header(self):
        self.response.append(b"\r\n")

    def translate_path(self):
        self.request = self.request.split("\r\n")
        for parts in self.request[1:]:
            line = parts.split(" ")
            if line[0] != "":
                self.request_header.update({line[0][:-1]: line[1]})
        return self.request[0]

    def handle(self):
        requestline = self.translate_path().split(" ")
        f = str(requestline[1])
        if f == '/':
            path = 'index.html'
        else:
            path = f[1:]
        if requestline[0] == "GET":
            self.do_GET(path)

        if requestline[0] == "POST":
            self.do_POST(path)

        if requestline[0] == "OPTIONS":
            self.do_OPTION()

    def guess_type(self, path):
        guess, _ = mimetypes.guess_type(path)
        if guess:
            return guess
        return 'application/octet-stream'

    def chunk_send(self, f):
        self.send_header("Transfer-Encoding", "chunked")
        self.end_header()
        try:
            chunk_size = 10
            while True:
                buf = f.read(chunk_size)
                # time.sleep(1) # only for illustrating chunked transferring
                if not buf:
                    self.response.append(b'0\r\n\r\n')
                    break

                self.response.append(b"%s\r\n%s\r\n" % (hex(len(buf))[2:].encode("ascii"), buf))
        finally:
            f.close()

    def content_length_send(self, f):
        response = []
        _WINDOWS = os.name == 'nt'
        COPY_BUFSIZE = 1024 * 1024 if _WINDOWS else 64 * 1024
        try:
            while True:
                buf = f.read(COPY_BUFSIZE)
                if not buf:
                    break

                response.append(b"%s" % buf)
            self.send_header("Content-length", str(len(b"".join(response))))
            self.end_header()
            self.response.extend(response)
        finally:
            f.close()

    def do_GET(self, path):
        f = None
        filetype = self.guess_type(path)
        if "&" in path:
            self.do_POST(path)
            return None
        try:
            f = open(path, 'rb')
            self.send_response("200 OK")
            self.send_header("Connection", "keep-alive")
            self.send_header("Content-type", filetype)
            if filetype == "text/html" or filetype == "text/css":
                self.content_length_send(f)
            else:
                self.chunk_send(f)

        except OSError:
            f = open('404.html', 'rb')
            self.send_response('404 NOT FOUND')
            self.send_header("Connection", "keep-alive")
            self.send_header("Content-type", filetype)
            if filetype == "text/html" or filetype == "text/css":
                self.content_length_send(f)
            else:
                self.chunk_send(f)

    def do_POST(self, path):
        if "&" in path:
            query = path.split("&")
            username = query[0].split("=")[1]
            password = query[1].split("=")[1]
            print("username:%s - password:%s" % (username, password))
            url = "%s%s/" % ("http://", self.HOST)
            if username == "admin" and password == "admin":
                path = "info.html"
                self.send_response("301 MOVED PERMANENTLY")
                self.send_header("Location", "%s%s" % (url, path))
            else:
                path = "404.html"
                self.send_response("301 MOVED PERMANENTLY")
                self.send_header("Location", "%s%s" % (url, path))

    def do_OPTION(self):
        self.send_response("204 NO CONTENT")
        self.send_header("Access-Control-Allow-Origin", self.request_header["Origin"])
        self.send_header("Access-Control-Allow-Methods", "%s, %s, %s" % ("GET", "POST", "OPTIONS"))
        self.send_header("Connection", "keep-alive")


server = HTTPserver("127.0.0.1", 80)
server.serve_forever()
