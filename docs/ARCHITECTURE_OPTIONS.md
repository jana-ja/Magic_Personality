# Architektur-Optionen — Magic Personality

**Status:** Entscheidungsvorlage · **Datum:** 2026-09-05 · Grundlage: `docs/PRD.md`

---

## 1. Was die Architektur eigentlich lösen muss

Aus dem PRD ergeben sich fünf Punkte, an denen sich die Varianten wirklich unterscheiden:

| # | Treiber | Konsequenz |
|---|---|---|
| **T1** | Das Fünfeck (FR-C1 bis FR-C8) ist eine zustandsbehaftete, interaktive SVG-Komponente mit URL-Bindung und Tastaturbedienung. | Das ist die anspruchsvollste UI-Aufgabe des Projekts. Ein serverseitig gerendertes Formular-Paradigma passt hier schlecht. |
| **T2** | Content liegt in der DB und soll später von Nutzenden bearbeitet werden (§8.2, v1.1 Kuratoren). Schon in v0.1 müssen 31 Kombinationen, Eigenschaften und Perspektiven **erfasst** werden. | Eine Pflegeoberfläche wird gebraucht — geschenkt bekommen oder selbst bauen ist ein echter Aufwandsunterschied. |
| **T3** | Sessions, Rate Limiting, i18n, Migrations, später ein Rechtekonzept. | Entweder vom Framework mitgeliefert oder handgebaut. |
| **T4** | **Kein SEO** (NFR-7, `noindex`), 3–10 Nutzende, kein Skalierungsdruck. | Server-Side-Rendering hat hier **keinen** Nutzen. Performance-Argumente sind irrelevant. Das entwertet einige sonst starke Argumente. |
| **T5** | DevOps und Deployment sind ausdrückliches Lernziel; Start auf kleinem Server, späterer Cloud-Umzug ohne Lock-in (NFR-10). | Anzahl und Zuschnitt der Deploy-Artefakte sind ein Bewertungskriterium, nicht nur ein Nebeneffekt. |

---

## 2. Option A — Ein Framework, ein Artefakt

**Next.js (App Router) · TypeScript · Prisma · PostgreSQL**

Frontend und Backend im selben Projekt. Datenzugriff über Server Components und Route Handlers, Sessions selbst implementiert (Cookie + Session-Tabelle). Deployment als ein Container plus Postgres.

```
[ Browser ] ──> [ Next.js Container ] ──> [ PostgreSQL ]
```

**Stärken**
- Eine Sprache, ein Repo, ein Deploy — schnellster Weg zu einer laufenden v0.1.
- Typen durchgehend von der Datenbank bis ins UI (Prisma → TypeScript).
- React löst T1 hervorragend.
- Riesiges Ökosystem, sehr viel Material bei Problemen.

**Schwächen**
- Next.js hat ein eigenwilliges mentales Modell (Server Components, Caching-Ebenen). Ein guter Teil der Lernzeit fließt in Framework-Eigenheiten statt in übertragbares Wissen.
- SSR ist der Kern des Frameworks — und laut T4 brauchst du es nicht. Du zahlst Komplexität für einen Vorteil, den das Projekt nicht abruft.
- Selbst-Hosting funktioniert (`output: "standalone"` + Docker), ist aber der weniger begangene Pfad; die Doku zieht Richtung Vercel.
- Pflegeoberfläche für Content (T2): komplett selbst zu bauen.
- DevOps-Lernwert (T5): gering — ein Container ist schnell verstanden.

---

## 3. Option B — Getrennte SPA und API

**React + Vite + TypeScript · FastAPI (Python) · SQLAlchemy + Alembic · PostgreSQL · Docker Compose · Caddy als Reverse Proxy**

Zwei eigenständige Artefakte hinter einem Reverse Proxy, ausgeliefert unter einer Domain — dadurch bleiben Session-Cookies `SameSite=Lax` und CORS entfällt.

