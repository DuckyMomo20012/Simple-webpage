import mimetypes
import os
import socket


class HttpServer:
    def __init__(self, host, port):
        self.HOST = host
        self.PORT = port
        self.s = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind((self.HOST, self.PORT))
        self.s.listen(5)
        self.request = str()
        self.request_header = dict()
        self.request_body = dict()
        self.response = list()

    def serve_forever(self):
        while True:
            conn, address = self.s.accept()
            try:
                self.request = conn.recv(1024).decode('utf-8')
                print("Connect to: %s-port: %d" % (self.HOST, self.PORT))
                self.handle()
                conn.send(b"".join(self.response))
                self.response = []
            finally:
                conn.close()

    def send_response(self, status_code):
        self.response.append(b"%s %s\r\n" % (b"HTTP/1.1", status_code.encode("utf-8")))

    def send_header(self, keyword, value):
        self.response.append(b"%s: %s\r\n" % (keyword.encode("utf-8"), value.encode("utf-8")))

    def end_header(self):
        self.response.append(b"\r\n")

    def translate_path(self):
        self.request = self.request.split("\r\n")
        parts: str
        for parts in self.request[1:]:
            if "&" not in parts:
                line = parts.split(" ")
                if line[0] != "":
                    self.request_header.update({line[0][:-1]: line[1]})
            else:
                line = parts.split("&")
                for pairs in line:
                    pairs = pairs.split("=")
                    self.request_body.update({pairs[0]: pairs[1]})

        return self.request[0]

    def handle(self):
        request_line = self.translate_path().split(" ")
        f = str(request_line[1])
        if f == '/':
            path = 'index.html'
        else:
            path = f[1:]
        if request_line[0] == "GET":
            self.do_GET(path)

        if request_line[0] == "POST":
            self.do_POST(path)

        # if request_line[0] == "OPTIONS":
        #     self.do_OPTION()

    def do_GET(self, path):
        f = None
        filetype = self.guess_type(path)
        if "&" in path:
            query = path.split("&")
            username = query[0].split("=")[1]
            password = query[1].split("=")[1]
            print("username:%s - password:%s" % (username, password))
            if username == "admin" and password == "admin":
                path = "/info.html"
            else:
                path = "/404.html"
            self.send_response("301 MOVED PERMANENTLY")
            self.send_header("Location", "%s" % path)
            return None
        try:
            f = open(path, 'rb')
            self.send_response("200 OK")
            self.send_header("Connection", "keep-alive")
            self.send_header("Content-type", filetype)

        except OSError:
            f = open('404.html', 'rb')
            self.send_response('404 NOT FOUND')
            self.send_header("Connection", "keep-alive")
            self.send_header("Content-type", filetype)
        finally:
            # self.send_header("Content-Disposition", 'attachment; filename="{filename}"'.format(filename=path.strip("/")))
            self.chunk_send(f)
            # self.send_file(f, filetype)

    def do_POST(self, path):
        if len(self.request_body) != 0:
            if "username" and "password" in self.request_body:
                filetype = self.guess_type(path)
                username = self.request_body["username"]
                password = self.request_body["password"]
                print("username:%s - password:%s" % (username, password))
                if username == "admin" and password == "admin":
                    path = "/info.html"
                else:
                    path = "/404.html"

                self.send_response("201 CREATED")
                self.send_header("Location", "%s" % path)
                self.send_header("Connection", "keep-alive")
                self.send_header("Content-type", filetype)
                f = open(path, 'rb')
                self.send_file(f, filetype)

    # def do_OPTION(self):
    #     self.send_response("204 NO CONTENT")
    #     self.send_header("Access-Control-Allow-Origin", self.request_header["Origin"])
    #     self.send_header("Access-Control-Allow-Methods", "%s, %s, %s" % ("GET", "POST", "OPTIONS"))
    #     self.send_header("Connection", "keep-alive")

    def guess_type(self, path):
        guess, _ = mimetypes.guess_type(path)
        if guess:
            return guess
        return 'application/octet-stream'

    def chunk_send(self, f):
        print("chunk send")
        self.send_header("Transfer-Encoding", "chunked")
        self.end_header()
        try:
            chunk_size = 1024
            while True:
                buf = f.read(chunk_size)
                if not buf:
                    self.response.append(b'0\r\n\r\n')
                    break

                self.response.append(b"%s\r\n%s\r\n" % (hex(len(buf))[2:].encode("ascii"), buf))
        finally:
            f.close()

    def content_length_send(self, f):
        print("content-length send")
        response = []
        _WINDOWS = os.name == 'nt'
        COPY_BUFFSIZE = 1024 * 1024 if _WINDOWS else 64 * 1024
        try:
            while True:
                buf = f.read(COPY_BUFFSIZE)
                if not buf:
                    break

                response.append(b"%s" % buf)
            self.send_header("Content-length", str(len(b"".join(response))))
            self.end_header()
            self.response.extend(response)
        finally:
            f.close()

    def send_file(self, f, filetype):
        # if filetype == "text/html" or filetype == "text/css":
        #     self.content_length_send(f)
        # else:
        #     self.chunk_send(f)
        pass


server = HttpServer("127.0.0.1", 80)
server.serve_forever()
