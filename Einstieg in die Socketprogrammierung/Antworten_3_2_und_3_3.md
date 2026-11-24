# Laboraufgabe Socketprogrammierung – Aufgaben 3.2 und 3.3

Alle Ausgaben unten stammen aus echten Testläufen unter Linux (Python 3.10).
Wo ihr eure eigenen Werte aus dem Test mit zwei Rechnern eintragen müsst, steht **[eintragen]**.

Dazugehörige Dateien:

| Datei | Wofür |
|---|---|
| `experimente_3_2.py` | kleine Experimente zu den Fragen 1–5 aus 3.2 |
| `aufgabe_server_tcp_threads.py` | 3.3: Server mit Threads und Pipelining |
| `aufgabe_client_tcp_pipelining.py` | 3.3: Client, der alle Anfragen mit einem `sendall()` schickt |

Die Dateien aus 3.1 (`aufgabe_*_tcp.py`, `aufgabe_*_udp.py`) bleiben unverändert, damit ihr sie für die Wireshark-Auswertung von 3.1 weiter benutzen könnt.

---

## 3.2 Netzwerk-Kommunikation

### Durchführung (Linux)

1. **Beide Rechner ins gleiche Netz bringen**, entweder per NordVPN-Meshnet (gleicher Account auf beiden Geräten, Meshnet einschalten, „Remote Access“ für das andere Gerät erlauben) oder per WLAN-Hotspot.
2. **IP-Adressen herausfinden:** `ip addr`. Im Meshnet hat die Schnittstelle eine eigene Adresse (bei NordVPN meist `100.x.x.x`), im WLAN die Adresse auf `wlan0`/`wlp…`.
3. **Erreichbarkeit testen:** `ping <IP des anderen Rechners>`.
4. **Firewall auf dem Server-Rechner öffnen**, falls eine aktiv ist (z. B. ufw):
   `sudo ufw allow 50000/tcp` und `sudo ufw allow 50000/udp`.
5. **IP-Adressen in den Skripten anpassen:**
   - Server: `My_IP = '0.0.0.0'` (lauscht auf allen Schnittstellen) oder direkt die Meshnet/WLAN-IP des Server-Rechners.
     Mit `127.0.0.x` geht es **nicht**: Loopback-Adressen sind nur auf dem eigenen Rechner erreichbar.
   - Client: `Server_IP = '<Meshnet/WLAN-IP des Server-Rechners>'`.
6. Erst den Server starten, dann den Client auf dem anderen Rechner. Mit `ss -tanp` (TCP) bzw. `ss -uanp` (UDP) seht ihr auf beiden Seiten den Socket mit den echten Adressen.

| | Rechner A (Server) | Rechner B (Client) |
|---|---|---|
| IP im Meshnet/WLAN | **[eintragen]** | **[eintragen]** |
| Port | 50000 | **[eintragen, vom Betriebssystem vergeben]** |

---

### Frage 1: Wie findet man im Client die eigene IP-Adresse und Port-Nummer heraus?

Mit **`sock.getsockname()`**. Die Methode liefert das Tupel `(IP, Port)` des **lokalen** Endes des Sockets.
Das Gegenstück ist **`sock.getpeername()`**: Es liefert die Adresse der **Gegenseite**, geht also nur bei verbundenen (TCP-)Sockets.

```python
sock.connect((Server_IP, Server_PORT))
print('Lokaler Socket:', sock.getsockname())
print('Server:', sock.getpeername())
```

Ausgabe aus `experimente_3_2.py`:

```
TCP nach connect():  ('127.0.0.1', 36702)
Gegenseite:          ('127.0.0.1', 50001)
Server sieht Client: ('127.0.0.1', 36702)
```

Der Server sieht über `accept()` genau dieselbe Adresse, die der Client mit `getsockname()` ausgibt. Im Pipelining-Client aus 3.3 ist diese Ausgabe schon eingebaut (`Verbunden, lokaler Socket: ...`).