```
                 ┌─> [ Static SPA (React) ]
[ Browser ] ─> [ Caddy ]
                 └─> [ API (FastAPI) ] ──> [ PostgreSQL ]
```

**Stärken**
- Klare Grenze zwischen UI und Domäne. Die spätere Graph-Auswertung (§8.2) und mögliche weitere Clients hängen an einer echten API.
- React ohne Framework-Overhead für T1; Vite ist unkompliziert und schnell.
- FastAPI erzeugt automatisch ein OpenAPI-Schema → daraus generierte TypeScript-Typen halten Frontend und Backend synchron.
- **Höchster DevOps-Lernwert (T5):** mehrere Artefakte, Reverse Proxy, TLS, Compose, Healthchecks, Migrations als eigener Schritt, saubere Trennung von Build und Deploy. Genau die Themen, die beim Cloud-Umzug wieder auftauchen.
- Zwei Sprachen — passt zu „ich bin an verschiedenen Bereichen interessiert".
- Kein Lock-in: läuft auf jedem Server, jedem Cloud-Anbieter, später auch als Container-Service.

**Schwächen**
- Der meiste Boilerplate der drei Optionen: jeder Endpunkt existiert zweimal (Server-Route und Client-Aufruf). Bei ~25 Endpunkten spürbar, aber beherrschbar.
- Auth muss vollständig selbst gebaut werden (Sessions, Rate Limiting, CSRF).
- Pflegeoberfläche für Content (T2): selbst zu bauen — oder anfangs über Seed-Skripte und direkte SQL-Pflege gelöst.
- Zwei Laufzeiten bedeuten zwei Toolchains und zwei Abhängigkeitsbäume.

*Variante:* Statt FastAPI ginge **Go** — ein einzelnes Binary, sehr angenehm in Containern und näher an Infrastruktur-Themen. Preis: deutlich mehr Handarbeit bei CRUD und Migrations. Empfehlung: nur wählen, wenn Go selbst das Lernziel ist.

---

## 4. Option C — Batteries-included-Monolith

**Django (Python) · Django Templates + HTMX · React-Insel für das Fünfeck · PostgreSQL**

Ein Server-Monolith. Auth, Sessions, Migrations, i18n, Rechte und ein vollwertiges Admin-Interface kommen mit dem Framework. Das Fünfeck wird als eingebettete JavaScript-Komponente auf einer sonst servergerenderten Seite umgesetzt.

```
[ Browser ] ──> [ Django Container ] ──> [ PostgreSQL ]
                     └─ /admin (geschenkt)
```

**Stärken**
- **Löst T2 und T3 fast vollständig, ohne Code.** Django Admin ist genau die Pflegeoberfläche, die du zum Erfassen von 31 Kombinationen, Eigenschaften und Perspektiven brauchst — und gleichzeitig die Vorstufe des Kuratoren-Rechtekonzepts aus v1.1.
- Sessions, Passwort-Hashing, CSRF, Rate Limiting, i18n mit Locale-Handling: alles eingebaut und erprobt. Die gesamten FR-U-Anforderungen sind weitgehend Konfiguration statt Implementierung.
- Geringster Gesamtaufwand für alles außer dem Fünfeck.
- Ein Artefakt, sehr einfacher Betrieb.

**Schwächen**
- **Bruch genau beim Kernfeature (T1).** Das Fünfeck braucht Client-State; entweder du baust eine JS-Insel in eine Template-Welt (zwei Paradigmen im selben Projekt) oder du quälst es durch HTMX.
- Moderne Frontend-Praxis lernst du damit kaum.
- DevOps-Lernwert (T5): gering, wie bei Option A.
- Django Admin ist eine interne Oberfläche — für das spätere *nutzerseitige* Bearbeiten von Content (§8.2) trägt sie nicht, dort brauchst du ohnehin eigene Views.

---

## 5. Vergleich

