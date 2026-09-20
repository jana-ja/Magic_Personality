# Deployment

Task 1.12 (`docs/ROADMAP.md`), ARCHITECTURE.md §11. Bringt v0.1 auf den kleinen eigenen Server (NFR-10). Ziel dieser Datei: einmal von Grund auf durchgespielt, nicht nur am Schreibtisch entworfen — der genaue Wortlaut der Befehle ist mit `docker compose -f compose.yaml -f compose.prod.yaml` lokal geprüft (D-50/D-52 in `docs/DECISIONS.md`), das echte Zusammenspiel mit DNS, Firewall und Let's-Encrypt-ACME lässt sich nur auf dem echten Server verifizieren.

## Voraussetzungen

- Docker und Docker Compose v2 (`docker compose version`, nicht das alte `docker-compose`) auf dem Server.
- Eine Domain, deren A/AAAA-Eintrag auf die IP des Servers zeigt — Caddy braucht das für die automatische TLS-Ausstellung (Let's Encrypt HTTP-01-Challenge über Port 80).
- Port 80 und 443 (TCP **und** UDP für HTTP/3) extern erreichbar — sonst schlägt die Zertifikatsausstellung fehl bzw. bricht die Verbindung ab.
- Das GHCR-Image `ghcr.io/jana-ja/magic_personality` ist aktuell **privat** (per `docker pull` ohne Login geprüft: `unauthorized`) — auf dem Server vor dem ersten `pull` einmalig `docker login ghcr.io` mit einem Personal Access Token (Scope `read:packages`) ausführen. Wer stattdessen lieber ohne Token auskommen möchte, kann das Package auf GitHub unter Package-Einstellungen auf öffentlich stellen (unproblematisch, solange kein Quellcode oder Secret im Image landet — beides ist hier nicht der Fall, `.env` wird zur Laufzeit gemountet, nicht eingebacken).

## Einmalige Einrichtung

1. Verzeichnis auf dem Server anlegen, z. B. `/opt/magic_personality`.
2. Genau sechs Dateien aus dem Repository dorthin bringen — kein vollständiger Checkout nötig, das *Image* kommt fertig gebaut aus der Registry, ein `Dockerfile` oder Quellcode braucht der Server nie:
   - `compose.yaml`
   - `compose.prod.yaml`
   - `Caddyfile`
   - `scripts/backup.sh` (Task 2.14, siehe "Backups" unten)
   - `scripts/deploy.sh` und `scripts/deploy_full.sh` (siehe "Deploy-Skripte" unten)

   **Nicht** `compose.override.yaml` — die ist nur für lokale Entwicklung gedacht (D-50) und würde Host-Ports öffnen, die in Produktion bewusst geschlossen bleiben.

   Empfohlener Weg, weil diese Dateien sich künftig auch mal ändern (neuer Healthcheck, andere Caddy-Direktive, …) und dann erneut auf den Server müssen: ein **Sparse Checkout** statt Einzeldateien per Hand zu kopieren — danach reicht `git pull`, um sie zu aktualisieren, ohne den Rest des Repos (App-Code, Tests, `docs/`) mitzuschleppen. `git sparse-checkout set` erwartet im Standard-Modus ("Cone Mode") **Verzeichnisse**, keine einzelnen Dateien — die drei Root-Dateien liegen aber im Repository-Wurzelverzeichnis. `--no-cone` schaltet auf den älteren, musterbasierten Modus um, der einzelne Pfade akzeptiert (führendes `/` verankert den Pfad an der Repo-Wurzel, sonst würde z. B. `Caddyfile` auch gleichnamige Dateien in Unterordnern mitnehmen):

   ```bash
   git clone --filter=blob:none --sparse https://github.com/jana-ja/Magic_Personality.git .
   git sparse-checkout set --no-cone /compose.yaml /compose.prod.yaml /Caddyfile /scripts/backup.sh /scripts/deploy.sh /scripts/deploy_full.sh
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
docker compose -f compose.yaml -f compose.prod.yaml run --rm web python manage.py seed_questionnaire --questionnaire-version 1 --locale en
docker compose -f compose.yaml -f compose.prod.yaml run --rm web python manage.py seed_questionnaire --questionnaire-version 2 --locale en
docker compose -f compose.yaml -f compose.prod.yaml up -d
```

Migrations laufen bewusst als **eigener** Schritt vor `up -d`, nicht beim Containerstart (D-29) — sonst migrieren mehrere Worker gleichzeitig, und ein Fehlschlag zeigt sich erst im Log statt im Deployment selbst.

`seed_content` ist ein **eigener** Schritt, keine Migration (ARCHITECTURE.md §9/§1.1): Die Migrationen legen nur die leeren Strukturzeilen an (fünf Farben, 31 Kombinationen — "bewusst noch ohne Inhalt", `apps/colors/migrations/0002_seed_colors_and_combinations.py`), Namen, Ziel/Mittel, Eigenschaften, Perspektiven und Themes kommen erst mit diesem Befehl aus `seeds/colors_en.json`. Ohne ihn läuft die Seite scheinbar normal (Fünfeck mit den fünf Farbnamen, Struktur, Navigation — die kommen aus den Migrationen), zeigt aber zu jeder Auswahl nur leere Inhalte. Idempotent (D-Entscheidung, ARCHITECTURE.md §9), also gefahrlos bei jedem Deployment erneut ausführbar.

`seed_questionnaire` ist aus demselben Grund ein eigener Schritt (ARCHITECTURE.md §9): Die Fragen kommen ausschließlich aus `seeds/questionnaire_v<version>.json`. Ohne ihn liefert `/quiz/` 404 ("No published questionnaire available yet."), weil der Test nur veröffentlichte Versionen anbietet. Für eine veröffentlichte, unveränderte Version ändert ein erneuter Lauf nichts (FR-T6, `seeds/questionnaire_README.md`). Jede Version hat eine eigene Zeile; alte Versionen bleiben stehen, damit ihre Ergebnisse auswertbar bleiben. `/quiz/` zeigt immer die neueste veröffentlichte Version — eine unveröffentlichte v2 wird eingespielt, aber noch nicht angeboten.

Danach prüfen:

```bash
docker compose -f compose.yaml -f compose.prod.yaml ps          # alle drei "healthy"/"running"
docker compose -f compose.yaml -f compose.prod.yaml logs caddy  # Zertifikat ausgestellt? Fehler beim ACME-Challenge?
curl -I https://<domain>/healthz                                 # 200, ohne Zugangssperre erreichbar
curl -I https://<domain>/                                        # 302 auf /gate/ — alles andere ist gesperrt
```

`web` und `db` veröffentlichen in Produktion bewusst keinen Host-Port (D-50) — sie sind ausschließlich über Caddy erreichbar, nicht direkt per `<server-ip>:8000` oder `:5432`.

## Folge-Deployments

Bei jedem neuen Stand auf `main` (CI baut und veröffentlicht automatisch, D-31/D-76) — als Einzelbefehle hier, gebündelt als `scripts/deploy_full.sh` bzw. `scripts/deploy.sh` (siehe „Deploy-Skripte"):

```bash
docker compose -f compose.yaml -f compose.prod.yaml pull
docker compose -f compose.yaml -f compose.prod.yaml run --rm web python manage.py migrate
docker compose -f compose.yaml -f compose.prod.yaml run --rm web python manage.py seed_content --locale en
docker compose -f compose.yaml -f compose.prod.yaml run --rm web python manage.py seed_questionnaire --questionnaire-version 1 --locale en
docker compose -f compose.yaml -f compose.prod.yaml run --rm web python manage.py seed_questionnaire --questionnaire-version 2 --locale en
docker compose -f compose.yaml -f compose.prod.yaml up -d
```

Dieselben Zeilen wie beim ersten Deployment — `up -d` erneuert nur Container, deren Image sich geändert hat, `db` bleibt unangetastet.

**Ändert sich `compose.yaml`, `compose.prod.yaml` oder `Caddyfile` selbst** (nicht nur der Anwendungscode): Diese drei Dateien liegen nicht im Image, sondern direkt auf dem Server (siehe "Einmalige Einrichtung") — ein `git pull` (bei Sparse Checkout) bzw. erneutes Herunterladen der geänderten Datei *vor* den Befehlen oben bringt sie auf den aktuellen Stand. `docker compose ... pull` holt ausschließlich das Anwendungs-Image, nie diese Konfigurationsdateien.

**Rollback auf einen älteren Stand:** `IMAGE_TAG=<sha-tag>` in der Server-`.env` setzen (die von CI veröffentlichten Tags stehen im Build-Job in GitHub Actions bzw. unter den Package-Versionen auf GitHub), dann dieselben Schritte — `compose.prod.yaml` liest `IMAGE_TAG` selbst, keine Datei muss dafür bearbeitet werden. Zurück auf den neuesten Stand: `IMAGE_TAG` wieder aus der `.env` entfernen (Default ist `latest`).

## Deploy-Skripte

Die Befehle aus „Folge-Deployments" gibt es als zwei Skripte (D-77), damit ein Deployment ein einzelner Aufruf ist:

| Skript | Schritte | Wann |
|---|---|---|
| `scripts/deploy.sh` | `pull`, `up -d`, `ps` | Stand ohne Migration und ohne neue Seed-Dateien (reine Code-, Template- oder CSS-Änderung) |
| `scripts/deploy_full.sh` | `pull`, `migrate`, `seed_content`, `seed_questionnaire` (v1, v2), `up -d`, `ps` | Stand mit neuer Migration oder geänderten Seeds — im Zweifel dieses |

Beide brechen beim ersten Fehler ab (`set -e`): Schlägt `migrate` fehl, läuft der alte Stand unverändert weiter. Sie finden das Compose-Verzeichnis selbst und lassen sich von überall aufrufen; `ps` am Ende zeigt, ob alles `healthy` ist. Kommt eine neue Fragebogen-Version dazu, in `deploy_full.sh` eine `seed_questionnaire`-Zeile ergänzen.

Aufruf im Verzeichnis auf dem Server:

```bash
./scripts/deploy.sh
./scripts/deploy_full.sh
```

**Die Skripte liegen im Repository und werden nicht von Git ignoriert.** Sie enthalten keine Geheimnisse, nur Befehle; Passwörter und Schlüssel stehen in der `.env`, und die bleibt ignoriert. Auf den Server kommen sie wie `backup.sh` über den Sparse Checkout; bei einem bestehenden Checkout einmalig:

```bash
git sparse-checkout add /scripts/deploy.sh /scripts/deploy_full.sh
git pull
```

Ausführbar sind sie, weil Git das Ausführungsrecht mitspeichert; fehlt es nach dem Checkout, hilft `chmod +x scripts/*.sh`.

**Ändern sich `compose*.yaml`, `Caddyfile` oder die Skripte selbst,** zuerst `git pull`, dann das Skript. Das Skript zieht bewusst nicht selbst per Git: Bash liest ein laufendes Skript zeilenweise nach, ein Austausch der Datei mitten im Lauf kann dazu führen, dass das Skript mit einem gemischten Stand weiterläuft.

## CI/CD — warum kein automatischer Deploy

`.github/workflows/ci.yml` baut und veröffentlicht bei jedem Push auf `main` automatisch ein neues Image (D-31) — das ist **Continuous Delivery**: ein deploybares Artefakt entsteht ohne Zutun. Der letzte Schritt, dieses Artefakt tatsächlich auf dem Server laufen zu lassen (**Continuous Deployment**), bleibt hier bewusst ein manueller Aufruf der Befehle oben, kein Auto-Trigger.

Der Grund ist nicht Bequemlichkeit, sondern D-29: Migrations müssen *vor* dem Neustart von `web` laufen, als eigener, beobachtbarer Schritt. Ein rein image-beobachtender Auto-Updater (das verbreitetste Muster dafür heißt "Watchtower" — ein Container, der neue Digests erkennt und automatisch neu startet) kennt diesen Zwischenschritt nicht: Er würde `web` einfach mit dem neuen Image neu starten, sobald es in der Registry auftaucht — bei einer Migration, die neue Spalten oder Tabellen braucht, liefe die neue Codeversion dann gegen ein noch altes Schema. Für 3–10 Nutzende ist der manuelle Trigger (oder — wie jetzt — ein kleines Deploy-Skript, das die Zeilen einfach nacheinander ausführt, siehe „Deploy-Skripte") kein nennenswerter Mehraufwand — ein "richtiges" CD mit automatischem Trigger würde stattdessen entweder den Migrationsschritt mit eingebaut bekommen (ein Skript, das CI selbst per SSH auf dem Server ausführt) oder bräuchte eine Möglichkeit, "Image da, aber noch nicht anwenden" von "jetzt anwenden" zu trennen — beides zusätzliche Komplexität, die diese Größenordnung (noch) nicht rechtfertigt.

## Nach den ersten Tagen: HSTS anheben

`SECURE_HSTS_SECONDS` steht bewusst konservativ auf einer Stunde (D-52) — ein Fehler im frischen TLS-Aufbau soll sich nicht für ein ganzes Jahr im Browser-Cache festsetzen. Sobald HTTPS ein paar Tage zuverlässig lief:

```env
SECURE_HSTS_SECONDS=31536000
```

in der Server-`.env`, dann `docker compose -f compose.yaml -f compose.prod.yaml up -d web` (nur `web` neu starten, `db`/`caddy` bleiben unberührt).

## Backups (Task 2.14, ARCHITECTURE.md §11.4)

Nächtlicher `pg_dump`, gepackt (`gzip`) und geschrieben in ein eigenes Docker-Volume (`postgres_backups`, `compose.prod.yaml`) — kein eigener vierter Container, `scripts/backup.sh` läuft über den bereits laufenden `db`-Dienst. Aufbewahrung 14 Tage; ältere Dumps entfernt das Skript bei jedem Lauf selbst.

### Einrichten (einmalig)

Cron-Eintrag auf dem Server, z. B. mit `crontab -e`:

```cron
0 3 * * * cd /opt/magic_personality && ./scripts/backup.sh >> backup.log 2>&1
```

Läuft dann jede Nacht um 03:00 Uhr Serverzeit. `backup.log` im selben Verzeichnis hält die Ausgabe fest — bei einem stillen Fehlschlag (Container down, Festplatte voll) ist das die erste Anlaufstelle.

### Wiederherstellung

Bewusst **kein** Skript dafür — eine Wiederherstellung ist ein seltener, folgenreicher Eingriff, der jedes Mal eine bewusste Entscheidung braucht (welches Backup, welche Zieldatenbank), keine automatisierte Routine wie das Backup selbst.

1. Verfügbare Dumps auflisten:
   ```bash
   docker compose -f compose.yaml -f compose.prod.yaml exec db ls -la /backups
   ```
2. **Erst gegen eine Wegwerf-Datenbank prüfen**, nie direkt in die echte einspielen:
   ```bash
   docker compose -f compose.yaml -f compose.prod.yaml exec -T db sh -c \
     'PGPASSWORD="$POSTGRES_PASSWORD" psql -U "$POSTGRES_USER" -d postgres -c "CREATE DATABASE restore_check OWNER \"$POSTGRES_USER\";"'
   docker compose -f compose.yaml -f compose.prod.yaml exec -T db sh -c \
     'gunzip -c /backups/<datei>.sql.gz | PGPASSWORD="$POSTGRES_PASSWORD" psql -U "$POSTGRES_USER" -d restore_check -v ON_ERROR_STOP=1'
   ```
   Stichprobe gegen die Wegwerf-Datenbank (Zeilenzahlen, ob sie plausibel zum erwarteten Zeitpunkt des Dumps passen):
   ```bash
   docker compose -f compose.yaml -f compose.prod.yaml exec -T db sh -c \
     'PGPASSWORD="$POSTGRES_PASSWORD" psql -U "$POSTGRES_USER" -d restore_check -c "select count(*) from accounts_profile;"'
   ```
   Danach aufräumen: `DROP DATABASE restore_check;` (gleicher Verbindungsaufbau wie beim Anlegen, `-d postgres`).
3. **Erst wenn Schritt 2 überzeugt**, die echte Datenbank ersetzen — das braucht `web` gestoppt (offene Verbindungen verhindern sonst `DROP DATABASE`) und ist der eigentliche Ernstfall:
   ```bash
   docker compose -f compose.yaml -f compose.prod.yaml stop web
   docker compose -f compose.yaml -f compose.prod.yaml exec -T db sh -c \
     'PGPASSWORD="$POSTGRES_PASSWORD" psql -U "$POSTGRES_USER" -d postgres -c "DROP DATABASE \"$POSTGRES_DB\";" -c "CREATE DATABASE \"$POSTGRES_DB\" OWNER \"$POSTGRES_USER\";"'
   docker compose -f compose.yaml -f compose.prod.yaml exec -T db sh -c \
     'gunzip -c /backups/<datei>.sql.gz | PGPASSWORD="$POSTGRES_PASSWORD" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1'
   docker compose -f compose.yaml -f compose.prod.yaml start web
   ```

**Einmal geprobt** (2026-09-17, lokal gegen `compose.yaml`/`compose.prod.yaml` — derselbe Mechanismus, den auch der Server verwendet, nur ohne Caddy/TLS davor): `scripts/backup.sh` gegen die lokale Entwicklungsdatenbank laufen lassen, den entstandenen Dump in eine frisch angelegte `restore_rehearsal`-Datenbank eingespielt (Schritt 2 oben) und die Zeilenzahlen dreier Tabellen (`accounts_profile`, `quiz_testresult`, `colors_colorcombination`) sowie die tatsächlichen Nickname-Werte gegen die Ursprungsdatenbank verglichen — identisch. Die Wegwerf-Datenbank danach gelöscht. Schritt 3 (Ersetzen der echten Datenbank) wurde bewusst **nicht** an einer Datenbank mit echten Nutzerdaten geprobt; der SQL-Inhalt ist zwischen Schritt 2 und 3 identisch, nur das Ziel unterscheidet sich.

**Erneut geprobt** (2026-09-17, Task 3.6/Release-Durchsicht v1.0, derselbe Ablauf, diesmal ausdrücklich gegen den seit M3 gewachsenen Schema-Stand): `db` einmal mit allen drei Compose-Dateien zusammen hochgefahren (`-f compose.yaml -f compose.override.yaml -f compose.prod.yaml up -d db`, damit sowohl der Host-Port aus `compose.override.yaml` als auch das `postgres_backups`-Volume aus `compose.prod.yaml` gleichzeitig da sind — mit nur `-f compose.yaml -f compose.prod.yaml` allein, wie im Server-Befehl oben, verschwindet lokal der Host-Port, weil `compose.override.yaml` dann nicht mehr automatisch eingelesen wird). `scripts/backup.sh` gelaufen, in eine frische `restore_check`-Datenbank eingespielt (Schritt 2), Zeilenzahlen von `accounts_profile`/`quiz_testresult`/`colors_colorcombination` sowie zusätzlich `social_friendship` (Task 3.4, seit dem letzten Probelauf neu) gegen die Ursprungsdatenbank verglichen — identisch, `\d social_friendship` zeigte alle drei Constraints aus `apps.social.models.Friendship.Meta` (D-67) korrekt wiederhergestellt. Wegwerf-Datenbank danach gelöscht.

## Admin-Zugang (D-71)

Das Django-Admin liegt unter `/admin/` (hinter der Zugangssperre, also erst den Invite-Code eingeben). Hinein kommt nur ein Account mit `is_staff`. Einen vorhandenen Account zum Superuser machen — bevorzugt statt `createsuperuser`, weil das einen Account **ohne Profil** anlegt (der Nickname im Kopfbereich bliebe leer, `/accounts/profile/` gäbe 404):

```bash
docker compose -f compose.yaml -f compose.prod.yaml exec web python manage.py shell -c \
  "from apps.accounts.models import User; User.objects.filter(email='deine@mail.example').update(is_staff=True, is_superuser=True)"
```

Danach in `/admin/` mit den normalen Zugangsdaten anmelden. Weitere Admins lassen sich dort selbst über „Users" ernennen.

**Ein drittes Mal geprobt** (2026-09-19, Task 4.10/Release-Durchsicht v1.2, gleicher Ablauf wie zuvor mit allen drei Compose-Dateien): Dump mit `scripts/backup.sh`, Einspielen in eine Wegwerf-Datenbank (Schritt 2), Zeilenzahlen von `accounts_profile`, `accounts_colorassignment`, `quiz_testresult`, `social_friendship` und `colors_colorcombination` gegen die Ursprungsdatenbank verglichen — identisch —, die drei Constraints von `social_friendship` vorhanden und ein Prüfsummen-Vergleich über Nickname und Bio aller Profile identisch. Wegwerf-Datenbank danach gelöscht.

## Release-Hinweise v1.2 (Profil-Überarbeitung)

Für das Deployment von v1.2 ist nichts Besonderes zu tun: **keine Migrationen** (`makemigrations --check` meldet nichts, der Schema-Stand ist der von v1.1), keine neuen Abhängigkeiten, `compose*.yaml`, `Dockerfile` und `Caddyfile` unverändert — der übliche Ablauf aus „Folge-Deployments" genügt. Zwei Dinge, die auffallen können:

- **Adressen:** Die Profilseite ist jetzt `/u/<nickname>/` für die eigene Person wie für alle anderen. `/accounts/profile/` bleibt als Weiterleitung auf das eigene Profil erhalten (alte Lesezeichen funktionieren), speichert aber nichts mehr. Ändert jemand den Nickname, ändert sich die Adresse des Profils; alte Adressen führen dann zu 404.
- **Statische Dateien:** In Produktion liefert WhiteNoise sie mit Inhalts-Hash im Namen aus (`CompressedManifestStaticFilesStorage`), zwischengespeicherte Browser-Kopien der alten Stylesheets und Skripte werden also nicht weiterverwendet.

Vor dem Deployment lässt sich mit dem Backup-Ablauf oben ein Dump ziehen; nach dem Deployment reicht ein Blick auf `/healthz` und ein eigenes Profil. Die Bestandsdaten (Zuordnungen, Testverknüpfungen, Freundschaften) bleiben unangetastet — für v1.2 lokal nachgewiesen (Vorher-nachher-Vergleich, siehe `docs/ROADMAP.md`, Task 4.10).

## Fehlerbehebung

**Seite lädt, Fünfeck und Navigation sind da, aber jede Auswahl zeigt leere Inhalte:** `seed_content` wurde vergessen (siehe "Erstes Deployment" oben) — die Migrationen legen nur leere Zeilen an, den eigentlichen Content bringt erst `docker compose -f compose.yaml -f compose.prod.yaml run --rm web python manage.py seed_content --locale en`. Gegenprobe: `docker compose -f compose.yaml -f compose.prod.yaml exec web python manage.py shell -c "from apps.colors.models import ColorCombination; print(ColorCombination.objects.filter(name='').count())"` — `0` heißt durchgängig befüllt, jede andere Zahl zeigt fehlenden Content.

**`/quiz/` liefert 404:** Der Test bietet nur veröffentlichte Fragebogen-Versionen an. Gegenprobe: `docker compose -f compose.yaml -f compose.prod.yaml exec web python manage.py shell -c "from apps.quiz.models import Questionnaire; print(list(Questionnaire.objects.values_list('version', 'question_count', 'published_at')))"`
- Leere Liste: `seed_questionnaire` wurde nicht ausgeführt (siehe "Erstes Deployment").
- `published_at` ist `None`: Das eingespielte Image enthielt noch eine unveröffentlichte Seed-Datei (`"published": false`). Mit dem aktuellen Image erneut `seed_questionnaire` ausführen; die Ausgabe endet dann mit "Soeben veröffentlicht."
- Version mit `published_at` vorhanden, trotzdem 404: Der laufende `web`-Container ist älter als das Image, mit dem geseedet wurde. `docker compose -f compose.yaml -f compose.prod.yaml up -d` erneuert ihn.

**`docker compose down` bricht mit "Resource is still in use" ab:** Betrifft praktisch immer ein Netzwerk (seltener ein Volume), an dem noch ein Container hängt — auch einer außerhalb dieses Compose-Projekts.

```bash
docker network ls                          # das verdächtige Netzwerk finden
docker network inspect <netzwerk-name>      # Feld "Containers" zeigt, was noch dranhängt
docker network disconnect <netzwerk-name> <container-name>
docker compose down --remove-orphans        # danach erneut
```

**Caddy bekommt kein Zertifikat:** `docker compose -f compose.yaml -f compose.prod.yaml logs caddy` — meistens entweder DNS zeigt noch nicht auf den Server, oder Port 80/443 ist von außen nicht erreichbar (Firewall, Cloud-Security-Group).

**`web` bleibt dauerhaft "unhealthy":** Vor D-52 tatsächlich passiert — der interne Healthcheck lief ohne `X-Forwarded-Proto` gegen `SECURE_SSL_REDIRECT=True` und scheiterte an einem SSL-Handshake auf einem reinen HTTP-Socket. Mit `SECURE_REDIRECT_EXEMPT` behoben; falls es doch wieder auftaucht, `docker compose -f compose.yaml -f compose.prod.yaml logs web` prüfen.
