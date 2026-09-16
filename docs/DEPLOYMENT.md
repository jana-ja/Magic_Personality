# Deployment

Task 1.12 (`docs/ROADMAP.md`), ARCHITECTURE.md §11. Bringt v0.1 auf den kleinen eigenen Server (NFR-10). Ziel dieser Datei: einmal von Grund auf durchgespielt, nicht nur am Schreibtisch entworfen — der genaue Wortlaut der Befehle ist mit `docker compose -f compose.yaml -f compose.prod.yaml` lokal geprüft (D-50/D-52 in `docs/DECISIONS.md`), das echte Zusammenspiel mit DNS, Firewall und Let's-Encrypt-ACME lässt sich nur auf dem echten Server verifizieren.

## Voraussetzungen

- Docker und Docker Compose v2 (`docker compose version`, nicht das alte `docker-compose`) auf dem Server.
- Eine Domain, deren A/AAAA-Eintrag auf die IP des Servers zeigt — Caddy braucht das für die automatische TLS-Ausstellung (Let's Encrypt HTTP-01-Challenge über Port 80).
- Port 80 und 443 (TCP **und** UDP für HTTP/3) extern erreichbar — sonst schlägt die Zertifikatsausstellung fehl bzw. bricht die Verbindung ab.
- Das GHCR-Image `ghcr.io/jana-ja/magic_personality` ist aktuell **privat** (per `docker pull` ohne Login geprüft: `unauthorized`) — auf dem Server vor dem ersten `pull` einmalig `docker login ghcr.io` mit einem Personal Access Token (Scope `read:packages`) ausführen. Wer stattdessen lieber ohne Token auskommen möchte, kann das Package auf GitHub unter Package-Einstellungen auf öffentlich stellen (unproblematisch, solange kein Quellcode oder Secret im Image landet — beides ist hier nicht der Fall, `.env` wird zur Laufzeit gemountet, nicht eingebacken).

## Einmalige Einrichtung

1. Verzeichnis auf dem Server anlegen, z. B. `/opt/magic_personality`.
2. Genau drei Dateien aus dem Repository dorthin bringen — kein vollständiger Checkout nötig, das *Image* kommt fertig gebaut aus der Registry, ein `Dockerfile` oder Quellcode braucht der Server nie:
   - `compose.yaml`
   - `compose.prod.yaml`
   - `Caddyfile`

   **Nicht** `compose.override.yaml` — die ist nur für lokale Entwicklung gedacht (D-50) und würde Host-Ports öffnen, die in Produktion bewusst geschlossen bleiben.

   Empfohlener Weg, weil diese drei Dateien sich künftig auch mal ändern (neuer Healthcheck, andere Caddy-Direktive, …) und dann erneut auf den Server müssen: ein **Sparse Checkout** statt Einzeldateien per Hand zu kopieren — danach reicht `git pull`, um sie zu aktualisieren, ohne den Rest des Repos (App-Code, Tests, `docs/`) mitzuschleppen. `git sparse-checkout set` erwartet im Standard-Modus ("Cone Mode") **Verzeichnisse**, keine einzelnen Dateien — alle drei Dateien liegen aber im Repository-Wurzelverzeichnis. `--no-cone` schaltet auf den älteren, musterbasierten Modus um, der einzelne Pfade akzeptiert (führendes `/` verankert den Pfad an der Repo-Wurzel, sonst würde z. B. `Caddyfile` auch gleichnamige Dateien in Unterordnern mitnehmen):

   ```bash
   git clone --filter=blob:none --sparse https://github.com/jana-ja/Magic_Personality.git .
   git sparse-checkout set --no-cone /compose.yaml /compose.prod.yaml /Caddyfile
   ```

   Alternative ohne Git, für einzelne, seltene Aktualisierungen: die Rohdatei direkt von GitHub laden (`https://raw.githubusercontent.com/jana-ja/Magic_Personality/main/<datei>`), z. B. `curl -O https://raw.githubusercontent.com/jana-ja/Magic_Personality/main/Caddyfile`.
3. `.env` im selben Verzeichnis anlegen (niemals ins Repository commiten):

   ```bash
   # Zufälligen SECRET_KEY erzeugen:
   python3 -c "import secrets; print(secrets.token_urlsafe(50))"
   ```

   ```env
   SECRET_KEY=<generierter Wert>
   ALLOWED_HOSTS=<domain>
   INVITE_CODE=<frei gewählt, mit dem kleinen Nutzerkreis geteilt>

   POSTGRES_USER=magic_personality
   POSTGRES_PASSWORD=<eigenes, langes Passwort>
   POSTGRES_DB=magic_personality

   DOMAIN=<domain>
   ACME_EMAIL=<kontaktadresse für Let's-Encrypt-Ablaufhinweise>
   ```

   `DATABASE_URL` und `SECURE_SSL_REDIRECT` müssen hier **nicht** stehen — `compose.yaml` setzt `DATABASE_URL` selbst auf den internen Compose-Hostnamen `db`, und `SECURE_SSL_REDIRECT` hat in `config/settings/prod.py` bereits den passenden Default `True` (D-52).

## Erstes Deployment

Alle Befehle im Verzeichnis aus dem vorigen Schritt, mit beiden Compose-Dateien:

```bash
docker compose -f compose.yaml -f compose.prod.yaml pull
docker compose -f compose.yaml -f compose.prod.yaml run --rm web python manage.py migrate
docker compose -f compose.yaml -f compose.prod.yaml run --rm web python manage.py seed_content --locale en
docker compose -f compose.yaml -f compose.prod.yaml up -d
```

Migrations laufen bewusst als **eigener** Schritt vor `up -d`, nicht beim Containerstart (D-29) — sonst migrieren mehrere Worker gleichzeitig, und ein Fehlschlag zeigt sich erst im Log statt im Deployment selbst.

`seed_content` ist ein **eigener** Schritt, keine Migration (ARCHITECTURE.md §9/§1.1): Die Migrationen legen nur die leeren Strukturzeilen an (fünf Farben, 31 Kombinationen — "bewusst noch ohne Inhalt", `apps/colors/migrations/0002_seed_colors_and_combinations.py`), Namen, Ziel/Mittel, Eigenschaften, Perspektiven und Themes kommen erst mit diesem Befehl aus `seeds/colors_en.json`. Ohne ihn läuft die Seite scheinbar normal (Fünfeck mit den fünf Farbnamen, Struktur, Navigation — die kommen aus den Migrationen), zeigt aber zu jeder Auswahl nur leere Inhalte. Idempotent (D-Entscheidung, ARCHITECTURE.md §9), also gefahrlos bei jedem Deployment erneut ausführbar.

Danach prüfen:

```bash
docker compose -f compose.yaml -f compose.prod.yaml ps          # alle drei "healthy"/"running"
docker compose -f compose.yaml -f compose.prod.yaml logs caddy  # Zertifikat ausgestellt? Fehler beim ACME-Challenge?
curl -I https://<domain>/healthz                                 # 200, ohne Zugangssperre erreichbar
curl -I https://<domain>/                                        # 302 auf /gate/ — alles andere ist gesperrt
```

`web` und `db` veröffentlichen in Produktion bewusst keinen Host-Port (D-50) — sie sind ausschließlich über Caddy erreichbar, nicht direkt per `<server-ip>:8000` oder `:5432`.

## Folge-Deployments

Bei jedem neuen Stand auf `main` (CI baut und veröffentlicht automatisch, D-31):

```bash
docker compose -f compose.yaml -f compose.prod.yaml pull
docker compose -f compose.yaml -f compose.prod.yaml run --rm web python manage.py migrate
docker compose -f compose.yaml -f compose.prod.yaml run --rm web python manage.py seed_content --locale en
docker compose -f compose.yaml -f compose.prod.yaml up -d
```

Dieselben drei Zeilen wie beim ersten Deployment — `up -d` erneuert nur Container, deren Image sich geändert hat, `db` bleibt unangetastet.

**Ändert sich `compose.yaml`, `compose.prod.yaml` oder `Caddyfile` selbst** (nicht nur der Anwendungscode): Diese drei Dateien liegen nicht im Image, sondern direkt auf dem Server (siehe "Einmalige Einrichtung") — ein `git pull` (bei Sparse Checkout) bzw. erneutes Herunterladen der geänderten Datei *vor* den drei Befehlen oben bringt sie auf den aktuellen Stand. `docker compose ... pull` holt ausschließlich das Anwendungs-Image, nie diese Konfigurationsdateien.

**Rollback auf einen älteren Stand:** `IMAGE_TAG=<sha-tag>` in der Server-`.env` setzen (die von CI veröffentlichten Tags stehen im Build-Job in GitHub Actions bzw. unter den Package-Versionen auf GitHub), dann dieselben drei Schritte — `compose.prod.yaml` liest `IMAGE_TAG` selbst, keine Datei muss dafür bearbeitet werden. Zurück auf den neuesten Stand: `IMAGE_TAG` wieder aus der `.env` entfernen (Default ist `latest`).

## CI/CD — warum kein automatischer Deploy

`.github/workflows/ci.yml` baut und veröffentlicht bei jedem Push auf `main` automatisch ein neues Image (D-31) — das ist **Continuous Delivery**: ein deploybares Artefakt entsteht ohne Zutun. Der letzte Schritt, dieses Artefakt tatsächlich auf dem Server laufen zu lassen (**Continuous Deployment**), bleibt hier bewusst ein manueller Aufruf der drei Befehle oben, kein Auto-Trigger.

Der Grund ist nicht Bequemlichkeit, sondern D-29: Migrations müssen *vor* dem Neustart von `web` laufen, als eigener, beobachtbarer Schritt. Ein rein image-beobachtender Auto-Updater (das verbreitetste Muster dafür heißt "Watchtower" — ein Container, der neue Digests erkennt und automatisch neu startet) kennt diesen Zwischenschritt nicht: Er würde `web` einfach mit dem neuen Image neu starten, sobald es in der Registry auftaucht — bei einer Migration, die neue Spalten oder Tabellen braucht, liefe die neue Codeversion dann gegen ein noch altes Schema. Für 3–10 Nutzende ist der manuelle Trigger (oder später ein eigenes kleines Deploy-Skript, das die drei Zeilen einfach nacheinander ausführt) kein nennenswerter Mehraufwand — ein "richtiges" CD mit automatischem Trigger würde stattdessen entweder den Migrationsschritt mit eingebaut bekommen (ein Skript, das CI selbst per SSH auf dem Server ausführt) oder bräuchte eine Möglichkeit, "Image da, aber noch nicht anwenden" von "jetzt anwenden" zu trennen — beides zusätzliche Komplexität, die diese Größenordnung (noch) nicht rechtfertigt.

## Nach den ersten Tagen: HSTS anheben

`SECURE_HSTS_SECONDS` steht bewusst konservativ auf einer Stunde (D-52) — ein Fehler im frischen TLS-Aufbau soll sich nicht für ein ganzes Jahr im Browser-Cache festsetzen. Sobald HTTPS ein paar Tage zuverlässig lief:

```env
SECURE_HSTS_SECONDS=31536000
```

in der Server-`.env`, dann `docker compose -f compose.yaml -f compose.prod.yaml up -d web` (nur `web` neu starten, `db`/`caddy` bleiben unberührt).

## Fehlerbehebung

**Seite lädt, Fünfeck und Navigation sind da, aber jede Auswahl zeigt leere Inhalte:** `seed_content` wurde vergessen (siehe "Erstes Deployment" oben) — die Migrationen legen nur leere Zeilen an, den eigentlichen Content bringt erst `docker compose -f compose.yaml -f compose.prod.yaml run --rm web python manage.py seed_content --locale en`. Gegenprobe: `docker compose -f compose.yaml -f compose.prod.yaml exec web python manage.py shell -c "from apps.colors.models import ColorCombination; print(ColorCombination.objects.filter(name='').count())"` — `0` heißt durchgängig befüllt, jede andere Zahl zeigt fehlenden Content.

**`docker compose down` bricht mit "Resource is still in use" ab:** Betrifft praktisch immer ein Netzwerk (seltener ein Volume), an dem noch ein Container hängt — auch einer außerhalb dieses Compose-Projekts.

```bash
docker network ls                          # das verdächtige Netzwerk finden
docker network inspect <netzwerk-name>      # Feld "Containers" zeigt, was noch dranhängt
docker network disconnect <netzwerk-name> <container-name>
docker compose down --remove-orphans        # danach erneut
```

**Caddy bekommt kein Zertifikat:** `docker compose -f compose.yaml -f compose.prod.yaml logs caddy` — meistens entweder DNS zeigt noch nicht auf den Server, oder Port 80/443 ist von außen nicht erreichbar (Firewall, Cloud-Security-Group).

**`web` bleibt dauerhaft "unhealthy":** Vor D-52 tatsächlich passiert — der interne Healthcheck lief ohne `X-Forwarded-Proto` gegen `SECURE_SSL_REDIRECT=True` und scheiterte an einem SSL-Handshake auf einem reinen HTTP-Socket. Mit `SECURE_REDIRECT_EXEMPT` behoben; falls es doch wieder auftaucht, `docker compose -f compose.yaml -f compose.prod.yaml logs web` prüfen.
