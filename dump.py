import socket
import selectors
import sys

if len(sys.argv) !=2:
    print(f"usage: {sys.argv[0]} <port>")
    sys.exit(1)

HOST = sys.argv[1]
PORT = 9000

sel=selectors.DefaultSelector()

redacted="O{'byteorder': 'little', 'lengthofdata': 10, 'request': 'push', 'user': 'admin'}"
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.listen()
    print(f'listening on {PORT}')
    sel.register(s, selectors.EVENT_READ, data=None)
    conn, addr = s.accept()
    with conn:
        print(f"Connected by {addr}")
        while True:
            data = conn.recv(1024)
            if not data:
                print(f'closing connection with {addr}')
                break
            else:
                print("Data received successfully. Printing data...")
                data=data.decode('utf-8')
                data=data[len(redacted)+1:len(data)]
                print(data)

