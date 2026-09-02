# 🥗 Kantinen-Wochenplan

Holt jeden Sonntag ab 17:35 Uhr automatisch den Speiseplan einer Kantinen-Web-App
(für die kommende Woche), berechnet Nährwerte **pro Portion**, wählt pro Tag
Empfehlungen (**ausgewogen / proteinreich / vegetarisch**) und baut Mahlzeit-Kombis
mit **~600 kcal** und **~1000 kcal** — inkl. **Extern-Preisen** (Faktor 1,5,
wo die App keinen Extern-Preis ausweist).

**Ausgaben:** HTML-Seite (`docs/index.html`, optional via GitHub Pages) und
`docs/plan.json`. Ein E-Mail-Versand findet nicht statt.

Die konkrete Kantine wird **nicht im Repo** genannt — die Quell-URL kommt aus
dem Secret `EUREST_BASE`.

## Einrichtung (einmalig, ~10 Minuten)

### 1. Secrets hinterlegen
Repo → **Settings → Secrets and variables → Actions → New repository secret**:

| Secret        | Bedeutung                                                    |
|---------------|--------------------------------------------------------------|
| `EUREST_BASE` | **Erforderlich.** Basis-URL der Kantinen-Web-App (z. B. `https://<standort>.<anbieter>.de/<restaurant>/web-app-2`) |
| `PLAN_TITLE`  | optional. Bezeichnung in der Kopfzeile (z. B. `Betriebsrestaurant · Standort X`). Ohne Angabe: neutral „Kantinen-Wochenplan". |
| `SOURCE_URL`  | optional. Link in der Fußzeile („Quelle"), meist identisch mit `EUREST_BASE`. |

⚠️ **Bei öffentlichem Repo:** `PLAN_TITLE` und `SOURCE_URL` erscheinen in den
committeten Dateien (`docs/index.html`, `docs/plan.json`) und sind damit
öffentlich sichtbar. Wer die Seite neutral halten will, setzt zusätzlich die
Variable `PAGE_SHOW_DETAILS` auf `0`.

### 2. Erster Testlauf
Repo → **Actions → Kantinen-Wochenplan → Run workflow**
(Häkchen bei **Debug** für einen ausführlichen Lauf mit Artefakt `debug-html`).
Danach im Log prüfen, wie viele Tage/Gerichte gefunden wurden.

### 3. GitHub Pages (optional)
Repo → **Settings → Pages** → Source: *Deploy from a branch* →
Branch `main`, Ordner `/docs` → Save. Bei privaten Repos erfordert Pages einen
kostenpflichtigen Plan. Ohne Pages lässt sich `docs/index.html` direkt aus dem
Repo herunterladen und im Browser öffnen.

## Konfiguration

In `wochenplan.yml` anpassbar:
- `PRICE_FACTOR` — Extern-Aufschlag (Standard `1.5`)
- `SEED_ID` / `SEED_DATE` — Fallback, falls die Tages-IDs nicht aus dem HTML
  lesbar sind: eine bekannte Tages-ID + zugehöriges Datum (IDs zählen +1/Tag)
- Zeitzone: Variable `PLAN_TZ` (Standard `Europe/Berlin`). Sie bestimmt
  Zeitstempel, Kalenderwoche und Commit-Datum; Sommer-/Winterzeit erkennt die
  Zeitzonendatenbank automatisch.
- Cron-Zeiten: GitHub rechnet ausschließlich in UTC, kennt also keine
  Zeitumstellung. Deshalb gibt es je Slot einen Sommer- und einen
  Winter-Ausdruck, und der erste Job-Schritt lässt nur den passenden durch:

  | Cron (UTC) | gilt bei | Ortszeit | Zweck |
  |---|---|---|---|
  | `35 15 * * 0` | UTC+2 (Sommer) | So 17:35 | Hauptlauf |
  | `35 16 * * 0` | UTC+1 (Winter) | So 17:35 | Hauptlauf |
  | `35 19 * * 0` | UTC+2 (Sommer) | So 21:35 | Sicherheitsnetz |
  | `35 20 * * 0` | UTC+1 (Winter) | So 21:35 | Sicherheitsnetz |

  Die krumme Minute ist Absicht: Slots zur vollen Stunde werden bei GitHub
  regelmäßig 30–60 Minuten verzögert bedient. Das Sicherheitsnetz überspringt
  sich selbst, wenn `docs/plan.json` schon einen Plan vom selben Tag enthält.
- Bei anderer Zeitzone als UTC±1/±2 die Cron-Ausdrücke und die Zuordnung im
  Guard-Schritt entsprechend anpassen.

## Fehlersuche

- **„Keine Tage gefunden"**: Workflow manuell mit gesetztem **Debug**-Häkchen
  starten und das Artefakt `debug-html` (u. a. `debug_main.html`) prüfen —
  ggf. `SEED_ID`/`SEED_DATE` mit einer aktuellen ID aus den Browser-DevTools
  aktualisieren (Netzwerk-Tab → `ajaxpage_dailymenupage/<ID>`).
- **Nährwerte wirken falsch**: Werte mit `*` sind geschätzt, weil die App
  kein oder ein unplausibles Portionsgewicht liefert.
  Schätzgewichte stehen in `WEIGHT_RULES` in `fetch_menu.py`.
- **Zeitplan**: GitHub-Cron kann sich um einige Minuten verspäten — normal.

## Hinweise
- Die Daten sind öffentlich ohne Login abrufbar; das Skript ruft pro Woche
  nur ~6 Seiten ab (schonender als ein Browser-Besuch).
- Alle Angaben ohne Gewähr; vegetarisch/vegan wird über eine Wortheuristik
  bestimmt, solange die Quelle keine maschinenlesbaren Labels liefert.