Wichtig: `getsockname()` muss man **nach** `connect()` (TCP) bzw. nach dem ersten `sendto()` (UDP) aufrufen, denn vorher hat der Socket noch keine Adresse (siehe Frage 2).

Alternativ von außen: `ss -tanp` zeigt in der Spalte „Local Address:Port“ dieselben Werte.

---

### Frage 2: Wann (in welcher Code-Zeile) und woher bekommt der Client IP-Adresse und Port?

**Wann:** Beim Client ruft niemand `bind()` auf. Das Betriebssystem bindet den Socket deshalb **automatisch (implizit)**, und zwar bei der ersten Operation, die eine lokale Adresse braucht:

| | Code-Zeile | Datei |
|---|---|---|
| TCP | `sock.connect((Server_IP, Server_PORT))` | `aufgabe_client_tcp.py`, Zeile 95 |
| UDP | `sock.sendto(baue_anfrage(...), (Server_IP, Server_PORT))` | `aufgabe_client_udp.py`, Zeile 100 (erster Durchlauf) |

`socket.socket(...)` erzeugt nur einen „leeren“ Socket, der noch keine Adresse hat. Das sieht man im Experiment:

```
TCP vor connect():   ('0.0.0.0', 0)
TCP nach connect():  ('127.0.0.1', 36702)
UDP vor sendto():    ('0.0.0.0', 0)
UDP nach sendto():   ('0.0.0.0', 38067)
```

`('0.0.0.0', 0)` bedeutet „noch nichts festgelegt“.

**Woher:** Beides vergibt das **Betriebssystem** (der TCP/IP-Stack im Kernel):

- **Port:** Ein freier sogenannter *ephemeral port* (kurzlebiger Port) aus einem festen Bereich. Unter Linux steht der Bereich in `/proc/sys/net/ipv4/ip_local_port_range`, bei uns **32768–60999** (Windows nimmt 49152–65535). Deshalb bekommt der Client bei jedem Start einen anderen Port.
- **IP-Adresse:** Das Betriebssystem schaut in der **Routing-Tabelle** nach, über welche Schnittstelle das Ziel erreicht wird, und nimmt die Adresse dieser Schnittstelle als Absender. Das kann man mit `ip route get <Ziel-IP>` nachvollziehen:
  ```
  $ ip route get 127.0.0.67
  local 127.0.0.67 dev lo src 127.0.0.1
  ```
  Darum hat der Client auch dann die Adresse `127.0.0.1`, wenn er sich mit einem Server auf `127.0.0.67` verbindet. Beim Test mit zwei Rechnern ist es entsprechend die Meshnet- oder WLAN-Adresse, je nachdem, über welche Schnittstelle der Server erreichbar ist.

**Besonderheit UDP:** Nach `sendto()` steht als IP weiterhin `0.0.0.0`, nur der Port ist fest. Ein UDP-Socket ist nicht „verbunden“. Er könnte als Nächstes an ein ganz anderes Ziel über eine andere Schnittstelle senden, deshalb wählt das Betriebssystem die Absender-IP **für jedes Datagramm einzeln**. Bei TCP gehört der Socket fest zu einer Verbindung, deshalb steht die IP nach `connect()` fest.

---

### Frage 3: Wie legt man IP-Adresse und Port im Client selbst fest?

Genau wie beim Server, mit **`bind()`**, aber **vor** `connect()` bzw. `sendto()`:

```python
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind(('127.0.0.1', 54321))      # eigene IP und eigenen Port festlegen
sock.connect((Server_IP, Server_PORT))
```

Ausgabe aus dem Experiment:

```
Client mit bind():   ('127.0.0.1', 54321) | Server sieht: ('127.0.0.1', 54321)
```

Varianten:

