import mimetypes
import socket


class HTTPserver:
    def __init__(self, HOST, PORT):
        self.s = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        self.s.bind((HOST, PORT))
        self.s.listen(1)
        self.request = ""
        self.response = []

    def serve_forever(self):
        while True:
            self.conn, self.addr = self.s.accept()
            self.request = self.conn.recv(1024).decode('utf-8')
            self.handle()
            # conn.sendall(b"".join(self.response))
            self.response = []

    def send_response(self, status_code):
        self.response.append(b"%s %s\r\n" % (b"HTTP/1.1", status_code.encode("utf-8")))

    def send_header(self, keyword, value):
        self.response.append(b"%s: %s\r\n" % (keyword.encode("utf-8"), value.encode("utf-8")))

    def end_header(self):
        self.response.append(b"\r\n")

    def translate_path(self):
        self.request = self.request.split("\r\n")
        return self.request[0]

    def handle(self):
        requesline = self.translate_path().split(" ")
        if requesline[0] == 'GET':
            f = requesline[1]
            if f == '/':
                path = 'index.html'
            else:
                path = f[1:]
            self.do_GET(path)

    def guess_type(self, path):
        guess, _ = mimetypes.guess_type(path)
        if guess:
            return guess
        return 'application/octet-stream'

    def do_GET(self, path):
        f = None
        try:
            f = open(path, 'rb')
            self.send_response("200 OK")
            self.send_header("Connection", "keep-alive")
            self.send_header("Content-type", self.guess_type(path))
            self.send_header("Transfer-Encoding", "chunked")
            self.end_header()

        except OSError:
            # self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            self.send_response('404 NOT FOUND')
            self.send_header("Connection", "keep-alive")
            self.send_header("Content-type", self.guess_type(path))
            self.send_header("Transfer-Encoding", "chunked")
            self.end_header()
            f = open('404.html', 'rb')

        finally:
            self.conn.sendall(b"".join(self.response))
            try:
                chunk_size = 1024
                while True:
                    buf = f.read(chunk_size)
                    # time.sleep(1) # only for illustrating chunked transferring
                    if not buf:
                        # self.response.append(b'0\r\n\r\n')
                        self.conn.sendall(b'0\r\n\r\n')
                        break

                    # self.response.append(b"%s\r\n%s\r\n" % (hex(len(buf))[2:].encode("ascii"), buf))
                    self.conn.sendall(b"%s\r\n%s\r\n" % (hex(len(buf))[2:].encode("ascii"), buf))
            finally:
                f.close()


server = HTTPserver("127.0.0.1", 8000)
server.serve_forever()
