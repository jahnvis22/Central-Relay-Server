import socket
import selectors
import sys
import struct
import json
import traceback
import io

# defining a message class that deals with the jsonheader and request(push) handling
class Message:
    def __init__(self, selector, sock, addr):
        self.selector = selector
        self.sock = sock
        self.addr = addr
        self._recv_buffer = b""
        self._send_buffer = b""
        self._jsonheader_len = None
        self.jsonheader = None
        self.request = None
        self.response_created = False
    
    def close(self):
        print(f"Closing connection to {self.addr}")
        try:
            self.selector.unregister(self.sock)
        except Exception as e:
            print(
                f"Error: selector.unregister() exception for "
                f"{self.addr}: {e!r}"
            )

        try:
            self.sock.close()
        except OSError as e:
            print(f"Error: socket.close() exception for {self.addr}: {e!r}")
        finally:
            # Delete reference to socket object for garbage collection
            self.sock = None

    def process_protoheader(self):
        hdrlen = 2
        if len(self._recv_buffer) >= hdrlen:
            self._jsonheader_len = struct.unpack(
                ">H", self._recv_buffer[:hdrlen]
            )[0]
            self._recv_buffer = self._recv_buffer[hdrlen:]
    
    def handle_push(self,jsonheader):
        jsonheader_bytes=json.dumps(jsonheader, ensure_ascii=False).encode()
        message_hdr = struct.pack(">H", len(jsonheader_bytes))

        message = message_hdr + jsonheader_bytes + self._recv_buffer
        self._send_buffer+=message
        try:
                # Sending data to dump server
                sent = dumpSocket.send(message)
        except BlockingIOError:
            pass
        else:
            self._send_buffer = self._send_buffer[sent:]
            # Close when the buffer is drained and the response has been sent.
            if sent and not self._send_buffer:
                self.close()



    def process_jsonheader(self):
        hdrlen = self._jsonheader_len
        if len(self._recv_buffer) >= hdrlen: 
            tiow = io.TextIOWrapper(
                io.BytesIO(self._recv_buffer[:hdrlen]),encoding="utf-8",newline=""
            )
            self.jsonheader  = json.load(tiow)
            tiow.close()
            self._recv_buffer = self._recv_buffer[hdrlen:]
            for reqhdr in (
                "byteorder",
                "lengthofdata",
                "request",
                "user",
            ):
                if reqhdr not in self.jsonheader:
                    raise ValueError(f"Missing required header '{reqhdr}'.")
                # checking if the request is push
            if self.jsonheader["request"]=="push":
                self.handle_push(self.jsonheader)
            

    def service_connection(self,mask):
        if mask & selectors.EVENT_READ:
            try:
                # Should be ready to read
                data = self.sock.recv(1024)
            except BlockingIOError:
                # Resource temporarily unavailable (errno EWOULDBLOCK)
                pass
            else:
                if data: # checking if the data has been received from the client
                    self._recv_buffer += data
                    if self._jsonheader_len is None:
                        self.process_protoheader()

                    if self._jsonheader_len is not None:
                        if self.jsonheader is None:
                            self.process_jsonheader()
    
                else: # closing connection with client if data is empty bytes 
                    print(f"Closing connection to {self.addr}")
                    selC.unregister(self.sock)
                    self.sock.close()

            

# checking if the number of arguments is 5

if len(sys.argv) != 4:
    print(f"Usage: {sys.argv[0]} <host> <dumpHost> <dumpPort>") # if number of arguments is not 5, then prompting the user with the usage of the server
    sys.exit(1)

selC=selectors.DefaultSelector()

selS=selectors.DefaultSelector()

# taking hosts and ports of the relay server and dump server as
# command line arguments
host=sys.argv[1]
port=8000
dumpHost=sys.argv[2]
dumpPort=int(sys.argv[3])


# function that accepts connections from client server
def accept_wrapper(sock):
    conn, addr = sock.accept()  # Should be ready to read
    print(f"Accepted connection from {addr}")
    conn.setblocking(False)
    message = Message(selC, conn, addr)
    selC.register(conn, selectors.EVENT_READ, data=message)


#binding the relay server with client
relaySocket= socket.socket()
relaySocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
relaySocket.bind((host,port))
relaySocket.listen()
print(f"listening on {(host,port)}")
relaySocket.setblocking(False)
selC.register(relaySocket, selectors.EVENT_READ, data=None)

#creating socket for relay server to dump server
dumpSocket= socket.socket()
dumpSocket.connect((dumpHost,dumpPort))
dumpSocket.setblocking(False)
selS.register(dumpSocket, selectors.EVENT_WRITE,data=None)

# checking if the objects have been connected already
# if not connected, then making the connection
# if connected, then receiving data
try:
    while True:
        events = selC.select(timeout=None)
        for key, mask in events:
            if key.data is None:
                accept_wrapper(key.fileobj)
            else:
                message = key.data
                try:
                    message.service_connection(mask)

                except Exception:
                    print(
                        f"Main: Error: Exception for {message.addr}:\n"
                        f"{traceback.format_exc()}"
                    )
                   
except KeyboardInterrupt:
    print("Caught keyboard interrupt, exiting")
finally:
    # closing selector objects
    selC.close()
    selS.close()









