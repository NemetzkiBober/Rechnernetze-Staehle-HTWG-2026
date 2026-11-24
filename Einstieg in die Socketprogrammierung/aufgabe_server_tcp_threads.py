# Aufgabe 3.3: TCP-Rechen-Server mit Threads (mehrere Clients) und Pipelining
#
#   listen(sock)   nimmt Verbindungen an, startet pro Client einen Thread
#   receive(conn)  liest Anfragen, rechnet, antwortet (ein Thread pro Client)
#
# Beenden mit Strg+C.

import socket
import threading
import numpy as np
from struct import pack, unpack

My_IP = '127.0.0.1'     # für 3.2 (zwei Rechner): '0.0.0.0' = alle Netzwerkkarten
My_PORT = 50000
TIMEOUT = 10            # Verbindung zu nach 10 s ohne Anfrage
HEADER_FORMAT = '!I3sH' # ID, Rechenoperation, N = 9 Bytes
HEADER_LEN = 9

stop = False            # globales Stop-Flag für alle Threads


def berechne(op, zahlen):
    if op == "SUM":
        return np.sum(zahlen)
    elif op == "PRO":
        return np.prod(zahlen)
    elif op == "MIN":
        return np.min(zahlen)
    elif op == "MAX":
        return np.max(zahlen)


def receive(conn, addr):
    conn.settimeout(TIMEOUT)
    puffer = b''        # empfangene, noch nicht bearbeitete Bytes
    try:
        while not stop:
            try:
                stueck = conn.recv(65536)   # nimmt, was da ist – evtl. mehrere Anfragen
            except socket.timeout:
                print(addr, 'keine Anfrage seit', TIMEOUT, 's -> schließe')
                break
            if not stueck:
                print(addr, 'Client hat geschlossen')
                break
            print(addr, 'recv lieferte', len(stueck), 'Bytes')
            puffer += stueck

            # Alle vollständigen Anfragen aus dem Puffer abarbeiten
            while len(puffer) >= HEADER_LEN:
                id, op, n = unpack(HEADER_FORMAT, puffer[:HEADER_LEN])
                ende = HEADER_LEN + 4 * n
                if len(puffer) < ende:
                    break                    # Anfrage noch unvollständig -> weiter lesen

                zahlen = unpack(f'!{n}i', puffer[HEADER_LEN:ende])
                puffer = puffer[ende:]       # Rest gehört schon zur nächsten Anfrage

                ergebnis = berechne(op.decode('utf-8'), zahlen)
                print(addr, f'Anfrage {id}: {op.decode()} (N = {n}) = {ergebnis}')
                conn.sendall(pack('!Ii', id, int(ergebnis)))
    except Exception as e:
        # z. B. unbekannte Operation oder Überlauf: nur dieser Client fliegt raus
        print(addr, 'Fehler:', repr(e))
    finally:
        conn.close()


def listen(sock):
    sock.settimeout(1)  # damit accept() regelmäßig das Stop-Flag prüfen kann
    while not stop:
        try:
            conn, addr = sock.accept()
        except socket.timeout:
            continue
        print('Neue Verbindung:', addr)
        threading.Thread(target=receive, args=(conn, addr)).start()


sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)   # sofort neu startbar
sock.bind((My_IP, My_PORT))
sock.listen()
print('Listening on', My_IP, 'Port', My_PORT)

try:
    listen(sock)
except KeyboardInterrupt:
    print('Strg+C -> Server stoppt (laufende Threads enden spätestens nach', TIMEOUT, 's)')
    stop = True
sock.close()