- `bind(('', 54321))` oder `bind(('0.0.0.0', 54321))`: nur den Port festlegen, die IP wählt weiter das Betriebssystem.
- `bind(('<IP einer Schnittstelle>', 0))`: nur die IP festlegen (z. B. „über das Meshnet raus“). Port 0 heißt „Betriebssystem, such dir einen aus“.
- Die IP muss eine Adresse sein, die der eigene Rechner tatsächlich hat, sonst kommt `OSError: Cannot assign requested address`.
- Ist der Port schon belegt, kommt `OSError: Address already in use`. Das passiert z. B., wenn man den Client mit festem Port zweimal kurz hintereinander startet und die alte Verbindung noch im Zustand `TIME_WAIT` ist.

Normalerweise legt man beim Client **nichts** fest. Gerade weil das Betriebssystem jedes Mal einen freien Port nimmt, können beliebig viele Clients gleichzeitig laufen.

---

### Frage 4: Warum braucht man Timeouts, wie funktioniert `try … except`, und wie setzt man einen gemeinsamen Timeout für alle Sockets?

**Warum Timeouts?**
Viele Socket-Befehle **blockieren**: Das Programm bleibt in der Zeile stehen, bis etwas passiert.

- `accept()` wartet auf eine Verbindung,
- `recv()` / `recvfrom()` warten auf Daten,
- `connect()` wartet auf die Antwort des Servers (SYN-ACK).

Ohne Timeout warten diese Befehle **unbegrenzt**. Das ist ein Problem, wenn das Erwartete nie kommt:

- **UDP:** Geht ein Datagramm (Anfrage oder Antwort) verloren oder läuft der Server gar nicht, kommt einfach nichts an. UDP meldet das nicht. Der Client würde in `recvfrom()` für immer hängen.
- **Server:** Ein Client verbindet sich und schickt nichts mehr (wie bei telnet in 3.1). Ohne Timeout würde der Server ewig in `recv()` warten und die Verbindung nie schließen. Unsere Aufgabe verlangt aber ausdrücklich, dass er nach 10 s schließt.
- **Server beenden:** Ein Server, der in `accept()` blockiert, kommt nie dazu, eine Abbruchbedingung zu prüfen (z. B. die Laufzeit `server_activity_period` im Echo-Server oder das Stop-Flag in 3.3). Unter Windows lässt sich ein blockierendes `accept()` nicht einmal mit Strg+C unterbrechen.
- **Netzwerkfehler:** Ist der andere Rechner plötzlich weg (WLAN aus), merkt TCP das unter Umständen erst sehr spät.

Mit `sock.settimeout(10)` wartet jeder blockierende Befehl auf diesem Socket höchstens 10 s. Danach wirft er die Ausnahme `socket.timeout`. Das Programm kann dann reagieren (Verbindung schließen, Anfrage wiederholen, Schleifenbedingung prüfen …).
`settimeout(None)` heißt „blockierend, ohne Limit“ (Standard), `settimeout(0)` heißt „nicht blockierend“.

**Wie funktioniert `try … except`?**

```python
try:
    data, addr = sock.recvfrom(1024)     # (1) kann eine Ausnahme werfen
    print('Antwort:', data)              # (2) wird übersprungen, wenn (1) scheitert
except socket.timeout:
    print('Keine Antwort nach 10 s')     # (3) nur bei Timeout
# (4) hier geht es in jedem Fall weiter
```

- Python führt den `try`-Block normal aus.
- Wirft eine Zeile darin eine Ausnahme (z. B. `socket.timeout`), wird der Rest des `try`-Blocks **übersprungen**. Python sucht dann ein passendes `except`.
- Passt der Typ, läuft dieser `except`-Block, danach geht das Programm **nach** dem gesamten `try`-Konstrukt normal weiter. Es stürzt also nicht ab.
- Passt kein `except`, wird die Ausnahme nach oben weitergereicht. Fängt sie niemand, bricht das Programm mit Fehlermeldung (Traceback) ab. Genau das passiert in euren `problem_aufgaben` mit `struct.error` im Server.
- Optional gibt es `else:` (läuft, wenn keine Ausnahme kam) und `finally:` (läuft **immer**, gut zum Aufräumen, z. B. `conn.close()`; so ist es im Thread-Server in 3.3 gemacht).
- Ausnahmen sind Klassen und haben eine Vererbungshierarchie: `except OSError` fängt auch `socket.timeout`, `ConnectionResetError` usw. Seit Python 3.10 ist `socket.timeout` nur noch ein anderer Name für das eingebaute `TimeoutError`.