| Kriterium | **A — Next.js** | **B — SPA + API** | **C — Django** |
|---|---|---|---|
| Komplexität | mittel (Framework-Eigenheiten) | mittel-hoch (zwei Systeme) | niedrig |
| Wartbarkeit | mittel (Framework-Churn) | hoch (klare Grenzen) | hoch (sehr stabiles Ökosystem) |
| Skalierbarkeit | ausreichend | am besten — aber **irrelevant** (T4) | ausreichend |
| Entwicklungsaufwand v0.1 | **niedrig** | hoch | niedrig |
| Entwicklungsaufwand v0.2 (Auth) | hoch | hoch | **sehr niedrig** |
| Content-Pflege (T2) | selbst bauen | selbst bauen | **geschenkt** |
| Eignung für das Fünfeck (T1) | **sehr gut** | **sehr gut** | mäßig |
| DevOps-Lernwert (T5) | gering | **hoch** | gering |
| Lernbreite | Frontend-lastig | **Frontend + Backend + Ops** | Backend-lastig |
| Lock-in-Risiko | mittel (Vercel-Sog) | **keins** | keins |

---

## 6. Empfehlung

**Option B**, mit einer Anleihe bei C.

Begründung entlang deiner eigenen Prioritäten:

1. **DevOps ist dein erklärtes Lernziel** (NFR-10). Nur Option B erzeugt die Situationen, in denen DevOps überhaupt stattfindet: mehrere Artefakte, ein Reverse Proxy mit TLS, Migrations als eigener Deploy-Schritt, ein sauberer Schnitt für den Cloud-Umzug. A und C sind „ein Container" — daran lernt man das nicht.
2. **Das Fünfeck ist das Herz von v0.1.** Es sollte in der Technologie gebaut werden, die dafür am besten geeignet ist, nicht in der, die für den Rest am bequemsten ist. Das schließt C für den Kern aus.
3. **T4 entwertet Option A's Hauptargument.** Ohne SEO-Bedarf zahlst du bei Next.js Komplexität für SSR, das du nicht brauchst.
4. **Zwei Sprachen passen zu deinem Interesse an verschiedenen Bereichen** — und Python plus TypeScript ist die Kombination mit dem breitesten Anschluss.

**Die Anleihe bei C:** Du brauchst früh eine Pflegeoberfläche für Content (T2). Baue sie **nicht** in v0.1. Erfasse die Daten stattdessen über versionierte Seed-Dateien im Repo, die per Migrations-Skript eingespielt werden. Das ist reproduzierbar, reviewbar, passt zur DevOps-Linie — und die nutzerseitige Bearbeitung kommt später ohnehin als eigenes Feature, nicht als Admin-Tool.

**Wenn du gegen die Empfehlung entscheidest:** Willst du v0.1 möglichst schnell sehen und ist DevOps zweitrangig, nimm **A**. Willst du v0.2 und v1.0 mit minimalem Aufwand durchziehen und nimmst ein umständliches Fünfeck in Kauf, nimm **C**.

---

## 7. Entscheidungen, die unabhängig von der Wahl gelten

- **PostgreSQL** als Datenbank. JSON-Spalten für `scores`, Array- oder Join-Tabelle für Farbmengen, brauchbare Mengenoperationen für die Teilmengen-Suche aus FR-S3.
- **Sessions in einer Datenbanktabelle**, kein Redis. Bei 3–10 Nutzenden ist ein zusätzlicher Dienst reine Betriebslast.
- **Docker plus Compose** von Anfang an, auch lokal. Das ist die Brücke zum späteren Cloud-Umzug.
- **Caddy als Reverse Proxy** — automatisches TLS via Let's Encrypt, minimale Konfiguration.
- **Migrations als Code**, immer. Kein manuelles Schema-Ändern, auch nicht lokal.
- **Konfiguration ausschließlich über Umgebungsvariablen**, keine Secrets im Repo.
- **CI (GitHub Actions):** Lint, Typecheck, Tests, Container-Build. Deployment zunächst manuell angestoßen.
- **Backups der Datenbank** ab dem Moment, in dem echte Nutzerdaten entstehen (v0.2).
