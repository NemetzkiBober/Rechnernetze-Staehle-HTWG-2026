# Kleine Experimente zu den Fragen aus Aufgabe 3.2
import socket
import time

IP = '127.0.0.1'
PORT = 50001

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((IP, PORT))
server.listen(1)


print('--- Frage 1 + 2: Wann bekommt der Client IP und Port? ---')
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print('TCP vor connect():  ', client.getsockname())   # noch nichts vergeben
client.connect((IP, PORT))
print('TCP nach connect(): ', client.getsockname())   # jetzt vom Betriebssystem vergeben
print('Gegenseite:         ', client.getpeername())
conn, addr = server.accept()
print('Server sieht Client:', addr)
conn.close()
client.close()

udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
print('UDP vor sendto():   ', udp.getsockname())
udp.sendto(b'hallo', (IP, PORT))                      # niemand hört zu, egal
print('UDP nach sendto():  ', udp.getsockname())
udp.close()


print('--- Frage 3: IP und Port selbst festlegen ---')
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.bind((IP, 54321))                              # bind() VOR connect()
client.connect((IP, PORT))
conn, addr = server.accept()
print('Client mit bind():  ', client.getsockname(), '| Server sieht:', addr)
conn.close()
client.close()


print('--- Frage 4: gemeinsamer Timeout für alle Sockets ---')
socket.setdefaulttimeout(2)                           # gilt für alle NEU erzeugten Sockets
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
print('Timeout des neuen Sockets:', s.gettimeout())
start = time.time()
try:
    s.recvfrom(100)                                   # es kommt nie etwas
except socket.timeout:
    print('socket.timeout nach', round(time.time() - start, 1), 's')
s.close()
socket.setdefaulttimeout(None)                        # wieder aus


print('--- Frage 5: TCP und UDP auf demselben Port? ---')
PORT5 = 50002
tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp.bind((IP, PORT5))
tcp.listen(1)
udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp.bind((IP, PORT5))
print('TCP und UDP beide auf Port', PORT5, 'gebunden')

# Beide wirklich benutzen
c_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
c_udp.sendto(b'per UDP', (IP, PORT5))
print('UDP-Socket empfängt:', udp.recvfrom(100)[0])
c_tcp = socket.create_connection((IP, PORT5))
c_tcp.sendall(b'per TCP')
conn, _ = tcp.accept()
print('TCP-Socket empfängt:', conn.recv(100))

# Gegenprobe: ein zweiter TCP-Socket auf denselben Port
try:
    tcp2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp2.bind((IP, PORT5))
except OSError as e:
    print('Zweiter TCP-Socket:', e)

for s in (conn, c_tcp, c_udp, tcp, udp, tcp2, server):
    s.close()