**Gemeinsamer Timeout für alle Sockets:**

```python
socket.setdefaulttimeout(10)
```

Das setzt den Standard-Timeout für **alle danach neu erzeugten** Sockets. Bereits existierende Sockets ändert der Befehl nicht. Auch die Sockets, die `accept()` zurückgibt, bekommen diesen Timeout (im Test: `accept-socket timeout: 3.0` nach `setdefaulttimeout(3)`).
Ausgabe aus dem Experiment (mit 2 s):

```
Timeout des neuen Sockets: 2.0
socket.timeout nach 2.0 s
```

---

### Frage 5: Kann ein Server auf demselben Port über UDP **und** TCP antworten?

**Ja.** Experiment (`experimente_3_2.py`, Teil 5): Ein TCP-Socket und ein UDP-Socket werden beide an `127.0.0.1:50002` gebunden, und beide empfangen ihre Daten:

```
TCP und UDP beide auf Port 50002 gebunden
UDP-Socket empfängt: b'per UDP'
TCP-Socket empfängt: b'per TCP'
Zweiter TCP-Socket: [Errno 98] Address already in use
```

Ihr könnt es auch mit euren eigenen Servern zeigen: In `aufgabe_server_udp.py` und `aufgabe_server_tcp.py` dieselbe `My_IP` eintragen (z. B. `127.0.0.1`), beide gleichzeitig starten und mit `ss -tulpn | grep 50000` nachsehen. Dort tauchen zwei Zeilen auf, eine `tcp LISTEN` und eine `udp UNCONN`, beide mit Port 50000.

**Warum geht das?**
TCP und UDP haben **getrennte Port-Bereiche**. Ein Socket ist nicht nur durch (IP, Port) bestimmt, sondern durch **(Protokoll, IP, Port)**.
Wenn ein Paket ankommt, schaut das Betriebssystem zuerst ins **Protokoll-Feld des IP-Headers** (6 = TCP, 17 = UDP) und gibt das Paket an den TCP- oder den UDP-Teil des Stacks weiter. Erst dort wird anhand des Ziel-Ports der passende Socket gesucht. TCP-Port 50000 und UDP-Port 50000 kommen sich also nie in die Quere.
Die Gegenprobe zeigt: Zwei Sockets mit **demselben** Protokoll auf demselben Port gehen nicht („Address already in use“).

Praxisbeispiel: DNS läuft auf Port 53 sowohl über UDP (normale Anfragen) als auch über TCP (große Antworten, Zonentransfers).

---

## 3.3 Mehrere Clients und Pipelining

### Aufbau des Servers (`aufgabe_server_tcp_threads.py`)

```
Haupt-Thread:   listen(sock) ── accept() ──┬── Thread: receive(conn1)  ← Client 1
                     ↑   (Schleife)        ├── Thread: receive(conn2)  ← Client 2
                     └─────────────────────┴── ...
```

**`listen(sock)`** läuft im Haupt-Thread. Die Funktion wartet in einer Schleife mit `accept()` auf neue Verbindungen. Für jede neue Verbindung startet sie mit

```python
threading.Thread(target=receive, args=(conn, addr)).start()
```

einen eigenen Thread und geht **sofort** zurück zu `accept()`. Darum kann der nächste Client schon angenommen werden, während der erste noch bedient wird.

