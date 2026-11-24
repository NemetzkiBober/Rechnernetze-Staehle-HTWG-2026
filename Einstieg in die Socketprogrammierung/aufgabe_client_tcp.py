# =====================================================================
# REIHENFOLGE (über alle 4 Dateien), suche nach "Schritt X":
#
# TEIL A: UDP (einfacher, weil 1 Datagramm = 1 Anfrage)
#   1      aufgabe_client_udp.py  baue_anfrage()            -> in Python-Shell testen
#   2      aufgabe_server_udp.py  berechne()                -> in Python-Shell testen
#   3-6    aufgabe_server_udp.py  Anfrage zerlegen, rechnen, Antwort senden
#   7-10   aufgabe_client_udp.py  senden, Antwort empfangen, ausgeben
#          >>> TEST: erst Server, dann Client starten <<<
#   11     aufgabe_client_udp.py  weitere Aufgaben (SUM, PRO, MIN, MAX)
#
# TEIL B: TCP (Byte-Strom -> recv_exact nötig)
#   12     aufgabe_server_tcp.py  berechne() aus UDP-Server übernehmen
#   13     aufgabe_server_tcp.py  recv_exact()              <- der Kern!
#   14-17  aufgabe_server_tcp.py  Kopf/Zahlen lesen, rechnen, senden
#   18     aufgabe_client_tcp.py  recv_exact() übernehmen
#   19-21  aufgabe_client_tcp.py  baue_anfrage() (wie UDP-Client)
#   22-25  aufgabe_client_tcp.py  senden, Antwort lesen, ausgeben
#          >>> TEST: erst Server, dann Client starten <<<
#   26     aufgabe_client_tcp.py  Aufgabe mit großem N (für 3.1 / Wireshark)
#          >>> danach: 3.1 mit Wireshark, ss und telnet <<<
# =====================================================================

import socket
import time
from struct import pack, unpack

Server_IP = '127.0.0.67'
Server_PORT = 50000
MAX_N = 65535          # größtes N (unsigned short); bei TCP kein 64-KB-Limit wie bei UDP
INT_MAX = 2**31 - 1
INT_MIN = -2**31


def recv_exact(sock, n):
    """Liest GENAU n Bytes (wie im Server)."""
    # [Schritt 18] wie im Server, nur ohne print
    data = b''
    while len(data) < n:
        stueck = sock.recv(n - len(data))
        if not stueck:        # Server hat geschlossen
            return None
        data += stueck
    return data


def baue_anfrage(id, op, zahlen):
    """Erzeugt <ID><OP><N><z1>...<zN> als bytes."""
    n = len(zahlen)
    kopf = pack('!I3sH', id, op.encode('utf-8'), n)   # [Schritt 19]
    body = pack(f'!{n}i', *zahlen)                     # [Schritt 20]
    return kopf + body                                 # [Schritt 21]


# Aufgaben: (ID, Operation, Zahlen)
# Mindestens zwei, davon eine mit großem N (z. B. 20000 Zahlen) für 3.1
aufgaben = [
    # Normalfälle
    (1,  'SUM', [1, 2, 3]),              # 6
    # [Schritt 26] 80 000 Bytes -> mehrere TCP-Segmente
    (2,  'MAX', list(range(20000))),     # 19999
    (3,  'PRO', [2, 3, 4]),              # 24
    (4,  'MIN', [5, -3, 8]),             # -3

    # Nur eine Zahl
    (5,  'SUM', [42]),                   # 42
    (6,  'PRO', [-7]),                   # -7

    # Negative Zahlen und Null
    (7,  'SUM', [-1, -2, -3]),           # -6
    (8,  'PRO', [-2, -3, -4]),           # -24
    (9,  'PRO', [5, 0, 1000]),           # 0

    # Grenzen von signed int
    (10, 'MAX', [INT_MIN, INT_MAX]),     # 2147483647
    (11, 'MIN', [INT_MIN, INT_MAX]),     # -2147483648
    (12, 'SUM', [INT_MAX, INT_MIN]),     # -1

    # Grenzen der ID (unsigned int)
    (0,  'SUM', [1]),                    # ID 0 -> 1
    (2**32 - 1, 'SUM', [1]),             # ID 4294967295 -> 1

    # N = 0: SUM geht noch (MIN/MAX würden den Server abstürzen lassen)
    (13, 'SUM', []),                     # 0

    # Mehr als bei UDP erlaubt (16374) – geht nur mit TCP
    (14, 'SUM', [1] * 16375),            # 16375
    (15, 'MAX', list(range(MAX_N))),     # 65534  (größtes N, ~256 KB)
    (16, 'MIN', list(range(MAX_N, 0, -1))),  # 1
]

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(10)
print('Connecting to TCP server with IP', Server_IP, 'on Port', Server_PORT)
sock.connect((Server_IP, Server_PORT))

try:
    for id, op, zahlen in aufgaben:
        # Seriell: senden, auf Antwort warten, dann nächste Aufgabe
        sock.sendall(baue_anfrage(id, op, zahlen))   # [Schritt 22]

        antwort = recv_exact(sock, 8)                # [Schritt 23] Antwort = 8 Bytes
        if antwort is None:
            print('Server hat die Verbindung geschlossen')
            break

        antwort_id, ergebnis = unpack('!Ii', antwort)   # [Schritt 24]
        print(f'Antwort auf Aufgabe {antwort_id}: {op}({len(zahlen)} Zahlen) = {ergebnis}')   # [Schritt 25]
except socket.timeout:
    print('Socket timed out at', time.asctime())

sock.close()
