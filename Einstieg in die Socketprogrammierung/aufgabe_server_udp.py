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
import numpy as np
import socket
import time
import math
from struct import pack, unpack

My_IP = '127.0.0.69'
My_PORT = 50000
server_activity_period = 30   # wie lange der Server insgesamt läuft

HEADER_FORMAT = '!I3sH'       # 9 Bytes
ZAHLEN_FORMAT = '!{}i'

def berechne(op, zahlen):
    # TODO [Schritt 2]: je nach op ('SUM', 'PRO', 'MIN', 'MAX') das Ergebnis
    #   berechnen und zurückgeben (Tipp: sum, min, max, math.prod)
    if op == "SUM":
        return np.sum(zahlen)
    elif op == "PRO":
        return np.prod(zahlen)
    elif op == "MIN":
        return np.min(zahlen)
    elif op == "MAX":
        return np.max(zahlen)
        
    pass


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((My_IP, My_PORT))
sock.settimeout(10)
print('UDP server listening on Port', My_PORT)

t_end = time.time() + server_activity_period

while time.time() < t_end:
    try:
        # Ein Datagramm = genau eine Anfrage -> Puffer groß genug wählen!
        data, addr = sock.recvfrom(65535)
        print('received', len(data), 'bytes from', addr)

        # TODO [Schritt 3]: Kopf = data[:9] entpacken -> id, op, n
        kopf = data[:9]
        id, op, n = unpack(HEADER_FORMAT, kopf)
        op = op.decode('utf-8')
        # TODO [Schritt 4]: Zahlen = data[9:9 + 4*n] entpacken
        zahlen = unpack(ZAHLEN_FORMAT.format(n), data[9:9+4*n])
        
        # TODO [Schritt 5]: ergebnis = berechne(...)
        ergebnis = berechne(op, zahlen)
        # TODO [Schritt 6]: sock.sendto(pack('!Ii', ...), addr)
        sock.sendto(pack('!Ii', id, ergebnis), addr)

    except socket.timeout:
        print('Socket timed out at', time.asctime())

sock.close()
