import socket
from struct import pack,unpack

serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

serversocket.bind((socket.gethostname(), 80))

serversocket.listen(5)
