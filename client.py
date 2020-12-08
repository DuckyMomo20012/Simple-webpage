from http.client import HTTPConnection

HOST = '127.0.0.1'  # The server's hostname or IP address
PORT = 8000  # The port used by the server

conn = HTTPConnection(HOST, PORT)
headers = {'Connection': 'keep alive',
           # 'Transfer-Encoding': 'chunked',
           'Content-type': 'text/html'
           }

conn.request('GET', '/', headers=headers)


