# Central-Relay-Server
Usage

To test the relay server, first run the dump server with the command

python3 dump.py <host> <port>

Next, run the relay server using the command

python3 relay.py <host> <port> <dumpHost> <dumpPort>

Finally, run the client with the command

python3 client.py <clientHost> <clientPort>

and input the message that is desired to be sent
