import socket

HOST = '127.0.0.1'
PORT = 80
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(1)
print('SUCCESS')
conn, addr = s.accept()
conversation = ''
while conversation != 'exit':
    print('connect to', addr)
    data = conn.recv(1024)
    print('Receive' + data.decode("utf8"))
    conversation = input('type smt ')
    conn.sendall(bytes(conversation.encode("utf8")))