**`receive(conn, addr)`** läuft einmal pro Client in einem eigenen Thread. Sie liest Anfragen, rechnet und antwortet, bis der Client schließt oder 10 s lang nichts kommt (`conn.settimeout(10)`). Zusätzlich zu `conn` bekommt sie `addr`, aber nur, damit die Ausgaben zeigen, zu welchem Client eine Zeile gehört.

**Warum Threads?** Im seriellen Server aus 3.1 blockiert `recv()` den **ganzen** Server. Solange er auf Client 1 wartet, kann er niemand anderen annehmen. Mit Threads blockiert `recv()` nur den Thread dieses einen Clients.

Test: Client A verbindet sich und schweigt. Gleichzeitig verbindet sich Client B und bekommt sofort alle Antworten:

```
Client B fertig nach 0.02 s, während A noch verbunden ist:
...
Neue Verbindung: ('127.0.0.1', 60852)        ← A
Neue Verbindung: ('127.0.0.1', 60858)        ← B
('127.0.0.1', 60858) Anfrage 1: SUM (N = 3) = 6
...
('127.0.0.1', 60852) keine Anfrage seit 10 s -> schließe
```

Mit dem seriellen Server hätte B 10 s warten müssen, bis A rausfliegt.

### Pipelining und warum der Server einen Puffer braucht

Der Client (`aufgabe_client_tcp_pipelining.py`) hängt alle fünf Anfragen aneinander und schickt sie mit **einem** `sendall()`:

```python
alle = b''.join(baue_anfrage(id, op, zahlen) for id, op, zahlen in aufgaben)
sock.sendall(alle)
```

Erst danach liest er die fünf Antworten (je 8 Bytes) und ordnet sie über die **ID** zu (Dictionary `offen`).

TCP ist ein **Byte-Strom ohne Nachrichtengrenzen**. Beim Server kommen also keine fünf „Pakete“ an, sondern einfach 80 093 Bytes am Stück, aufgeteilt so, wie es gerade passt. Ein echter Testlauf:

```
recv lieferte 65482 Bytes
  Anfrage 1: SUM (N = 3) = 6
  Anfrage 2: PRO (N = 3) = 24
recv lieferte 14611 Bytes
  Anfrage 3: MAX (N = 20000) = 19999
  Anfrage 4: MIN (N = 3) = -3
  Anfrage 5: SUM (N = 3) = -6
```

Nachgerechnet (Anfrage = 9 Bytes Kopf + 4·N Bytes Zahlen):

| Anfrage | Größe |
|---|---|
| 1 (N = 3) | 21 Bytes |
| 2 (N = 3) | 21 Bytes |
| 3 (N = 20000) | 80 009 Bytes |
| 4 (N = 3) | 21 Bytes |
| 5 (N = 3) | 21 Bytes |
| **Summe** | **80 093 Bytes** |

- 1. `recv`: 65 482 = 21 + 21 + **65 440** → Anfrage 1 und 2 komplett, dazu der **Anfang** von Anfrage 3
- 2. `recv`: 14 611 = **14 569** + 21 + 21 → der **Rest** von Anfrage 3, dazu Anfrage 4 und 5 komplett

Genau das meint der Hinweis in der Aufgabe: Ein `recv()` enthält das Ende einer Anfrage und den Anfang der nächsten. In anderen Läufen war die Aufteilung anders (z. B. 32 741 + 47 352 oder 65 536 + 14 557). Wie die Bytes auf die `recv()`-Aufrufe verteilt werden, hängt vom Zufall ab (Timing, Puffer), nicht vom Protokoll.

Der Server löst das mit einem **Puffer**:

```python
puffer += conn.recv(65536)            # alles anhängen, was gerade da ist

while len(puffer) >= HEADER_LEN:      # mindestens ein Kopf da?
    id, op, n = unpack(HEADER_FORMAT, puffer[:HEADER_LEN])
    ende = HEADER_LEN + 4 * n         # erst der Kopf verrät, wie lang die Anfrage ist
    if len(puffer) < ende:
        break                         # unvollständig -> erst weiter empfangen
    zahlen = unpack(f'!{n}i', puffer[HEADER_LEN:ende])
    puffer = puffer[ende:]            # Rest aufheben: gehört zur nächsten Anfrage
    ... rechnen, antworten ...
```

