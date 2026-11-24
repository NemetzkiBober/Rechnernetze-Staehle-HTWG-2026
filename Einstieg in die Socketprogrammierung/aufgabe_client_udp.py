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

Server_IP = '127.0.0.69'
Server_PORT = 50000
MAX_N = 16374        
INT_MAX = 2**31 - 1        
INT_MIN = -2**31

def baue_anfrage(id, op, zahlen):
    n = len(zahlen)
    kopf = pack('!I3sH', id, op.encode('utf-8'), n)   
    body = pack(f'!{n}i', *zahlen)                     
    return kopf + body
    pass


aufgaben = [
    # Normalfälle
    (1,  'SUM', [1, 2, 3]),              # 6
    (2,  'PRO', [2, 3, 4]),              # 24
    (3,  'MIN', [5, -3, 8]),             # -3
    (4,  'MAX', [5, -3, 8]),             # 8

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

    # Viele Zahlen
    (13, 'SUM', list(range(1000))),      # 499500
    (14, 'MAX', list(range(MAX_N))),     # 16373  (genau die UDP-Grenze)
    (15, 'SUM', [1] * MAX_N),            # 16374
]

problem_aufgaben = [
    # Ergebnis passt nicht in 4 Bytes -> struct.error beim pack im SERVER
    (20, 'SUM', [INT_MAX, 1]),           # wäre 2147483648
    (21, 'PRO', [100000, 100000]),       # wäre 10_000_000_000

    # N = 0
    (22, 'SUM', []),                     # sum(()) = 0, geht noch
    (23, 'MIN', []),                     # min(()) -> ValueError im SERVER

    # Unbekannte Operation -> berechne gibt None zurück -> pack scheitert
    (24, 'XYZ', [1, 2]),
    (25, 'sum', [1, 2]),                 # Kleinschreibung

    # Falsche Länge der Operation (achte genau darauf, was ankommt!)
    (26, 'SUMM', [1, 2]),                # '3s' schneidet still ab -> kommt als 'SUM' an!
    (27, 'SU',   [1, 2]),                # wird mit \x00 aufgefüllt -> b'SU\x00'

    # Fehler schon im CLIENT
    (28, 'SUM', [2**31]),                # Zahl zu groß für 'i' -> struct.error
    (29, 'SUM', [1] * (MAX_N + 1)),      # 65509 Bytes > 65507 -> OSError: Message too long
]

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(10)

for id, op, zahlen in problem_aufgaben:
    try:
        sock.sendto(baue_anfrage(id, op, zahlen), (Server_IP, Server_PORT))
        data, addr = sock.recvfrom(1024)
        antwort_id, ergebnis = unpack('!Ii', data)
        print(f'Antwort auf Aufgabe {antwort_id}: {op}({len(zahlen)} Zahlen) = {ergebnis}')
        pass
    except socket.timeout:
        print('Socket timed out at', time.asctime())

sock.close()
