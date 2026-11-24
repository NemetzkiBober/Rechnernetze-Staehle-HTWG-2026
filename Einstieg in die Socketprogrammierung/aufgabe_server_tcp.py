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
import numpy as np
from struct import pack, unpack

My_IP = '127.0.0.67'
My_PORT = 50000
TIMEOUT = 10            # Server schließt Verbindung nach 10 s ohne Anfrage
HEADER_FORMAT = '!I3sH' # ID (4 B), Rechenoperation (3 B), N (2 B) = 9 Bytes
HEADER_LEN = 9
ANTWORT_FORMAT = '!Ii'  # ID (4 B), Ergebnis (4 B) = 8 Bytes


def recv_exact(conn, n):
    """Liest GENAU n Bytes aus conn (recv kann weniger liefern!).
    Gibt None zurück, wenn die Gegenseite die Verbindung geschlossen hat."""
    # [Schritt 13]
    # TCP ist ein Byte-Strom: recv() gibt nur das, was gerade da ist.
    # Also so lange lesen, bis alles beisammen ist.
    data = b''
    while len(data) < n:
        stueck = conn.recv(n - len(data))   # nur anfordern, was noch fehlt
        if not stueck:                      # b'' = Gegenseite hat geschlossen
            return None
        print('  recv lieferte', len(stueck), 'Bytes')   # für 3.1
        data += stueck
    return data   # bei n == 0 einfach b''


# [Schritt 12] wie im UDP-Server.
# Unbekannte op -> gibt None zurück -> pack() unten schlägt fehl.
def berechne(op, zahlen):
    if op == "SUM":
        return np.sum(zahlen)
    elif op == "PRO":
        return np.prod(zahlen)
    elif op == "MIN":
        return np.min(zahlen)
    elif op == "MAX":
        return np.max(zahlen)
    pass


# --- Listening-Socket anlegen ---
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((My_IP, My_PORT))
sock.listen(1)
print('Listening on Port', My_PORT, 'for incoming TCP connections')

# --- Verbindung annehmen -> neuer Connected-Socket conn ---
conn, addr = sock.accept()
print('Incoming connection accepted:', addr)
conn.settimeout(TIMEOUT)   # gilt für jedes einzelne recv() auf conn

# --- Anfragen bearbeiten, bis Timeout oder Gegenseite schließt ---
while True:
    try:
        # 1. Kopf lesen (9 Bytes) – hier wartet der Server auf die nächste Anfrage
        kopf = recv_exact(conn, HEADER_LEN)
        if kopf is None:
            print('Connection closed from other side')
            break

        # [Schritt 14] erst jetzt kennen wir N
        id, op, n = unpack(HEADER_FORMAT, kopf)
        op = op.decode('utf-8')   # b'SUM' -> 'SUM'
        print(f'Anfrage {id}: {op}, N = {n}')

        # 2. Zahlen lesen (4 * n Bytes) und entpacken
        # [Schritt 15] "is None" statt "not body": bei N = 0 ist body == b''
        body = recv_exact(conn, 4 * n)
        if body is None:
            print('Connection closed in the middle of a request')
            break
        zahlen = unpack(f'!{n}i', body)

        # 3. Rechnen
        # [Schritt 16]
        ergebnis = berechne(op, zahlen)
        print(f'Anfrage {id}: Ergebnis = {ergebnis}')

        # 4. Antwort <ID><Ergebnis> senden
        # [Schritt 17] int(): numpy-Zahl -> Python-int (np.sum(()) ist sogar 0.0)
        # sendall statt send: send darf auch nur einen Teil verschicken.
        conn.sendall(pack(ANTWORT_FORMAT, id, int(ergebnis)))

    except socket.timeout:
        # 10 s kein recv() fertig -> Verbindung zu (Server schickt das FIN)
        print('No request for', TIMEOUT, 's -> closing connection at', time.asctime())
        break

conn.close()
sock.close()
