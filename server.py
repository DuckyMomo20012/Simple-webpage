import mimetypes
import socket
from datetime import datetime


class HttpServer:
    def __init__(self, port, host = '0.0.0.0'):
        self.HOST = host
        self.PORT = port
        self.request = str()
        self.request_header = dict()
        self.request_body = dict()
        self.response = list()
        self.status_code = str()
        self.s = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind((self.HOST, self.PORT))
        self.s.listen(5)

    def serve_forever(self):
        while True:
            conn, address = self.s.accept()
            try:
                self.request = conn.recv(1024).decode('utf-8')
                self.translate_path()
                if self.request_body:
                    print(self.request_body)
                today = datetime.today().strftime("%d/%b/%Y")
                time = datetime.now().strftime("%H:%M:%S")
                self.handle()
                print('%s - - [%s % s] "%s" %s -' % (self.HOST, today, time, self.request[0], self.status_code))
                conn.send(b"".join(self.response))
                self.response = []
            finally:
                conn.close()

    def send_response(self, status_code):
        self.status_code = status_code
        self.response.append(b"%s %s\r\n" % (b"HTTP/1.1", status_code.encode("utf-8")))

    def send_header(self, keyword, value):
        self.response.append(b"%s: %s\r\n" % (keyword.encode("utf-8"), value.encode("utf-8")))

    def end_header(self):
        self.response.append(b"\r\n")

    def translate_path(self):
        self.request = self.request.split("\r\n")
        parts: str
        for parts in self.request[1:]:  # ignore 'Method "GET" or "POST"'
            if "&" not in parts:
                line = parts.split(" ")
                if line[0] != "":
                    self.request_header.update({line[0][:-1]: line[1]})  # remove ":"
            else:
                line = parts.split("&")  # get request body
                for pairs in line:
                    pairs = pairs.split("=")
                    self.request_body.update({pairs[0]: pairs[1]})

    def handle(self):
        request_line = self.request[0].split(" ")
        try:
            f = str(request_line[1])
            if f == '/':
                path = 'index.html'
            else:
                path = f[1:]  # ignore first dash
            if request_line[0] == "GET":
                self.do_GET(path)

            if request_line[0] == "POST":
                self.do_POST(path)
        except OSError:
            print("error")
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
                path = "info.html"
            else:
                path = "404.html"
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
            self.send_file(f, filetype)

    def do_POST(self, path):
        if len(self.request_body) != 0:
            if "username" and "pass" in self.request_body:
                filetype = self.guess_type(path)
                username = self.request_body["username"]
                password = self.request_body["pass"]
                print("username:%s - password:%s" % (username, password))
                if username == "admin" and password == "admin":
                    path = "info.html"
                else:
                    path = "404.html"

                self.send_response("301 MOVED PERMANENTLY")
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
        # print('"%s": %s' % (f.name, "chunk send"))

    def content_length_send(self, f):
        response = []
        COPY_BUFFERSIZE = 10485760
        try:
            while True:
                buf = f.read(COPY_BUFFERSIZE)
                if not buf:
                    break

                response.append(b"%s" % buf)
            self.send_header("Content-length", str(len(b"".join(response))))
            self.end_header()
            self.response.extend(response)
        finally:
            f.close()
        # print('"%s": %s' % (f.name, "content-length send"))

    def send_file(self, f, filetype):
        try:
            if filetype == "text/html" or filetype == "text/css":
                self.content_length_send(f)
            else:
                self.chunk_send(f)
        except:
            print('There was an error')
        else:
            print(f"{f.name} sent")


# server = HttpServer("127.0.0.1", 80)
server = HttpServer(port = 80)
server.serve_forever()
