# Aufgabe 3.3: TCP-Client mit Pipelining
# Alle Anfragen mit EINEM sendall() verschicken, danach alle Antworten lesen.

import socket
import time
from struct import pack, unpack

Server_IP = '127.0.0.1'   # für 3.2: IP des Server-Rechners (Meshnet/WLAN)
Server_PORT = 50000


def recv_exact(sock, n):
    data = b''
    while len(data) < n:
        stueck = sock.recv(n - len(data))
        if not stueck:
            return None
        data += stueck
    return data


def baue_anfrage(id, op, zahlen):
    n = len(zahlen)
    return pack('!I3sH', id, op.encode('utf-8'), n) + pack(f'!{n}i', *zahlen)


aufgaben = [
    (1, 'SUM', [1, 2, 3]),               # 6
    (2, 'PRO', [2, 3, 4]),               # 24
    (3, 'MAX', list(range(20000))),      # 19999  (große Anfrage mittendrin)
    (4, 'MIN', [5, -3, 8]),              # -3
    (5, 'SUM', [-1, -2, -3]),            # -6
]

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(10)
sock.connect((Server_IP, Server_PORT))
print('Verbunden, lokaler Socket:', sock.getsockname())

# Alles auf einmal: alle Anfragen hintereinander in einen Byte-String
alle = b''.join(baue_anfrage(id, op, zahlen) for id, op, zahlen in aufgaben)
sock.sendall(alle)
print(len(aufgaben), 'Anfragen mit einem sendall() geschickt,', len(alle), 'Bytes')

# Über die ID wissen wir, zu welcher Anfrage eine Antwort gehört
offen = {id: (op, len(zahlen)) for id, op, zahlen in aufgaben}
try:
    while offen:
        antwort = recv_exact(sock, 8)
        if antwort is None:
            print('Server hat die Verbindung geschlossen')
            break
        antwort_id, ergebnis = unpack('!Ii', antwort)
        op, n = offen.pop(antwort_id)
        print(f'Antwort auf Aufgabe {antwort_id}: {op}({n} Zahlen) = {ergebnis}')
except socket.timeout:
    print('Socket timed out at', time.asctime())

sock.close()
