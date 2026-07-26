# 🥗 Kantinen-Wochenplan

Holt jeden Sonntag um 18 Uhr automatisch den Speiseplan einer Kantinen-Web-App
(für die kommende Woche), berechnet Nährwerte **pro Portion**, wählt pro Tag
Empfehlungen (**ausgewogen / Protein / vegetarisch**) und baut Mahlzeit-Kombis
mit **~600 kcal** und **~1000 kcal** — inkl. **Extern-Preisen** (Faktor 1,5,
wo die App keinen Extern-Preis ausweist).

**Ausgaben:** HTML-Seite (`docs/index.html`, optional via GitHub Pages),
`docs/plan.json`, vollständige E-Mail mit Anhang.

Die konkrete Kantine wird **nicht im Repo** genannt — die Quell-URL kommt aus
dem Secret `EUREST_BASE`.

## Einrichtung (einmalig, ~10 Minuten)

### 1. Secrets hinterlegen
Repo → **Settings → Secrets and variables → Actions → New repository secret**:

| Secret        | Bedeutung                                                    |
|---------------|--------------------------------------------------------------|
| `EUREST_BASE` | **Erforderlich.** Basis-URL der Kantinen-Web-App (z. B. `https://<standort>.<anbieter>.de/<restaurant>/web-app-2`) |
| `SMTP_HOST`   | z. B. `smtp.gmail.com`                                       |
| `SMTP_PORT`   | optional, Standard `587`                                     |
| `SMTP_USER`   | SMTP-Login                                                   |
| `SMTP_PASS`   | App-Passwort (nicht das normale Login-Passwort!)             |
| `MAIL_FROM`   | optional, Standard = `SMTP_USER`                             |
| `MAIL_TO`     | **Erforderlich für Versand.** Empfänger, kommagetrennt für mehrere (z. B. `a@x.de, b@y.de`). Versand erfolgt per **BCC** – Empfänger sehen einander nicht. |
| `PLAN_TITLE`  | optional. Bezeichnung in der Kopfzeile (z. B. `Betriebsrestaurant · Standort X`). Ohne Angabe: neutral „Kantinen-Wochenplan". |
| `SOURCE_URL`  | optional. Link in der Fußzeile („Quelle"), meist identisch mit `EUREST_BASE`. |

⚠️ **Bei öffentlichem Repo:** `PLAN_TITLE` und `SOURCE_URL` erscheinen in den
committeten Dateien (`docs/index.html`, `docs/plan.json`) und sind damit
öffentlich sichtbar. Wer sie nur in der (privaten) E-Mail haben will, setzt
zusätzlich die Variable `PAGE_SHOW_DETAILS` auf `0` – dann bleiben Seite und
`plan.json` neutral.

Gmail: App-Passwort unter *Google-Konto → Sicherheit → 2FA → App-Passwörter*.
Ohne SMTP-Zugang oder `MAIL_TO` wird der Mailversand einfach übersprungen —
der Plan landet trotzdem in `docs/`.

### 2. Erster Testlauf
Repo → **Actions → Kantinen-Wochenplan → Run workflow**
(Häkchen bei **Debug** für einen ausführlichen Lauf mit Artefakt `debug-html`).
Danach im Log prüfen, wie viele Tage/Gerichte gefunden wurden.

### 3. GitHub Pages (optional)
Repo → **Settings → Pages** → Source: *Deploy from a branch* →
Branch `main`, Ordner `/docs` → Save. Bei privaten Repos erfordert Pages einen
kostenpflichtigen Plan — die E-Mail enthält den vollständigen Plan aber auch
ohne Pages (inkl. HTML-Anhang).

## Konfiguration

In `wochenplan.yml` anpassbar:
- `PRICE_FACTOR` — Extern-Aufschlag (Standard `1.5`)
- `SEED_ID` / `SEED_DATE` — Fallback, falls die Tages-IDs nicht aus dem HTML
  lesbar sind: eine bekannte Tages-ID + zugehöriges Datum (IDs zählen +1/Tag)
- Cron-Zeit: `0 16 * * 0` = Sonntag 18:00 MESZ (GitHub rechnet in UTC)

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