1. Alles Empfangene kommt hinten an den Puffer.
2. Solange vorne im Puffer eine **vollständige** Anfrage steht, wird sie herausgeschnitten und bearbeitet. Ob sie vollständig ist, verrät N im Kopf.
3. Was übrig bleibt, ist der Anfang der nächsten Anfrage und **bleibt im Puffer**, bis beim nächsten `recv()` der Rest kommt.

Die Anfragen werden so in der Reihenfolge ihres Eintreffens bearbeitet, und zu jeder geht eine Antwort raus.

**Alternative:** Das `recv_exact()` aus 3.1 würde auch funktionieren. Es fordert mit `recv(n - len(data))` nie mehr an, als zur aktuellen Anfrage gehört, also bleiben die Bytes der nächsten Anfrage im Empfangspuffer des Betriebssystems liegen. Die Puffer-Variante zeigt aber deutlicher, was der Hinweis meint, und braucht weniger `recv()`-Aufrufe.

### Timeout, Stop-Flag und Fehler

- **10-s-Timeout:** wie in 3.1 mit `conn.settimeout(10)`, jetzt pro Thread. Kommt 10 s nichts, schließt dieser Thread seine Verbindung. Die anderen laufen weiter.
- **Server beenden:** Mit Strg+C (`KeyboardInterrupt`) setzt der Haupt-Thread das globale Flag `stop = True`. Die Threads lassen sich nicht „von außen abschießen“. Sie prüfen das Flag selbst, jeweils wenn ein blockierender Befehl zurückkommt. Deshalb haben alle blockierenden Befehle Timeouts: `accept()` 1 s (damit `listen` das Flag oft prüft), `recv()` 10 s. Im Test hat ein schweigender Client den Server nach Strg+C noch 9 s am Leben gehalten, bis sein `recv()`-Timeout ablief. Das ist genau die erwartete Obergrenze von 10 s.
- **Fehler pro Client:** Eine unbekannte Operation oder ein Überlauf wirft im Thread eine Ausnahme. `except Exception` gibt sie aus, `finally` schließt die Verbindung, und **nur dieser Client** fliegt raus. Der Server und die anderen Clients laufen weiter:
  ```
  ('127.0.0.1', 52186) Anfrage 99: XYZ (N = 1) = None
  ('127.0.0.1', 52186) Fehler: TypeError(...)
  Neue Verbindung: ('127.0.0.1', 52196)       ← nächster Client wird normal bedient
  ```
- **`SO_REUSEADDR`:** Damit kann man den Server direkt nach dem Beenden neu starten, auch wenn alte Verbindungen noch im Zustand `TIME_WAIT` sind (sonst „Address already in use“).

### Testen

```bash
# Fenster 1
python3 aufgabe_server_tcp_threads.py
# Fenster 2 und 3 (gleichzeitig, oder mehrmals schnell hintereinander)
python3 aufgabe_client_tcp_pipelining.py
# optional: ein "schweigender" Client
telnet 127.0.0.1 50000
```

In Wireshark auf `lo` sieht man beim Pipelining: Der Client schickt alle Daten-Segmente hintereinander, ohne zwischendurch auf eine Antwort zu warten. Erst danach kommen die 8-Byte-Antworten des Servers, teils auch in einem gemeinsamen Segment. Mit `ss -tanp` sieht man auf dem Server **einen** LISTEN-Socket und pro Client **einen** ESTABLISHED-Socket, alle auf Port 50000. Die Verbindungen unterscheiden sich nur durch IP und Port des Clients.

Für den Test mit zwei Rechnern (3.2) in beiden 3.3-Dateien die IPs wie oben beschrieben anpassen.
